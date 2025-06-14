from typing import Optional
from django.db.models import QuerySet
from gov_datas.models import Dataset
from utils.search import hybrid_search_with_rerank


def build_dataset_queryset(
    category: Optional[str] = None,
    description: Optional[str] = None,
    name: Optional[str] = None,
    upload_start: Optional[str] = None,
    upload_end: Optional[str] = None,
    update_start: Optional[str] = None,
    update_end: Optional[str] = None
) -> QuerySet[Dataset]:
    from datetime import datetime
    
    queryset = Dataset.objects.all()
    
    if category:
        queryset = queryset.filter(category=category)
    
    if name:
        queryset = queryset.filter(name__icontains=name)
    
    if description:
        queryset = hybrid_search_with_rerank(
            queryset=queryset,
            vector_field_name="description_embeddings",
            text_field_name="description",
            original_question=description,
        )
    else:
        queryset = queryset.order_by("-dataset_id")
    
    # 上架時間過濾
    if upload_start:
        try:
            start_date = datetime.fromisoformat(upload_start.replace('Z', '+00:00'))
            queryset = queryset.filter(upload_time__date__gte=start_date.date())
        except (ValueError, TypeError):
            pass
    
    if upload_end:
        try:
            end_date = datetime.fromisoformat(upload_end.replace('Z', '+00:00'))
            queryset = queryset.filter(upload_time__date__lte=end_date.date())
        except (ValueError, TypeError):
            pass
    
    # 更新時間過濾
    if update_start:
        try:
            start_date = datetime.fromisoformat(update_start.replace('Z', '+00:00'))
            queryset = queryset.filter(update_time__date__gte=start_date.date())
        except (ValueError, TypeError):
            pass
    
    if update_end:
        try:
            end_date = datetime.fromisoformat(update_end.replace('Z', '+00:00'))
            queryset = queryset.filter(update_time__date__lte=end_date.date())
        except (ValueError, TypeError):
            pass
    
    return queryset 