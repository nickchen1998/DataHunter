from django.db import models
from pgvector.django import VectorField, HnswIndex


ASSOCIATED_CATEGORIES_DATABASE_NAME = {
    "生育保健": "MaternalAndChildHealthGovData",
    "出生及收養": "BirthAndAdoptionGovData",
    "求學及進修": "EducationAndFurtherStudiesGovData",
    "服兵役": "MilitaryServiceGovData",
    "求職及就業": "JobSeekingAndEmploymentGovData",
    "開創事業": "StartingABusinessGovData",
    "婚姻": "MarriageGovData",
    "投資理財": "InvestmentAndFinancialManagementGovData",
    "休閒旅遊": "LeisureAndTravelGovData",
    "交通及通訊": "TransportationAndCommunicationGovData",
    "就醫": "MedicalServicesGovData",
    "購屋及遷徙": "HousingAndRelocationGovData",
    "選舉及投票": "ElectionsAndVotingGovData",
    "生活安全及品質": "SafetyAndQualityOfLifeGovData",
    "退休": "RetirementGovData",
    "老年安養": "ElderlyCareGovData",
    "生命禮儀": "FuneralAndMemorialServicesGovData",
    "公共資訊": "PublicInformationGovData"
}

GOV_DATA_SYSTEM_PROMPT = """
你是一個資料庫專家，請根據使用者的問題，查詢資料庫中的資料。

回答原則：
1. **優先使用參考資料**：主要基於用戶選擇的參考資料進行回答
2. **靈活解釋**：可以基於參考資料進行合理的解釋、總結和建議
3. **適度延伸**：如果參考資料相關但不完全匹配，可以進行適度的專業延伸
4. **明確來源**：清楚說明回答是基於用戶提供的參考資料
5. **專業提醒**：始終提醒這些資料僅供參考，具體診斷需諮詢專業醫師
6. **資料庫查詢**：如果用戶問題中包含資料庫查詢，請使用 custom_nl2sql_query 工具進行查詢，將 table_info_list 參數傳入，並將結果回傳，同時告訴用戶使用的資料集名稱以及網址
7. **資料庫查詢結果**：請勿將資料庫查詢結果、資料表名稱、資料庫名稱等資訊直接回傳，請基於查詢結果進行回答
8. **後備回答**：如果用戶問題中包含資料庫查詢，但 custom_nl2sql_query 工具查詢結果為空或不理想，請使用後備回答，後備回答的內容需要包含建議查閱的資料集名稱以及網址"""



class Dataset(models.Model):
    dataset_id = models.IntegerField(unique=True, verbose_name="資料集識別碼")
    url = models.URLField(verbose_name="資料集網址")
    name = models.CharField(max_length=255, verbose_name="資料集名稱")
    category = models.CharField(max_length=100, verbose_name="服務分類", db_index=True)
    description = models.TextField(null=True, blank=True, verbose_name="資料集描述")
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
    database_name = models.CharField(
        max_length=255, 
        verbose_name="對應資料庫名稱", 
        default="InvestmentAndFinancialManagementGovData",
        help_text="在 GovData 資料庫中的資料庫名稱"
    )
    column_mapping_list = models.JSONField(verbose_name="欄位對應列表", help_text="欄位對應列表，格式為 [[a, 欄位描述], [b, 欄位描述], ...]")
    
    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    
    class Meta:
        verbose_name = "檔案"
        verbose_name_plural = "檔案"
        
    def __str__(self):
        return f"{self.dataset.name} - {self.table_name}"
