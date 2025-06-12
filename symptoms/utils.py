from typing import Optional
from django.db.models import QuerySet
from symptoms.models import Symptom
from utils.search import hybrid_search_with_rerank


def build_symptom_queryset(
    department: Optional[str] = None, 
    gender: Optional[str] = None, 
    question: Optional[str] = None
) -> QuerySet[Symptom]:
    queryset = Symptom.objects.all()
    
    if department:
        queryset = queryset.filter(department__icontains=department)
    
    if gender:
        queryset = queryset.filter(gender=gender)
    
    if question:
        queryset = hybrid_search_with_rerank(
            queryset=queryset,
            vector_field_name="question_embeddings",
            text_field_name="question",
            original_question=question,
        )
    else:
        queryset = queryset.order_by("-question_time")
    
    return queryset
