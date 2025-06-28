![sidebar_logo](https://github.com/nickchen1998/RAGPilot/blob/main/static/sidebar_logo.png?raw=true)

---

# 🎯 數據領航員（RAGPilot）

> **_本專所呈現之資料皆為網路爬取之公開資料，站台僅提資料的呈現、查詢、請求，若要使用本站台中的內容進行任何的分析、商業、醫療...等其他功能，請務必核實資料正確性。_**

---

## ⚒️ Built With

- [Python](https://www.python.org/) - Python Programming Language
- [Django](https://www.djangoproject.com/) - Python Web Framework
- [Django Channels](https://channels.readthedocs.io/) - WebSocket Support
- [django-allauth](https://django-allauth.readthedocs.io/) - Authentication & Social Login
- [Postgres](https://www.postgresql.org/) - Database with pgvector
- [Redis](https://redis.io/) - Channel Layer & Caching
- [OpenAI](https://openai.com/) - AI Model
- [Cohere](https://cohere.ai/) - AI Model
- [LangChain](https://www.langchain.com/) - LLM Framework
- [Celery](https://docs.celeryproject.org/en/stable/) - Asynchronous Task Queue
- [Tailwind CSS](https://tailwindcss.com/) - CSS Framework (CDN)
- [daisyUI](https://daisyui.com/) - Tailwind CSS Components (CDN)
- [Daphne](https://github.com/django/daphne) - ASGI Server

---

## 🗂️ 專案結構

```
RAGPilot/
├── RAGPilot/              # Django 專案設定
│   ├── settings.py          # 主要設定檔
│   ├── asgi.py             # ASGI 配置
│   └── urls.py             # URL 路由
├── home/                   # 首頁應用
├── profiles/               # 用戶資料應用
├── conversations/          # 對話記錄應用
├── crawlers/               # 爬蟲數據統一管理
│   ├── models/             # 資料模型
│   ├── views/              # 網頁視圖
│   ├── tools/              # LangChain 工具
│   └── admin.py            # 管理介面
├── celery_app/             # Celery 任務
│   ├── tasks/              # 任務定義
│   └── crawlers/           # 爬蟲任務實作
├── templates/              # HTML 模板
├── utils/                  # 工具函數
└── docker-compose.yml      # Docker 配置
```

---

## 🚀 快速開始

### 1️⃣ 安裝依賴套件

**請先下載 Python3.11 以上版本以及 Poetry 套件管理器**

建議使用 Poetry 管理依賴：

```bash
# 安裝 Python 依賴
poetry install
```

### 2️⃣ 環境變數設定

於專案根目錄下建立 `.env` 檔案：

```dotenv
# Django 基本設定
SECDJANGO_SECRET_KEYRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# API 金鑰
OPENAI_API_KEY=your-openai-api-key
COHERE_API_KEY=your-cohere-api-key

# Google OAuth 設定（取得方式詳見第六步）
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
```

### 3️⃣ 啟動資料庫服務

```bash
# 啟動基本服務（PostgreSQL + Redis + Selenium Hub + Chrome + Conversation Queue）
docker-compose up -d --build
```

### 4️⃣ 資料庫初始化

```bash
# 若日後資料表有更動（選用）
python manage.py makemigrations

# 執行資料庫遷移
python manage.py migrate

# 創建超級用戶
python manage.py createsuperuser
```

### 5️⃣ 啟動應用程式

**重要：本專案使用 Django Channels 和 WebSocket，必須使用 ASGI 服務器**

```bash
# 啟動 Web 服務（支援 WebSocket）
daphne -p 8000 -b 0.0.0.0 RAGPilot.asgi:application
```

### 6️⃣ Google OAuth 設定

本專案支援 Google OAuth 登入功能，讓用戶可以使用 Google 帳戶快速註冊和登入。

#### 🔧 Google Cloud Console 設定

1. **創建 OAuth 應用程式**：
   - 前往 [Google Cloud Console](https://console.cloud.google.com/)
   - 創建新專案或選擇現有專案
   - 啟用 Google+ API（在「API 和服務」→「程式庫」中搜尋並啟用）

2. **設定 OAuth 2.0 憑證**：
   - 在「API 和服務」→「憑證」中點擊「建立憑證」→「OAuth 用戶端 ID」
   - 選擇應用程式類型：「網路應用程式」
   - 設定授權重新導向 URI：
     - 開發環境：`http://localhost:8000/accounts/google/login/callback/`
     - 生產環境：`https://yourdomain.com/accounts/google/login/callback/`

3. **設定環境變數**：
   - 將 Client ID 和 Client Secret 添加到 `.env` 檔案：
   ```
   GOOGLE_OAUTH_CLIENT_ID=your_google_client_id_here
   GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret_here
   ```

4. **將設定寫入 Postgres**：
   - 現在只需要執行一個簡單的命令來設置 Google OAuth 應用程式：
   ```bash
   python manage.py setup_google_oauth
   ```

### 7️⃣ 訪問應用

- **Web 應用**: http://localhost:8000
- **管理後台**: http://localhost:8000/admin/

---

## 🐳 Docker 完整部署

### 啟動所有服務

```bash
# 啟動基本服務（PostgreSQL + Redis + Selenium Hub + Chrome + Conversation Queue）
docker-compose up -d --build

# 啟動完整服務（包含爬蟲、站台），在本地開發時不需要使用
docker-compose --profile production up -d
```

### 服務說明

- **postgres** - PostgreSQL 資料庫 (含 pgvector)
- **redis** - Redis 服務 (Channel Layer & Celery)
- **celery-beat** - Celery 排程服務
- **celery-*-worker** - Celery 工作進程

---

## 🕷️ 爬蟲系統

### 自動排程

- **衛生福利部-台灣 e 院**: 每週日凌晨 1:00 自動爬取（celery_app.crawlers.symptoms）
- **政府開放資料**: 每天凌晨 1:00 自動爬取（celery_app.crawlers.gov_datas）

所有爬蟲資料現已統一整合到 `crawlers` 應用中，便於管理和擴展。

### 爬取範例資料

#### 1️⃣ 開啟終端機並輸入下方指令進入 Python Interpreter

```python
python manage.py shell
```

#### 2️⃣ 依照你想爬取的範例資料，使用下方範例進行匯入

**請 import 對應資料源之爬蟲任務中 period 開頭的函式**
**呼叫函式時請務必接上（demo=True），否則會完整執行爬蟲**
**可以再有資料之後直接中斷爬蟲以節省時間**

```python
from celery_app.crawlers.gov_datas import period_crawl_government_datasets
```

```python
period_crawl_government_datasets(demo=True)
```

---

## 🔧 新增爬蟲協作指南

> 製作爬蟲前請務必確認資料來源是否被授權或採用某種開放方式

本節說明如何為 RAGPilot 專案添加新的爬蟲模組。每個新爬蟲都需要遵循統一的架構模式，以確保系統的一致性和可維護性。

### 🗂️ 檔案結構概覽

新增一個名為 `example` 的爬蟲時，需要創建以下檔案：

```
RAGPilot/
├── crawlers/
│   ├── models/
│   │   └── example.py          # 資料模型
│   ├── views/
│   │   └── example.py          # 網頁視圖
│   ├── tools/
│   │   └── example.py          # LangChain 工具
│   └── admin.py                # 更新管理介面
├── templates/
│   └── example.html            # 前端模板
├── celery_app/
│   └── crawlers/
│       └── example.py          # 爬蟲邏輯
└── RAGPilot/
    ├── settings.py             # 更新設定
    ├── celery.py               # 更新任務佇列
    └── urls.py                 # 更新路由
```

### 🚀 協作步驟

#### 1️⃣ 創建資料模型

在 `crawlers/models/example.py` 中定義資料表結構：

```python
from django.db import models
from django.contrib.postgres.indexes import GinIndex
from pgvector.django import VectorField, HnswIndex

class ExampleQuerySet(models.QuerySet):
    def build_queryset(self, keyword=None, category=None, **kwargs):
        """建構查詢條件的統一方法"""
        queryset = self
        
        if keyword:
            queryset = queryset.filter(title__icontains=keyword)
        
        if category:
            queryset = queryset.filter(category=category)
            
        return queryset

class ExampleManager(models.Manager):
    def get_queryset(self):
        return ExampleQuerySet(self.model, using=self._db)
    
    def build_queryset(self, **kwargs):
        return self.get_queryset().build_queryset(**kwargs)

class Example(models.Model):
    title = models.CharField(max_length=200, verbose_name="標題")
    content = models.TextField(verbose_name="內容")
    category = models.CharField(max_length=100, verbose_name="分類")
    url = models.URLField(verbose_name="原始網址")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 向量欄位 (必須設定，用於語義搜尋和 AI 查詢)
    # 使用 OpenAI text-embedding-3-small 模型，維度為 1536
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    
    objects = ExampleManager()
    
    class Meta:
        db_table = 'crawlers_example'
        verbose_name = "範例資料"
        verbose_name_plural = "範例資料"
        indexes = [
            GinIndex(fields=['title']),
            GinIndex(fields=['category']),
            # HNSW 索引名稱必須是唯一的
            HnswIndex(
                name='crawlers_example_emb_hnsw_idx',
                fields=['embedding'],
                m=16,
                ef_construction=64,
            ),
        ]
    
    def __str__(self):
        return self.title
```

**記得在 `crawlers/models/__init__.py` 中匯入新模型：**

```python
from .example import Example
```

#### 2️⃣ 創建網頁視圖

在 `crawlers/views/example.py` 中實作列表頁面：

```python
# Django 框架相關匯入
from django.views.generic import ListView                # 泛型列表視圖，提供分頁、查詢等功能
from django.contrib.auth.mixins import LoginRequiredMixin  # 登入驗證 Mixin，確保用戶已登入
from django.utils.decorators import method_decorator      # 方法裝飾器，用於在類別方法上套用裝飾器
from django.views.decorators.cache import never_cache     # 禁用快取裝飾器，確保頁面不被瀏覽器快取
from ..models import Example                              # 匯入範例資料模型
from home.mixins import UserPlanContextMixin


# 禁用快取，確保每次都能取得最新資料（特別是用於即時更新的爬蟲資料）
@method_decorator(never_cache, name='dispatch')
class ExampleListView(LoginRequiredMixin, UserPlanContextMixin, ListView):
    """
    範例資料列表頁面
    
    繼承關係：
    - LoginRequiredMixin: 提供登入驗證功能
    - ListView: 提供列表顯示和分頁功能
    """
    
    # === 基本設定 ===
    model = Example                    # 指定要查詢的資料模型
    template_name = 'examples.html'    # 指定要使用的 HTML 模板檔案
    context_object_name = 'examples'   # 在模板中使用的變數名稱 (預設是 object_list)
    paginate_by = 20                   # 每頁顯示 20 筆資料，自動處理分頁邏輯
    login_url = '/login/'              # 未登入用戶將被重定向到此 URL

    def get_queryset(self):
        """
        自定義查詢邏輯
        
        功能：
        1. 從 URL 參數取得搜尋條件
        2. 使用模型的統一查詢方法進行過濾
        3. 按建立時間倒序排列 (最新的在前面)
        
        Returns:
            QuerySet: 過濾後的資料查詢集合
        """
        # 從 GET 參數取得搜尋條件 (如果沒有則為 None)
        keyword = self.request.GET.get('keyword')    # 關鍵字搜尋
        category = self.request.GET.get('category')  # 分類篩選
        
        # 使用模型自定義的統一查詢方法進行過濾
        return Example.objects.build_queryset(
            keyword=keyword,
            category=category
        ).order_by('-created_at')  # 按建立時間倒序排列

    def get_context_data(self, **kwargs):
        """
        添加額外的上下文資料到模板
        
        功能：
        1. 保留父類別的所有上下文資料 (包含分頁資訊)
        2. 添加當前的搜尋條件 (用於在表單中保持選中狀態)
        3. 添加所有可用的分類選項 (用於下拉選單)
        4. 添加當前頁面路徑 (用於表單提交)
        
        Returns:
            dict: 包含所有模板變數的字典
        """
        # 取得父類別的所有上下文資料 (包含 examples、page_obj 等)
        context = super().get_context_data(**kwargs)
        
        # === 保存當前搜尋條件 ===
        # 這些變數會傳遞到模板，用於在搜尋表單中保持用戶的輸入狀態
        context['keyword'] = self.request.GET.get('keyword', '')      # 關鍵字搜尋框的值
        context['category'] = self.request.GET.get('category', '')    # 分類下拉選單的選中值
        context['request_path'] = self.request.path                   # 當前頁面路徑，用於表單的 action 屬性
        
        # === 取得所有分類選項 ===
        # 查詢資料庫中所有不重複的分類，用於生成分類下拉選單
        context['categories'] = Example.objects.values_list('category', flat=True)\
                                               .distinct()\
                                               .order_by('category')
        
        return context
```

#### 3️⃣ 創建 LangChain 工具

在 `crawlers/tools/example.py` 中實作 AI 查詢工具：

```python
from typing import Dict, Any, Optional
from langchain.tools import BaseTool
from ..models import Example

class ExampleDataRetrievalTool(BaseTool):
    name = "example_data_retrieval"
    description = """
    用於搜尋範例資料的工具。
    
    參數：
    - keyword: 關鍵字搜尋 (選填)
    - category: 分類篩選 (選填)
    - limit: 返回結果數量限制，預設20筆
    """
    
    def _run(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20,
        **kwargs: Any
    ) -> str:
        try:
            # 使用統一的查詢方法
            queryset = Example.objects.build_queryset(
                keyword=keyword,
                category=category
            )[:limit]
            
            if not queryset.exists():
                return f"未找到符合條件的範例資料。"
            
            results = []
            for item in queryset:
                results.append({
                    'title': item.title,
                    'category': item.category,
                    'content': item.content[:200] + '...' if len(item.content) > 200 else item.content,
                    'url': item.url,
                })
            
            return f"找到 {len(results)} 筆範例資料：\n" + \
                   "\n".join([f"• {r['title']} ({r['category']}): {r['content']}" for r in results])
            
        except Exception as e:
            return f"搜尋範例資料時發生錯誤：{str(e)}"
    
    async def _arun(self, **kwargs: Any) -> str:
        return self._run(**kwargs)
```

#### 4️⃣ 創建前端模板

在 `templates/examples.html` 中創建使用者介面：

```html
<!-- 參考現有的 templates/gov_datas.html 或 templates/symptoms.html -->
<!-- 記得調整標題、搜尋欄位、資料顯示格式等 -->
```

#### 5️⃣ 實作爬蟲邏輯

在 `celery_app/crawlers/example.py` 中實作爬蟲：

**重要概念說明：**
- **`period_` 函數**：定期分派爬蟲任務的程式，負責任務調度和管理
- **實際爬蟲任務**：執行具體爬取工作的函數，由 `period_` 函數分派
- **一隻爬蟲至少需要兩個 function**：分派任務 + 執行任務

```python
import logging
from RAGPilot.celery import app
from crawlers.models import Example

logger = logging.getLogger(__name__)

# ==================== 任務分派器 ====================
@app.task()
def period_crawl_example_data(demo=False):
    """
    定期分派範例資料爬取任務
    
    功能：
    1. 這是任務分派器，不直接執行爬蟲
    2. 負責任務調度、錯誤處理、日誌記錄
    3. 將實際的爬蟲工作分派給專門的爬蟲任務
    
    Args:
        demo (bool): 是否為演示模式，True 時只爬取少量資料
    """
    try:
        logger.info("開始分派範例資料爬取任務...")
        
        if demo:
            logger.info("演示模式：分派少量資料爬取任務")
            # 分派演示任務
            result = crawl_example_data_task.delay(demo=True, crawl_count=5)
        else:
            logger.info("完整模式：分派完整資料爬取任務")
            # 分派完整任務
            result = crawl_example_data_task.delay(demo=False, crawl_count=-1)
        
        logger.info(f"任務已分派，任務 ID: {result.id}")
        return f"範例資料爬取任務已分派，任務 ID: {result.id}"
        
    except Exception as e:
        logger.error(f"分派範例資料爬取任務時發生錯誤：{str(e)}")
        raise

# ==================== 實際爬蟲任務 ====================
# 隊列設定說明：
# - 任務的隊列設定統一在 RAGPilot/celery.py 中進行配置
# - 使用 selenium 的任務：配置到 'dynamic' 隊列 (動態隊列，適合需要瀏覽器的任務)
# - 使用 requests 的任務：配置到 'static' 隊列 (靜態隊列，適合 HTTP 請求任務)

@app.task()  # 隊列設定請在 RAGPilot/celery.py 中配置
def crawl_example_data_task(demo=False, crawl_count=-1):
    """
    執行範例資料爬取的實際任務
    
    功能：
    1. 執行具體的爬蟲邏輯
    2. 發送 HTTP 請求或操作瀏覽器
    3. 解析資料並儲存到資料庫
    
    Args:
        demo (bool): 是否為演示模式
        crawl_count (int): 爬取數量限制，-1 表示無限制
    """
    try:
        logger.info(f"開始執行範例資料爬取任務，爬取數量: {crawl_count}")
        
        # === 爬蟲邏輯實作 ===
        # 1. 發送 HTTP 請求 (使用 requests)
        # 2. 解析 HTML/JSON (使用 BeautifulSoup/json)
        # 3. 儲存到資料庫
        # 4. 生成向量嵌入 (必須)
        
        # 範例：使用 requests 進行爬取
        import requests
        from bs4 import BeautifulSoup
        from langchain_openai import OpenAIEmbeddings
        
        # 初始化 OpenAI Embeddings (使用專案統一的嵌入模型)
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # 範例假資料 (實際開發時替換為真實爬蟲邏輯)
        sample_data = [
            {"title": f"範例資料 {i}", "content": f"這是第 {i} 筆範例內容", 
             "category": "測試分類", "url": f"https://example.com/{i}"}
            for i in range(1, (crawl_count if crawl_count > 0 else 100) + 1)
        ]
        
        created_count = 0
        for data in sample_data:
            # 計算向量嵌入 (使用標題或內容，根據業務需求決定)
            embedding_text = f"{data['title']} {data['content']}"  # 合併標題和內容
            embedding_vector = embeddings.embed_query(embedding_text)
            
            # 將向量添加到資料中
            data['embedding'] = embedding_vector
            
            example, created = Example.objects.get_or_create(
                title=data['title'],
                defaults=data
            )
            if created:
                created_count += 1
                
            # 演示模式時，處理少量資料後即可停止
            if demo and created_count >= 5:
                break
        
        logger.info(f"範例資料爬取完成，新增 {created_count} 筆資料")
        return f"成功爬取 {created_count} 筆範例資料"
        
    except Exception as e:
        logger.error(f"執行範例資料爬取任務時發生錯誤：{str(e)}")
        raise

# ==================== Selenium 範例 (選用) ====================
# 如果需要使用 Selenium 進行動態網頁爬取，可以參考以下範例：

@app.task()  # 隊列設定請在 RAGPilot/celery.py 中配置
def crawl_example_data_with_selenium_task(demo=False, crawl_count=-1):
    """
    使用 Selenium 執行範例資料爬取任務
    
    適用於：
    - 需要 JavaScript 渲染的動態網頁
    - 需要模擬用戶操作的情況
    - 需要處理複雜表單或登入流程
    """
    try:
        logger.info("開始執行 Selenium 範例資料爬取任務")
        
        # 使用 Selenium WebDriver
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        
        # Chrome 選項設定
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 無頭模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 連接到 Docker 中的 Selenium Hub
        driver = webdriver.Remote(
            command_executor='http://selenium-hub:4444/wd/hub',
            options=chrome_options
        )
        
        # 執行爬蟲邏輯
        # driver.get("https://example.com")
        # elements = driver.find_elements(By.CLASS_NAME, "data-item")
        # ... 處理資料 ...
        
        driver.quit()
        
        logger.info("Selenium 範例資料爬取完成")
        return "Selenium 爬取任務完成"
        
    except Exception as e:
        logger.error(f"執行 Selenium 爬取任務時發生錯誤：{str(e)}")
        raise

# ==================== 輔助函數 ====================
def parse_example_page(url):
    """解析單一頁面的輔助函數"""
    import requests
    from bs4 import BeautifulSoup
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 解析邏輯
        title = soup.find('title').text if soup.find('title') else ''
        content = soup.find('div', class_='content').text if soup.find('div', class_='content') else ''
        
        return {
            'title': title,
            'content': content,
            'url': url
        }
    except Exception as e:
        logger.error(f"解析頁面 {url} 時發生錯誤：{str(e)}")
        return None

def generate_example_embedding(text):
    """
    生成文本向量嵌入的輔助函數 (選用)
    
    注意：實際開發時建議直接在任務中使用，不需要額外封裝函數
    """
    from langchain_openai import OpenAIEmbeddings
    
    # 使用專案統一的 OpenAI 嵌入模型
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return embeddings.embed_query(text)
```

### 📋 任務架構說明

**每個爬蟲模組包含的函數：**

1. **`period_crawl_*`** (必須)
   - 定期分派任務的排程器
   - 負責任務調度和錯誤處理
   - 由 Celery Beat 定期呼叫

2. **`crawl_*_task`** (必須)
   - 執行實際爬蟲工作的任務
   - 處理 HTTP 請求或 Selenium 操作
   - 資料解析和儲存邏輯

3. **輔助函數** (選用)
   - 頁面解析函數
   - 資料處理函數
   - 向量嵌入生成函數

### 🔄 隊列設定原則

隊列設定統一在 `RAGPilot/celery.py` 的 `task_routes` 中配置：

| 爬蟲類型 | 隊列設定 | 適用情況 | 範例 |
|---------|---------|---------|------|
| `'static'` | 靜態隊列 | 使用 requests 的 HTTP 爬蟲 | API 資料、簡單網頁 |
| `'dynamic'` | 動態隊列 | 使用 Selenium 的瀏覽器爬蟲 | SPA 應用、需要 JS 渲染 |

#### 6️⃣ 更新路由配置

在 `crawlers/urls.py` 中添加新路由：

```python
from django.urls import path
from .views.example import ExampleListView

urlpatterns = [
    # ... 現有路由 ...
    path('examples/list/', ExampleListView.as_view(), name='example-list'),
]
```

#### 7️⃣ 更新管理介面

在 `crawlers/admin.py` 中註冊新模型：

```python
from django.contrib import admin
from .models import Example

@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
```

#### 8️⃣ 更新 Celery 設定

在 `RAGPilot/celery.py` 中添加定期任務和隊列路由設定：

```python
from celery.schedules import crontab

# === 定期任務設定 ===
app.conf.beat_schedule = {
    # ... 現有任務 ...
    'period-crawl-example-data': {
        'task': 'celery_app.crawlers.example.period_crawl_example_data',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨 2 點執行
    },
}

# === 任務隊列路由設定 ===
app.conf.task_routes = {
    # ... 現有路由 ...
    
    # 範例爬蟲任務路由
    'celery_app.crawlers.example.crawl_example_data_task': {'queue': 'static'},
    'celery_app.crawlers.example.crawl_example_data_with_selenium_task': {'queue': 'dynamic'},
    
    # 隊列設定原則：
    # - 'static': 使用 requests 的 HTTP 爬蟲任務
    # - 'dynamic': 使用 Selenium 的瀏覽器爬蟲任務
}
```

### ⚠️ 重要注意事項

1. **period 任務命名**: 爬蟲主任務必須以 `period_` 開頭
2. **demo 參數**: 所有 period 任務都必須支援 `demo=True` 參數用於測試
3. **向量欄位 (必須)**: 模型中至少要設定一個 `VectorField` 欄位用於存放向量嵌入
4. **向量計算方式**: 務必使用 `OpenAIEmbeddings(model="text-embedding-3-small").embed_query()` 計算向量
5. **向量維度**: 使用 `text-embedding-3-small` 模型時，向量維度設定為 1536
6. **向量索引**: 確保 HNSW 索引名稱唯一，避免與其他模型衝突
7. **統一查詢方法**: 使用 `build_queryset` 方法統一查詢邏輯
8. **錯誤處理**: 確保爬蟲有適當的異常處理和日誌記錄
9. **資料庫遷移**: 創建新模型後記得執行 `python manage.py makemigrations` 和 `python manage.py migrate`

### 🧪 測試新爬蟲

```bash
# 進入 Django shell
python manage.py shell

# 測試爬蟲 (演示模式)
from celery_app.crawlers.example import period_crawl_example_data
period_crawl_example_data(demo=True)

# 測試查詢方法
from crawlers.models import Example
examples = Example.objects.build_queryset(keyword="測試")
print(f"找到 {examples.count()} 筆資料")

# 測試 LangChain 工具
from crawlers.tools.example import ExampleDataRetrievalTool
tool = ExampleDataRetrievalTool()
result = tool.run(keyword="範例")
print(result)
```

遵循以上步驟，就能成功為 RAGPilot 添加新的爬蟲模組！

---

## 🎨 前端開發

### 樣式框架

本專案使用 **CDN 版本** 的 Tailwind CSS 和 daisyUI：

- **Tailwind CSS**: https://cdn.tailwindcss.com
- **daisyUI**: https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css

### 開發流程

1. **修改 HTML 模板**: 直接在 `templates/` 中編輯 HTML
2. **使用 Tailwind 類**: 無需建構步驟，直接使用 Tailwind CSS 類
3. **daisyUI 組件**: 直接使用 daisyUI 提供的組件類
4. **重啟服務**: 由於使用 ASGI 方式保持前後台同步，需要重啟服務。
5. **即時預覽**: 若修改部分與 WebSocket 無關，可使用 `python manage.py runserver 8000` 即可在儲存後即時預覽。

---

## 📝 注意事項

1. **WebSocket 支援**: 生產環境必須使用 Daphne 或其他 ASGI 服務器
2. **資料庫**: 需要 PostgreSQL 並啟用 pgvector 擴展
3. **API 金鑰**: 確保設定正確的 OpenAI 和 Cohere API 金鑰
4. **環境變數**: 生產環境請使用安全的 SECRET_KEY 和密碼
5. **Google OAuth**: 如啟用，請確保重定向 URI 設定正確

---

## 🛜 Google Cloud SQL 連線方式

Google Cloud SQL 部署相關連線資訊請找專案負責人索取。

### 1. 本機環境首次設定 (每台電腦只需一次)

在開始之前，請確保您的 macOS 電腦已安裝 [Homebrew](https://brew.sh/)。以下步驟將為您的電腦安裝必要的工具並完成授權。

#### **步驟 1.1：安裝 Google Cloud CLI**
Google Cloud CLI (`gcloud`) 是與 GCP 互動的主要命令列工具。
```bash
brew install --cask google-cloud-sdk
```

#### **步驟 1.2：安裝 Cloud SQL Auth Proxy**
此工具會在您的本機與雲端資料庫之間建立一條安全的加密通道。
```bash
brew install cloud-sql-proxy
```

#### **步驟 1.3：授權您的 Google 帳號**
這個步驟會將您的本機 CLI 與您的 Google 帳號綁定，並取得使用 Proxy 的權限。
```bash
# 首次執行，引導您登入並選擇專案
gcloud init

# 取得應用程式的預設憑證
gcloud auth application-default login
```
請依照終端機的指示，在瀏覽器中完成登入與授權。

### 2. 每日開發連線流程

完成首次設定後，每天要開始工作時，請遵循以下流程。

#### **步驟 2.1：啟動 Cloud SQL Auth Proxy**
開啟一個**新的終端機視窗**，執行以下指令。
**注意：此視窗在您工作期間必須保持開啟，最小化即可。**

```bash
# 將 <INSTANCE_CONNECTION_NAME> 換成您資料庫的連線名稱
cloud-sql-proxy <INSTANCE_CONNECTION_NAME>
```
當您看到 `Ready for new connections` 訊息時，代表通道已成功建立，這時候請不要關閉這個終端機，您可以直接使用前方提到的指令在另一個終端機當中啟動整個 Django 服務。



---

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request 來改善這個專案！
