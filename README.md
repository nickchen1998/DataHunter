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
├── symptoms/               # 症狀查詢應用
├── gov_datas/              # 政府資料應用
├── celery_app/             # Celery 任務
│   └── crawlers/           # 爬蟲任務
├── templates/              # HTML 模板
├── static/                 # 靜態檔案
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
# 使用 Docker 啟動 PostgreSQL 和 Redis
docker-compose up -d
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

# 在另一個終端啟動 Celery Worker（可選）
celery -A RAGPilot worker --loglevel=info
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

#### ⚙️ Django 設定

現在只需要執行一個簡單的命令來設置 Google OAuth 應用程式：

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
# 啟動基本服務（PostgreSQL + Redis + Selenium Hub + Chrome）
docker-compose up -d

# 啟動完整服務（包含爬蟲、站台）
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
