FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/tmp/huggingface

# Install Python, pip, and setuptools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-setuptools \
    ffmpeg libsndfile1 libgomp1 libgl1-mesa-glx libglib2.0-0 git \
    libcudnn8 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install CUDA-enabled PyTorch
RUN pip3 install --upgrade pip setuptools wheel && \
    pip3 install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121 && \
    pip3 install torchmetrics==1.4.0.post0 pytorch-lightning==2.3.3 && \
    pip3 install ctranslate2==4.4.0 whisperx==3.7.4 --no-deps && \
    pip3 install pyannote-audio==3.3.2 transformers==4.42.0 accelerate==0.33.0 && \
    pip3 install faster-whisper && \
    pip3 install -r requirements.txt

RUN python3 -c "import nltk; nltk.download('punkt', quiet=True)"

COPY app.py .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
