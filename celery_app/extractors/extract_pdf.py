from RAGPilot.celery import app
from sources.models import SourceFile, SourceFileChunk, ProcessingStatus
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from celery_app.extractors import utils

MAP_PROMPT = PromptTemplate.from_template("""
你是一個專業的文本摘要助手，請將以下內容進行摘要，使用繁體中文，並保持重點清晰。摘要請控制在 200 字以內：

{text}
""")

COMBINE_PROMPT = PromptTemplate.from_template("""
請綜合以下多段摘要，統一成一篇簡潔有重點的繁體中文摘要，總長度限制為 500 字以內：

{text}
""")



@app.task()
def extract_pdf_soruce_file_content(source_file_id: int):
    try:
        source_file = SourceFile.objects.get(id=source_file_id)
        source_file = utils.set_source_file_status(source_file, ProcessingStatus.PROCESSING)
    except Exception as e:
        utils.set_source_file_status(source_file, ProcessingStatus.FAILED, "找不到 SourceFile 物件。")
        return f"找不到 SourceFile 物件: {str(e)}"
    
    try:
        source_file.failed_reason = None
        source_file.save()
        source_file.refresh_from_db()
        
        if source_file.sourcefilechunk_set.count() > 0:
            source_file.sourcefilechunk_set.all().delete()
    except Exception as e:
        utils.set_source_file_status(source_file, ProcessingStatus.FAILED, "刪除 SourceFileChunk 物件失敗。")
        return f"刪除 SourceFileChunk 物件失敗: {str(e)}"

    try:
        # 使用 PyPDFLoader 載入 PDF
        loader = PyPDFLoader(source_file.path)
        documents = loader.load()
    except Exception as e:
        utils.set_source_file_status(source_file, ProcessingStatus.FAILED, "載入 PDF 檔案失敗。")
        return f"載入 PDF 檔案失敗: {str(e)}"
        
    if not documents:
        utils.set_source_file_status(source_file, ProcessingStatus.COMPLETED)

        source_file.summary = f"PDF 檔案 {source_file.filename} 沒有可提取的內容，請使用其他方式提取內容。"
        source_file.save()

        return f"PDF 檔案 {source_file.filename} 沒有可提取的內容，請使用其他方式提取內容。"
            
    parent_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    child_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=20,
        separators=["\n\n", "\n", " ", ""]
    )
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    

    try:
        parent_chunks_docs = parent_text_splitter.split_documents(documents)
        parent_chunks = [doc.page_content for doc in parent_chunks_docs]
        parent_chunk_embeddings = embeddings.embed_documents(parent_chunks)
    except Exception as e:
        utils.set_source_file_status(source_file, ProcessingStatus.FAILED, "分割父段落失敗。")
        return f"分割父段落失敗: {str(e)}"
    
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        chain = load_summarize_chain(
            llm, 
            chain_type="map_reduce", 
            map_prompt=MAP_PROMPT, 
            combine_prompt=COMBINE_PROMPT
        )
        summary = chain.invoke(parent_chunks_docs)
        source_file.summary = summary.get("output_text")
        source_file.save()
        source_file.refresh_from_db()
    except Exception as e:
        utils.set_source_file_status(source_file, ProcessingStatus.FAILED, "生成摘要失敗。")
        return f"生成摘要失敗: {str(e)}"
    
    parent_chunks_created = 0
    child_chunks_created = 0
    for parent_chunk_text, embedding in zip(parent_chunks, parent_chunk_embeddings):
        parent_chunk = SourceFileChunk.objects.create(
            user=source_file.user,
            source_file=source_file,
            content=parent_chunk_text,
            content_embedding=embedding
        )
        parent_chunks_created += 1

        try:
            child_chunks = child_text_splitter.split_text(parent_chunk_text)
            child_chunk_embeddings = embeddings.embed_documents(child_chunks)
        except Exception as e:
            utils.set_source_file_status(source_file, ProcessingStatus.FAILED, "分割子段落失敗。")
            return f"分割子段落失敗: {str(e)}"
        
        
        for child_chunk_text, child_chunk_embedding in zip(child_chunks, child_chunk_embeddings):
            SourceFileChunk.objects.create(
                user=source_file.user,
                source_file=source_file,
                source_file_chunk=parent_chunk,
                content=child_chunk_text,
                content_embedding=child_chunk_embedding
            )
            child_chunks_created += 1

    utils.set_source_file_status(source_file, ProcessingStatus.COMPLETED)
    
    return f"成功提取 PDF 檔案 {source_file.filename} 的內容，創建了 {parent_chunks_created} 個父文字片段和 {child_chunks_created} 個子文字片段。"
