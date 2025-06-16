# 本地機器部署指南

## 🚀 部署方式

### 方式一：Docker Compose（推薦）

#### 1. 準備環境
```bash
# 確保已安裝 Docker 和 Docker Compose
docker --version
docker-compose --version
```

#### 2. 配置環境變數
創建 `.env` 檔案：
```bash
# 基本設定
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,your-domain.com

# 資料庫設定
POSTGRES_DB=DataHunter
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-postgres-password

# Redis 設定
REDIS_URL=redis://redis:6379/0

# API 金鑰
OPENAI_API_KEY=your-openai-key
COHERE_API_KEY=your-cohere-key
```

#### 3. 啟動服務
```bash
# 建構並啟動所有服務
docker-compose up -d --build

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

#### 4. 初始化資料庫
```bash
# 執行資料庫遷移
docker-compose exec web python manage.py migrate

# 創建超級用戶
docker-compose exec web python manage.py createsuperuser

# 啟用 pgvector 擴展
docker-compose exec postgres psql -U postgres -d DataHunter -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### 5. 訪問應用
- **Web 應用**: http://localhost:8000
- **管理後台**: http://localhost:8000/admin/

### 方式二：本地開發環境

#### 1. 安裝依賴
```bash
# 安裝 Python 依賴
poetry install

# 或使用 pip
pip install -r requirements.txt  # 需要先生成
```

#### 2. 啟動資料庫服務
```bash
# 只啟動資料庫和 Redis
docker-compose up -d postgres redis
```

#### 3. 配置環境變數
創建 `.env` 檔案：
```bash
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

POSTGRES_DB=DataHunter
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

REDIS_URL=redis://localhost:6379/0
```

#### 4. 初始化資料庫
```bash
python manage.py migrate
python manage.py createsuperuser
```

#### 5. 啟動服務
```bash
# 啟動 Web 服務
daphne -p 8000 -b 0.0.0.0 DataHunter.asgi:application

# 在另一個終端啟動 Celery Worker
celery -A DataHunter worker --loglevel=info
```

## 🔧 管理命令

### Docker Compose 管理
```bash
# 停止所有服務
docker-compose down

# 重新建構並啟動
docker-compose up -d --build

# 查看日誌
docker-compose logs -f [service_name]

# 進入容器
docker-compose exec web bash
docker-compose exec postgres psql -U postgres -d DataHunter

# 備份資料庫
docker-compose exec postgres pg_dump -U postgres DataHunter > backup.sql

# 恢復資料庫
docker-compose exec -T postgres psql -U postgres DataHunter < backup.sql
```

### 應用管理
```bash
# 收集靜態檔案
docker-compose exec web python manage.py collectstatic --noinput

# 清除快取
docker-compose exec web python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# 查看 Celery 任務
docker-compose exec celery celery -A DataHunter inspect active
```

## 🌐 生產環境配置

### Nginx 反向代理
創建 `nginx.conf`：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### SSL 憑證（Let's Encrypt）
```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx

# 獲取 SSL 憑證
sudo certbot --nginx -d your-domain.com

# 自動續期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔍 監控和日誌

### 系統監控
```bash
# 查看資源使用
docker stats

# 查看磁碟使用
df -h
docker system df

# 清理未使用的 Docker 資源
docker system prune -a
```

### 應用日誌
```bash
# Django 日誌
docker-compose logs -f web

# Celery 日誌
docker-compose logs -f celery

# 資料庫日誌
docker-compose logs -f postgres

# Redis 日誌
docker-compose logs -f redis
```

## 🛠️ 故障排除

### 常見問題
1. **端口被佔用**: 修改 `docker-compose.yml` 中的端口映射
2. **資料庫連接失敗**: 檢查 PostgreSQL 服務狀態和環境變數
3. **靜態檔案載入失敗**: 執行 `collectstatic` 命令
4. **WebSocket 連接失敗**: 檢查 Redis 服務和 Channel Layer 配置

### 重置環境
```bash
# 完全重置（會刪除所有資料）
docker-compose down -v
docker-compose up -d --build
``` 