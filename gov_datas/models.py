from django.db import models
from pgvector.django import VectorField, HnswIndex
    

class Dataset(models.Model):
    dataset_id = models.IntegerField(unique=True, verbose_name="資料集識別碼")
    url = models.URLField(verbose_name="資料集網址")
    name = models.CharField(max_length=255, verbose_name="資料集名稱")
    category = models.CharField(max_length=100, verbose_name="服務分類")
    description = models.TextField(null=True, blank=True, verbose_name="資料集描述")
    columns_description = models.JSONField(models.CharField(max_length=100))
    department = models.CharField(max_length=100, verbose_name="提供機關")
    update_frequency = models.CharField(max_length=100, verbose_name="更新頻率")
    license = models.CharField(max_length=100, verbose_name="授權方式")
    price = models.CharField(max_length=100, verbose_name="計費方式")
    contact_person = models.CharField(max_length=100, null=True, blank=True, verbose_name="聯絡人姓名")
    contact_phone = models.CharField(max_length=50, null=True, blank=True, verbose_name="聯絡人電話")
    upload_time = models.CharField(max_length=50, null=True, blank=True, verbose_name="上架日期")
    update_time = models.CharField(max_length=50, null=True, blank=True, verbose_name="詮釋資料更新時間")
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

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="files", verbose_name="所屬資料集")

    original_download_url = models.URLField(verbose_name="資料下載網址")
    filename = models.CharField(max_length=255, verbose_name="檔案名稱")
    encoding = models.CharField(max_length=50, verbose_name="編碼格式")
    format = models.CharField( max_length=20, verbose_name="檔案格式", default='csv')
    original_formats = models.CharField(
        choices=FormatChoices.choices,max_length=20, null=True, blank=True, verbose_name="原始檔案格式", 
        help_text="記錄合併前的原始格式，如：csv,json,xml"
    )
    content_md5 = models.CharField(max_length=64, verbose_name="檔案內容 MD5", unique=True)
    gridfs_id = models.CharField(max_length=100, verbose_name="GridFS ID")  # 雖然是字串，但保留 GridFS ID 作為外部參照

    def __str__(self):
        return self.filename
