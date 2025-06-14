from django.db.models import Q, Case, When, QuerySet
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_cohere.rerank import CohereRerank
from pgvector.django import CosineDistance


def hybrid_search_with_rerank(
    queryset: QuerySet,
    vector_field_name: str,
    text_field_name: str,
    original_question: str,
    min_score: float = 0.80
) -> QuerySet:
    # 1. Extract keywords with OpenAI
    prompt = ChatPromptTemplate.from_template(
        "Extract relevant keywords from the following user question. "
        "Return them as a comma-separated list. "
        "User Question: {question}"
    )
    model = ChatOpenAI()
    parser = StrOutputParser()
    chain = prompt | model | parser
    keywords_str = chain.invoke({"question": original_question})
    keywords = [keyword.strip() for keyword in keywords_str.split(',') if keyword.strip()]

    # 2. Keyword-based search (Fuzzy search)
    keyword_query = Q()
    if keywords:
        for keyword in keywords:
            keyword_query |= Q(**{f"{text_field_name}__icontains": keyword})
        keyword_results = list(queryset.filter(keyword_query)[:100])
    else:
        keyword_results = []


    # 3. Vector-based search
    question_embeddings = OpenAIEmbeddings(model="text-embedding-3-small").embed_query(original_question)
    vector_results = list(queryset.annotate(
        distance=CosineDistance(vector_field_name, question_embeddings)
    ).order_by("distance")[:100])

    # 4. Combine and deduplicate results
    combined_results = []
    seen_ids = set()

    for result in keyword_results + vector_results:
        if result.id not in seen_ids:
            combined_results.append(result)
            seen_ids.add(result.id)

    # 5. Rerank using Cohere
    reranker = CohereRerank(
        model="rerank-multilingual-v3.0",
        top_n=100
    )

    docs_to_rerank = [
        Document(page_content=getattr(res, text_field_name), metadata={"id": res.id})
        for res in combined_results
    ]

    reranked_docs = reranker.compress_documents(
        documents=docs_to_rerank,
        query=original_question
    )

    # 6. Filter by minimum score and get sorted IDs
    high_score_docs = [doc for doc in reranked_docs]
    
    if not high_score_docs:
        # 如果沒有符合分數條件的結果，回傳空的 QuerySet
        return queryset.model.objects.none()
    
    sorted_ids = [doc.metadata["id"] for doc in high_score_docs]
    preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(sorted_ids)])

    final_queryset = queryset.model.objects.filter(pk__in=sorted_ids).order_by(preserved_order)

    return final_queryset 