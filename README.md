# 🎯 資料獵人（DataHunter）

> **_本專所呈現之資料皆為網路爬取之公開資料，站台僅提資料的呈現、查詢、請求，若要使用本站台中的內容進行任何的分析、商業、醫療...等其他功能，請務必核實資料正確性。_**

---

## ⚒️ Built With

- [Python](https://www.python.org/) - Python Programming Language
- [Django](https://www.djangoproject.com/) - Python Web Framework
- [Django Channels](https://channels.readthedocs.io/) - WebSocket Support
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
DataHunter/
├── DataHunter/              # Django 專案設定
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
POSTGRES_DB=DataHunter
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis 設定
REDIS_URL=redis://localhost:6379/0

# API 金鑰
OPENAI_API_KEY=your-openai-api-key
COHERE_API_KEY=your-cohere-api-key
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

# 啟用 pgvector 擴展
docker-compose exec postgres psql -U postgres -d DataHunter -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 創建超級用戶
python manage.py createsuperuser
```

### 5️⃣ 啟動應用程式

**重要：本專案使用 Django Channels 和 WebSocket，必須使用 ASGI 服務器**

```bash
# 啟動 Web 服務（支援 WebSocket）
daphne -p 8000 -b 0.0.0.0 DataHunter.asgi:application

# 在另一個終端啟動 Celery Worker（可選）
celery -A DataHunter worker --loglevel=info
```

### 6️⃣ 訪問應用

- **Web 應用**: http://localhost:8000
- **管理後台**: http://localhost:8000/admin/

---

## 🐳 Docker 完整部署

### 啟動所有服務

```bash
# 啟動基本服務（PostgreSQL + Redis）
docker-compose up -d postgres redis

# 啟動完整服務（包含 Celery）
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

- **衛生福利部-台灣 e 院**: 每天凌晨 1:00 自動爬取
- **政府開放資料**: 每天凌晨 1:00 自動爬取

### 手動執行

```bash
# 進入 Celery Beat 容器
docker exec -it celery-beat bash

# 手動執行症狀爬蟲
celery -A DataHunter call celery_app.crawlers.symptoms.period_send_symptom_crawler_task

# 手動執行政府資料爬蟲
celery -A DataHunter call celery_app.crawlers.gov_datas.period_crawl_government_datasets
```

### 監控狀態

```bash
# 查看 Celery 日誌
docker-compose logs -f celery-beat
docker-compose logs -f celery-static-worker

# 查看所有服務狀態
docker-compose ps
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
DEBUG=True daphne -p 8000 -b 0.0.0.0 DataHunter.asgi:application

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

---

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request 來改善這個專案！

---

## 📄 授權

本專案採用 MIT 授權條款。
