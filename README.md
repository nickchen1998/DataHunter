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
POSTGRES_PASSWORD="資料庫密碼" # 預設為 12345678
POSTGRES_HOST="資料庫主機" # 預設為 localhost
POSTGRES_VOLUME="資料庫資料夾" # 預設為 postgres_data

REDIS_HOST="Redis 主機" # 預設為 localhost
```

### 3️⃣ 建構 CSS 樣式

```bash
# 建構 Tailwind CSS
./build_css.sh

# 或開發模式（監控檔案變更）
./build_css.sh --watch
```

### 4️⃣ 執行應用程式

```bash
python manage.py runserver
```

---

## 💿 Database 啟動方式 (Based on Docker)

```bash
docker-compose up -d
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
