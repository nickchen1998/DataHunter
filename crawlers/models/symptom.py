from django.db import models
from django.db.models import QuerySet
from pgvector.django import VectorField, HnswIndex
from typing import Optional





class SymptomQuerySet(models.QuerySet):
    """Symptom 查詢集，包含自定義查詢方法"""
    
    def build_queryset(
        self,
        department: Optional[str] = None, 
        gender: Optional[str] = None, 
        question: Optional[str] = None
    ) -> 'SymptomQuerySet':
        """
        構建 Symptom 查詢集
        統一的查詢構建方法，支援多種過濾條件
        """
        from utils.search import hybrid_search_with_rerank
        
        queryset = self
        
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


class SymptomManager(models.Manager):
    """Symptom 管理器"""
    
    def get_queryset(self):
        return SymptomQuerySet(self.model, using=self._db)
    
    def build_queryset(self, **kwargs):
        return self.get_queryset().build_queryset(**kwargs)


class Symptom(models.Model):
    id = models.AutoField(primary_key=True)

    subject_id = models.IntegerField()
    subject = models.CharField(max_length=255)
    department = models.CharField(max_length=255)

    symptom = models.CharField(max_length=255)
    question = models.TextField(db_index=True)
    answer = models.TextField()

    gender = models.CharField(max_length=10)

    question_time = models.DateTimeField(help_text="網站上的患者提問時間。")
    answer_time = models.DateTimeField(help_text="網站上的醫師回答時間。")

    question_embeddings = VectorField(
        dimensions=1536,
        help_text="基於 question 欄位並使用 OpenAI text-embedding-3-small 產生向量。"
    )

    # 使用自定義管理器
    objects = SymptomManager()

    class Meta:
        verbose_name = '衛福部-台灣e院-症狀'
        verbose_name_plural = '衛福部-台灣e院-症狀'
        indexes = [
            HnswIndex(
                name="crawlers_symp_q_emb_hnsw_idx",
                fields=["question_embeddings"],
                m=16,
                ef_construction=64,
                opclasses=["vector_l2_ops"],
            )
        ]

    def __str__(self):
        return str(self.id) 