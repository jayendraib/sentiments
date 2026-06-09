#FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 AS runtime
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    # Hugging Face cache directory
   # HF_HOME=/app/.cache/huggingface \
   # TRANSFORMERS_CACHE=/app/.cache/huggingface \
    # Ollama host configuration
    OLLAMA_HOST=http://ollama:11434 \
    # Make Python output unbuffered
    PYTHONUNBUFFERED=1

# Create non-root user for security
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

# Install Python 3.11, pip, and runtime dependencies (GPU + PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
   # python3.11 python3-pip python3-setuptools python3.11-venv \
    libpq5 \
    curl \
   # ffmpeg libsndfile1 libgomp1 libgl1-mesa-glx libglib2.0-0 git \
   # libcudnn8 \
   # && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create virtual environment
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and remove torch to avoid CPU-only version conflicts
COPY requirements.txt .
   # sed -i '/^torch/d'
RUN pip install -r requirements.txt

# Install CUDA-enabled PyTorch (matching your API Dockerfile)
#RUN pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

# Create cache directory for Hugging Face models with proper permissions
#RUN mkdir -p /app/.cache/huggingface && chown -R appuser:appgroup /app

# Copy application code
COPY --chown=appuser:appgroup AnalysisAPI.py analysispipelines.py ./

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the FastAPI application with uvicorn
CMD ["uvicorn", "AnalysisAPI:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
