FROM python:3.9-slim

WORKDIR /app

# 配置 Debian 镜像源（使用阿里云镜像，提高下载速度）
# 兼容新旧版本的 Debian sources 配置
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
    else \
        sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list || true; \
    fi && \
    # 配置 pip 使用国内镜像源（清华大学镜像）
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple || true

# 安装系统依赖（添加重试机制和错误处理）
RUN apt-get update --fix-missing || apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建artifacts目录
RUN mkdir -p /app/artifacts

# 暴露端口
EXPOSE 8000

# 启动命令（在docker-compose中覆盖）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
