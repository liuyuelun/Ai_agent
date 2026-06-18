FROM python:3.11-slim

WORKDIR /app

# 安装依赖（利用 Docker 缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 初始化数据库
RUN python3 -c "from webapp.db import init_db; init_db()"

EXPOSE 8000

CMD ["gunicorn", "-c", "gunicorn_config.py", "webapp.app:create_app()"]
