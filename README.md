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

---

## 🗂️ 專案結構

├── comming soon ~~           # comming soon ~~

└── comming soon ~~    # comming soon ~~

---

## 🚀 Local 安裝與執行方式

### 1️⃣ 安裝依賴套件

建議使用虛擬環境，並安裝以下依賴：

```bash
poetry install
```

or

```bash
pip install -r requirements.txt
```

### 2️⃣ 建立 `.env`

於專案根目錄下建立 `.env` 檔案，內容範例如下或是可參考：

```dotenv
POSTGRES_PASSWORD="資料庫密碼" # 預設為 12345678
POSTGRES_USER="資料庫使用者" # 預設為 root
POSTGRES_DB="資料庫名稱" # 預設為 DataHunter
POSTGRES_HOST="資料庫主機" # 預設為 localhost
POSTGRES_PORT="資料庫埠號" # 預設為 5432

OPENAI_API_KEY="你的 OpenAI API 金鑰"
```

### 3️⃣ 執行應用程式

```bash
python manage.py runserver
```

---

## 💿 Postgres Database 啟動方式 (Based on Docker)

```bash
docker run --name postgres-vector \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=Ac0933521 \
  -e POSTGRES_DB=DataHunter \
  -p 5432:5432 \
  -d \
  -v ./Datas/PostgresVector:/var/lib/postgresql/data \
  ankane/pgvector
```
---
