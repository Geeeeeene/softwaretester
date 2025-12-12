FROM python:3.9-slim

WORKDIR /app

# 使用国内镜像源（Debian bookworm），加快 apt 下载
# 配置阿里云镜像源（包含 Qt 等开发包）
ENV DEBIAN_FRONTEND=noninteractive
# 设置 UTF-8 编码，解决中文乱码问题
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUNBUFFERED=1
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's|http://deb.debian.org|http://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources && \
        sed -i 's|http://security.debian.org|http://mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list.d/debian.sources; \
    else \
        echo "deb http://mirrors.aliyun.com/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
        echo "deb http://mirrors.aliyun.com/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
        echo "deb http://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list; \
    fi && \
    apt-get clean && \
    # 配置 pip 使用国内镜像源（清华大学镜像）
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple || true

# 安装系统依赖 + 静态分析工具（cppcheck + clazy）
# clazy 依赖 clang，安装一起
# 同时安装 Qt5 开发包（Clazy 分析 Qt 项目需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    cppcheck \
    clazy \
    clang \
    qtbase5-dev \
    qtbase5-dev-tools \
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
