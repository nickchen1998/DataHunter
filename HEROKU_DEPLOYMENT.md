# Heroku 部署指南

## 🚀 部署步驟

### 1. 準備部署
```bash
# 提交所有變更
git add .
git commit -m "feat: configure for Heroku deployment with WebSocket support"

# 創建 Heroku 應用
heroku create your-app-name

# 添加 PostgreSQL 附加元件
heroku addons:create heroku-postgresql:mini

# 添加 Redis 附加元件（WebSocket 需要）
heroku addons:create heroku-redis:mini
```

### 2. 設定環境變數
```bash
# 設定 Django 密鑰
heroku config:set SECRET_KEY="your-super-secret-key-here"

# 設定除錯模式（生產環境應為 False）
heroku config:set DEBUG=False

# 設定允許的主機（可選，預設為 *）
heroku config:set ALLOWED_HOSTS="your-app-name.herokuapp.com"

# 其他 API 金鑰
heroku config:set OPENAI_API_KEY="your-openai-key"
heroku config:set COHERE_API_KEY="your-cohere-key"
```

### 3. 部署應用
```bash
# 部署到 Heroku
git push heroku main

# 執行資料庫遷移
heroku run python manage.py migrate

# 收集靜態檔案（應該會自動執行）
heroku run python manage.py collectstatic --noinput

# 創建超級用戶
heroku run python manage.py createsuperuser
```

## 🔧 WebSocket 配置說明

### 為什麼使用 Daphne 而不是 Gunicorn？

- **Gunicorn**: WSGI 伺服器，只支援 HTTP 請求
- **Daphne**: ASGI 伺服器，支援 HTTP + WebSocket

### 架構說明
```
Heroku Dyno
├── Web Process: daphne (處理 HTTP + WebSocket)
├── Worker Process: celery (處理背景任務)
└── Redis: Channel Layer (WebSocket 訊息傳遞)
```

### Channel Layers 配置
- **開發環境**: 使用 InMemoryChannelLayer
- **生產環境**: 使用 RedisChannelLayer (透過 REDIS_URL)

## 📋 檢查清單

### 部署前檢查
- [ ] `STATIC_ROOT` 已設定
- [ ] `ASGI_APPLICATION` 指向正確的 ASGI 應用
- [ ] `Procfile` 使用 `daphne` 而非 `gunicorn`
- [ ] Redis 附加元件已安裝
- [ ] 環境變數已設定

### 部署後測試
- [ ] 網站可正常訪問
- [ ] 靜態檔案正常載入
- [ ] WebSocket 連接正常
- [ ] 背景任務正常執行

## 🐛 常見問題

### WebSocket 連接失敗
```bash
# 檢查 Redis 連接
heroku config:get REDIS_URL

# 檢查日誌
heroku logs --tail

# 重啟應用
heroku restart
```

### 靜態檔案問題
```bash
# 手動收集靜態檔案
heroku run python manage.py collectstatic --noinput

# 檢查 WhiteNoise 配置
heroku config:get STATICFILES_STORAGE
```

## 🔍 監控和除錯

```bash
# 查看即時日誌
heroku logs --tail

# 查看特定進程日誌
heroku logs --tail --dyno=web
heroku logs --tail --dyno=worker

# 檢查進程狀態
heroku ps

# 重啟特定進程
heroku restart web
heroku restart worker
```

## 💡 效能優化建議

1. **升級 Dyno 類型**: 如果需要更好的效能
2. **Redis 計劃**: 根據 WebSocket 連接數選擇適當的 Redis 計劃
3. **PostgreSQL 計劃**: 根據資料量選擇適當的資料庫計劃
4. **CDN**: 考慮使用 CDN 來加速靜態檔案載入 