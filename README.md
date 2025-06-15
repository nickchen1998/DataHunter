# 🎯 資料獵人（DataHunter）

> **_本專所呈現之資料皆為網路爬取之公開資料，站台僅提資料的呈現、查詢、請求，若要使用本站台中的內容進行任何的分析、商業、醫療...等其他功能，請務必核實資料正確性。_**

---

## ⚒️ Built With

- [Python](https://www.python.org/) - Python Programming Language
- [Django](https://www.djangoproject.com/) - Python Web Framework
- [Postgres](https://www.postgresql.org/) - Database
- [Docker](https://www.docker.com/) - Containerization Platform
- [Redis](https://redis.io/) - In-memory Data Structure Store
- [OpenAI](https://openai.com/) - AI Model
- [LangChain](https://www.langchain.com/) - LLM Framework
- [Celery](https://docs.celeryproject.org/en/stable/) - Asynchronous Task Queue
- [Tailwind CSS](https://tailwindcss.com/) - CSS Framework
- [daisyUI](https://daisyui.com/) - Tailwind CSS Components

---

## 🗂️ 專案結構

├── comming soon ~~           # comming soon ~~

└── comming soon ~~    # comming soon ~~

---

## 🚀 Local 安裝與執行方式

### 1️⃣ 安裝依賴套件

#### Python 依賴

建議使用虛擬環境，並安裝以下依賴：

```bash
poetry install
```

or

```bash
pip install -r requirements.txt
```

#### Node.js 依賴（用於 CSS 建構）

```bash
npm install
```

### 2️⃣ 建立 `.env`

於專案根目錄下建立 `.env` 檔案，內容範例如下或是可參考：

```dotenv
OPENAI_API_KEY="你的 OpenAI API 金鑰"
```

下面為本專案所有帶有預設值的的環境變數：

```dotenv
# 資料庫相關
POSTGRES_PASSWORD="資料庫密碼" # 預設為 postgres
POSTGRES_HOST="資料庫主機" # 預設為 localhost
POSTGRES_USER="資料庫使用者" # 預設為 postgres
POSTGRES_VOLUME="資料庫資料夾" # 預設為 ./postgres_data

# Redis 相關（Celery 使用）
REDIS_HOST="Redis 主機" # 預設為 localhost
REDIS_VOLUME="Redis 資料夾" # 預設為 ./redis_data

# OpenAI API（爬蟲和 AI 功能使用）
OPENAI_API_KEY="你的 OpenAI API 金鑰" # 必填
```

### 3️⃣ 建構 CSS 樣式

```bash
# 建構 Tailwind CSS
./build_css.sh

# 或開發模式（監控檔案變更）
./build_css.sh --watch
```

### 4️⃣ 執行應用程式

**重要：由於本專案使用了 Django Channels 和 WebSocket 功能，必須使用 ASGI 服務器運行**

```bash
# 使用 daphne ASGI 服務器（推薦）
daphne -p 8000 DataHunter.asgi:application

# 或者使用 uvicorn（替代方案）
uvicorn DataHunter.asgi:application --host 127.0.0.1 --port 8000
```

**注意：不要使用 `python manage.py runserver`，因為它不支援 WebSocket 連線**

---

## 🐳 Docker 容器化部署

### 本機開發環境（不含爬蟲服務）

如果您只需要進行一般的 Web 開發，不需要運行爬蟲任務，可以只啟動基本服務：

```bash
# 只啟動 PostgreSQL、Selenium Hub、Chrome 等基本服務
docker-compose up -d
```

這將啟動以下服務：
- `postgres` - PostgreSQL 資料庫
- `postgres-init` - 資料庫初始化
- `selenium-hub` - Selenium Grid Hub
- `chrome` - Chrome 瀏覽器節點

### 完整生產環境（包含爬蟲服務）

如果需要運行完整的爬蟲系統，請使用以下命令：

```bash
# 啟動所有服務，包含 Celery 相關服務
docker-compose --profile production up -d

# 或者使用 celery profile
docker-compose --profile celery up -d
```

這將額外啟動以下 Celery 相關服務：
- `redis` - Redis 作為 Celery 的 broker 和 backend
- `celery-beat` - Celery 排程服務
- `celery-static-worker` - 處理靜態爬蟲任務（5 個 worker）
- `celery-dynamic-worker` - 處理動態爬蟲任務（3 個 worker）
- `celery-default-worker` - 處理預設佇列任務（2 個 worker）

---

## 🕷️ 爬蟲系統說明

### 架構概述

本專案使用 Celery 作為分散式任務佇列，實現自動化的資料爬取系統：

- **Celery Beat**：負責排程管理，每天凌晨 1:00 自動觸發爬蟲任務
- **多佇列設計**：不同類型的爬蟲分配到專用佇列，避免資源競爭
- **Redis**：作為訊息代理和結果後端

### 爬蟲任務

1. **衛生福利部-台灣 e 院爬蟲** (`symptoms`)
   - 任務：`period_send_symptom_crawler_task`
   - 佇列：`static_crawler_queue`
   - 排程：每天凌晨 1:00

2. **政府開放資料爬蟲** (`gov_datas`)
   - 任務：`period_crawl_government_datasets`
   - 佇列：`dynamic_crawler_queue`
   - 排程：每天凌晨 1:00

### 手動執行爬蟲

如果需要手動觸發爬蟲任務，可以使用以下命令：

```bash
# 進入容器
docker exec -it celery-beat bash

# 手動執行症狀爬蟲
celery -A DataHunter call celery_app.crawlers.symptoms.period_send_symptom_crawler_task

# 手動執行政府資料爬蟲
celery -A DataHunter call celery_app.crawlers.gov_datas.period_crawl_government_datasets
```

### 監控 Celery 狀態

```bash
# 查看 Celery Beat 日誌
docker-compose logs -f celery-beat

# 查看 Worker 日誌
docker-compose logs -f celery-static-worker
docker-compose logs -f celery-dynamic-worker

# 查看所有 Celery 服務狀態
docker-compose ps | grep celery
```

---

## 🎨 前端開發說明

本專案使用 Tailwind CSS + daisyUI 進行樣式開發：

- **CSS 源文件**：`static/css/input.css`
- **生成文件**：`static/css/output.css`（自動生成，不需手動編輯）

### 樣式修改流程

1. 修改 HTML 模板中的 Tailwind 類或 daisyUI 組件
2. 如需自定義樣式，編輯 `static/css/input.css`
3. 執行 `./build_css.sh` 重新建構 CSS
4. 重新載入頁面查看效果

---
