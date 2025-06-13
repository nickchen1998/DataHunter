FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統相依性
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Poetry
RUN pip install poetry

# 複製 Poetry 配置檔案
COPY pyproject.toml ./

# 配置 Poetry（不建立虛擬環境，因為已經在容器中）
RUN poetry config virtualenvs.create false

# 安裝 Python 相依性（不使用 dev 依賴，並且不需要 lock 文件）
RUN poetry install --only=main --no-root

# 複製專案程式碼
COPY . .

# 設定環境變數
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=DataHunter.settings

# 暴露埠號（如果需要）
EXPOSE 8000

# 預設命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 