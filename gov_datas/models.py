from django.db import models
from pgvector.django import VectorField, HnswIndex
    

class Dataset(models.Model):
    dataset_id = models.IntegerField(unique=True, verbose_name="資料集識別碼")
    url = models.URLField(verbose_name="資料集網址")
    name = models.CharField(max_length=255, verbose_name="資料集名稱")
    category = models.CharField(max_length=100, verbose_name="服務分類", db_index=True)
    description = models.TextField(null=True, blank=True, verbose_name="資料集描述")
    columns_description = models.JSONField(models.CharField(max_length=100))
    department = models.CharField(max_length=100, verbose_name="提供機關")
    update_frequency = models.CharField(max_length=100, verbose_name="更新頻率")
    license = models.CharField(max_length=100, verbose_name="授權方式")
    price = models.CharField(max_length=100, verbose_name="計費方式")
    contact_person = models.CharField(max_length=100, null=True, blank=True, verbose_name="聯絡人姓名")
    contact_phone = models.CharField(max_length=50, null=True, blank=True, verbose_name="聯絡人電話")
    upload_time = models.DateTimeField(null=True, blank=True, verbose_name="上架日期")
    update_time = models.DateTimeField(null=True, blank=True, verbose_name="詮釋資料更新時間")
    description_embeddings = VectorField(
        dimensions=1536,
        help_text="基於 rag_description 欄位並使用 OpenAI text-embedding-3-small 產生向量。"
    )


    class Meta:
        indexes = [
            HnswIndex(
                name="description_embeddings_hnsw_idx",
                fields=["description_embeddings"],
                m=16,
                ef_construction=64,
                opclasses=["vector_l2_ops"],
            )
        ]

    def __str__(self):
        return self.name


class File(models.Model):
    class FormatChoices(models.TextChoices):
        CSV = "csv"
        JSON = "json"
        XML = "xml"

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, verbose_name="所屬資料集")
    
    # 原始檔案資訊
    original_download_url = models.URLField(verbose_name="資料下載網址")
    original_format = models.CharField(
        choices=FormatChoices.choices, 
        max_length=20, 
        verbose_name="原始檔案格式"
    )
    encoding = models.CharField(max_length=50, verbose_name="編碼格式")
    
    # 內容相關
    content_md5 = models.CharField(max_length=64, verbose_name="檔案內容 MD5", unique=True)
    table_name = models.CharField(max_length=255, verbose_name="對應資料表名稱", unique=True,
                                  help_text="在 GovData 資料庫中的資料表名稱")
    
    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    
    class Meta:
        verbose_name = "檔案"
        verbose_name_plural = "檔案"
        
    def __str__(self):
        return f"{self.dataset.name} - {self.table_name}"
