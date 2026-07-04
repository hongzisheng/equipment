# ================
# 第一阶段：构建（纯 CPU，无 GPU）
# ================
FROM python:3.11-slim AS builder

ARG service_home="/opt/EasyOCR"

# 安装系统依赖
# 使用清华 Tuna 镜像源（适用于 Debian bookworm，即 python:3.11-slim）
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc g++ libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1-mesa-dev \
        libssl-dev libffi-dev python3-dev ca-certificates wget \
    && rm -rf /var/lib/apt/lists/*

# ✅ 关键：使用 PyTorch 官方 CPU 仓库安装（版本对齐！）
RUN pip install --upgrade pip \
    && pip install --no-cache-dir torch torchvision torchaudio \
       --index-url https://download.pytorch.org/whl/cpu

# 安装 EasyOCR（普通安装，非 -e）
COPY easyocr-master.tar.gz /tmp/
RUN mkdir -p "${service_home}" \
    && tar -xzf /tmp/easyocr-master.tar.gz -C "${service_home}" --strip-components=1 \
    && cd "${service_home}" \
    && pip install --no-cache-dir . \
       -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
       --trusted-host pypi.tuna.tsinghua.edu.cn \
       --timeout 1000

# 安装你的应用依赖
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --timeout 1000

# ================
# 第二阶段：运行（精简镜像）
# ================
FROM python:3.11-slim

# 安装运行时依赖（图像库，必须！否则 EasyOCR 报错）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-dev \
    && rm -rf /var/lib/apt/lists/*


# 复制整个 Python 环境（包括 bin/ 和 lib/）
COPY --from=builder /usr/local /usr/local

WORKDIR /app
COPY . .

EXPOSE 8800
CMD ["gunicorn", "--bind", "0.0.0.0:8800", "--workers", "2", "main:app"]