from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField, HnswIndex
import uuid

class SourceFileFormat(models.TextChoices):
    PDF = 'pdf', 'PDF'
    CSV = 'csv', 'CSV'
    JSON = 'json', 'JSON'
    XML = 'xml', 'XML'


class ProcessingStatus(models.TextChoices):
    PENDING = 'pending', '等待處理'
    PROCESSING = 'processing', '處理中'
    COMPLETED = 'completed', '處理完成'
    FAILED = 'failed', '處理失敗'


# Create your models here.
class Source(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    description = models.TextField()

    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '自建資料源'
        verbose_name_plural = '自建資料源'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    @property
    def file_count(self):
        """獲取資料源中的檔案數量"""
        return self.sourcefile_set.count()



    def delete(self, using=None, keep_parents=False):
        """刪除資料源時同時刪除所有相關檔案"""
        # Django 的 CASCADE 會自動刪除相關的 SourceFile
        # 而 SourceFile 的 delete 方法會處理實體檔案的刪除
        super().delete(using=using, keep_parents=keep_parents)


class SourceFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)

    filename = models.CharField(max_length=255)
    size = models.FloatField(help_text="檔案大小，單位為 MB")
    format = models.CharField(max_length=10, choices=SourceFileFormat.choices)
    summary = models.TextField(null=True, blank=True)
    summary_embedding = VectorField(
        dimensions=1536,
        help_text="使用 OpenAI text-embedding-3-small 產生向量。"
    )

    path = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="檔案路徑，用於儲存上傳的檔案，格式為 /<指定目錄>/<a~z>(username 首字小寫)/<username>/<uuid>.<format>"
    )
    uuid = models.UUIDField(default=uuid.uuid4, help_text="檔案唯一 ID")

    status = models.CharField(max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING)
    failed_reason = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '資料源檔案'
        verbose_name_plural = '資料源檔案'
        ordering = ['-created_at']
        indexes = [
            HnswIndex(
                name="file_summary_embedding_hnsw_idx",
                fields=["summary_embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_l2_ops"],
            )
        ]

    def __str__(self):
        return f"{self.filename} ({self.source.name})"



    def delete(self, using=None, keep_parents=False):
        """刪除檔案時同時刪除實體檔案"""
        # 實體檔案的刪除由 pre_delete 信號處理器處理
        # 這確保了無論是直接刪除還是 CASCADE 刪除都會清理實體檔案
        super().delete(using=using, keep_parents=keep_parents)


class SourceFileTable(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source_file = models.ForeignKey(SourceFile, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=255)
    database_name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '資料源檔案表格'
        verbose_name_plural = '資料源檔案表格'

    def __str__(self):
        return f"{self.table_name} ({self.database_name})"


class SourceFileChunk(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source_file = models.ForeignKey(SourceFile, on_delete=models.CASCADE)
    source_file_chunk = models.ForeignKey(
        "self", on_delete=models.CASCADE, 
        null=True, blank=True, related_name="child_source_file_chunks"
    )

    content = models.TextField()
    content_embedding = VectorField(
        dimensions=1536,
        help_text="使用 OpenAI text-embedding-3-small 產生向量。"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '資料源檔案片段'
        verbose_name_plural = '資料源檔案片段'
        indexes = [
            HnswIndex(
                name="file_chunk_embedding_hnsw_idx",
                fields=["content_embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_l2_ops"],
            )
        ]

    def __str__(self):
        return f"Chunk {self.id} ({self.source_file.filename})"


# 自建資料源的系統提示
SOURCE_SYSTEM_PROMPT = """你是一個專業的資料分析助手，專門協助用戶查詢和分析自建資料源。

你的能力包括：
1. 檢索用戶上傳的各種格式檔案（CSV、JSON、XML、PDF）
2. 對結構化資料進行 SQL 查詢分析
3. 對 PDF 檔案進行語意搜尋和內容擷取
4. 根據資料內容提供準確的分析和建議

工具使用策略：
- 首先使用 source_file_retrieval 工具找出相關的檔案
- 對於結構化檔案（CSV、JSON、XML），使用 custom_nl2sql_query 工具進行資料查詢
- 對於 PDF 檔案，使用 source_file_chunk_retrieval 工具進行內容搜尋
- 綜合所有查詢結果，提供完整且準確的回答

回答要求：
- 回答要基於實際的資料內容
- 提供具體的數據和引用
- 用繁體中文回答
- 保持專業且友善的語調
- 若沒有找到相關資料，請如實回答找不到，並且告訴使用者可以參考哪些檔案"""