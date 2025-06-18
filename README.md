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

建議使用 Poetry 管理依賴：

```bash
# 安裝 Python 依賴
poetry install
```

### 2️⃣ 環境變數設定

於專案根目錄下建立 `.env` 檔案：

```dotenv
# Django 基本設定
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# 資料庫設定
POSTGRES_DB=RAGPilot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis 設定
REDIS_URL=redis://localhost:6379/0

# API 金鑰
OPENAI_API_KEY=your-openai-api-key
COHERE_API_KEY=your-cohere-api-key

# Google OAuth 設定（可選）
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

### 6️⃣ Google OAuth 設定（可選）

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

3. **複製憑證**：
   - 複製 Client ID 和 Client Secret 到 `.env` 檔案

#### ⚙️ Django 設定

執行以下命令來設置 Google OAuth 應用程式：

```bash
python manage.py setup_google_oauth --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

#### 🎯 功能特色

- **登入頁面 Google 登入**：在 `/login/` 頁面提供「使用 Google 登入」選項
- **第三方登入管理**：在個人資料頁面（`/profile/`）的「🔗 第三方登入」標籤中管理連結
- **自動跳轉**：連結或登入後自動跳轉到適當頁面
- **安全性**：使用 OAuth 2.0 標準協議，支援 PKCE

#### 🧪 測試流程

1. **新用戶註冊**：點擊「使用 Google 登入」→ 完成授權 → 自動創建帳戶
2. **現有用戶連結**：個人資料頁面 → 第三方登入標籤 → 連結 Google
3. **快速登入**：使用已連結的 Google 帳戶一鍵登入

#### ⚠️ 注意事項

- 確保重定向 URI 在 Google Cloud Console 中設定正確
- 生產環境請使用 HTTPS
- 妥善保管 Client Secret，不要提交到版本控制

### 7️⃣ 訪問應用

- **Web 應用**: http://localhost:8000
- **管理後台**: http://localhost:8000/admin/

---

## 🐳 Docker 完整部署

### 啟動所有服務

```bash
# 啟動基本服務（PostgreSQL + Redis）
docker-compose up -d

# 啟動完整服務（包含 Celery）
docker-compose --profile production up -d
```

### 服務說明

- **postgres** - PostgreSQL 資料庫 (含 pgvector)
- **redis** - Redis 服務 (Channel Layer & Celery)
- **celery-beat** - Celery 排程服務
- **celery-*-worker** - Celery 工作進程

---

## 👤 用戶認證系統

### 登入方式

- **傳統登入**: 使用 Email/用戶名稱 + 密碼
- **Google OAuth**: 一鍵 Google 帳戶登入
- **自動註冊**: Google 登入時自動創建帳戶

### 個人資料管理

- **基本資料編輯**: 用戶名稱、姓名修改
- **密碼管理**: 安全的密碼修改功能
- **第三方登入**: Google 帳戶連結/取消連結
- **帳戶安全**: 雙重確認的帳戶刪除功能

---

## 🕷️ 爬蟲系統

### 自動排程

- **衛生福利部-台灣 e 院**: 每週日凌晨 1:00 自動爬取
- **政府開放資料**: 每天凌晨 1:00 自動爬取

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
4. **即時預覽**: 重新載入頁面即可看到效果

### 優點

- ✅ **無需建構步驟**: 不需要 Node.js 或建構工具
- ✅ **快速開發**: 修改後立即生效
- ✅ **自動更新**: CDN 自動提供最新版本
- ✅ **減少檔案大小**: 不需要本地 CSS 檔案

---

## 🔧 開發工具

### 推薦的開發環境

```bash
# 開發模式啟動
daphne -p 8000 -b 0.0.0.0 RAGPilot.asgi:application

# 或使用 Django runserver（僅限不需要 WebSocket 的開發）
python manage.py runserver 8000
```

### 常用命令

```bash
# 資料庫操作
python manage.py makemigrations
python manage.py migrate
python manage.py shell

# 靜態檔案（如有需要）
python manage.py collectstatic

# 測試
python manage.py test
```

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

---

## 📄 授權

本專案採用 MIT 授權條款。
