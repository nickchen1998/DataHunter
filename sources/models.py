from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField, HnswIndex


class SourceFileFormat(models.TextChoices):
    PDF = 'pdf'
    DOCX = 'docx'
    TXT = 'txt'
    CSV = 'csv'
    XLS = 'xls'
    JSON = 'json'


class ProcessingStatus(models.TextChoices):
    PENDING = 'pending', '等待處理'
    PROCESSING = 'processing', '處理中'
    COMPLETED = 'completed', '處理完成'
    FAILED = 'failed', '處理失敗'


class SourceFileParserType(models.TextChoices):
    BASE = 'base', '基礎解析'
    LAYOUTLM = 'layoutlm', 'LayoutLM'
    GOOGLE_DOCUMENT_AI = 'google_document_ai', 'Google Document AI'


# Create your models here.
class Source(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    description = models.TextField()

    is_deleted = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class SourceFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)

    filename = models.CharField(max_length=255)
    size = models.FloatField(help_text="檔案大小，單位為 MB")
    format = models.CharField(max_length=10, choices=SourceFileFormat.choices)
    summary = models.TextField(null=True, blank=True)

    tmp_file_name = models.CharField(max_length=255, help_text="暫存檔案名稱，用於儲存上傳的檔案")
    chunking_status = models.CharField(max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


class SourceFileTable(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source_file = models.ForeignKey(SourceFile, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=255)
    database_name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)


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
        indexes = [
            HnswIndex(
                name="file_chunk_embedding_hnsw_idx",
                fields=["content_embedding"],
                dimensions=1536,
            )
        ]