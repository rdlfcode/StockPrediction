# Multi-stage build file to create all base images for the Stock Prediction Platform
# This file builds multiple tagged images that serve as bases for other services

# -----------------------------------------------------------------------------
# Stage 1: Python Base Image
# -----------------------------------------------------------------------------
    FROM python:3.13-slim AS python-base

    # Set working directory
    WORKDIR /app
    
    # Set environment variables
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1 \
        PYTHONHASHSEED=random \
        PIP_NO_CACHE_DIR=off \
        PIP_DISABLE_PIP_VERSION_CHECK=on \
        PIP_DEFAULT_TIMEOUT=100
    
    # Install system dependencies
    RUN apt-get update \
        && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        wget \
        curl \
        git \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*
    
    # Create a non-root user
    RUN groupadd -g 1000 appuser && \
        useradd -u 1000 -g appuser -m appuser
    
    # Install base Python packages
    COPY requirements-base.txt .
    RUN pip install --no-cache-dir -r requirements-base.txt
    
    # Install prometheus client for metrics
    RUN pip install --no-cache-dir prometheus-client
    
    # Health check
    HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
        CMD python -c "import requests; requests.get('http://localhost:8000/health')"
    
    # -----------------------------------------------------------------------------
    # Stage 2: PyTorch Image
    # -----------------------------------------------------------------------------
    FROM python-base AS pytorch-base
    
    # Install CUDA and cuDNN (needed for PyTorch with CUDA support)
    # Note: This has been simplified. In a real setup, you would need to match CUDA and cuDNN versions
    # with the specific PyTorch requirements
    RUN apt-get update && apt-get install -y --no-install-recommends \
        gnupg2 \
        && apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub \
        && echo "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64 /" > /etc/apt/sources.list.d/cuda.list \
        && apt-get update && apt-get install -y --no-install-recommends \
        cuda-minimal-build-12-6 \
        libcudnn8 \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*
    
    # Install PyTorch with CUDA support
    RUN pip install --no-cache-dir torch==2.6.0+cu126 torchvision==0.17.0+cu126 torchaudio==2.6.0+cu126 -f https://download.pytorch.org/whl/torch_stable.html
    
    # Additional ML libraries common for model service
    RUN pip install --no-cache-dir \
        scikit-learn \
        pandas \
        statsmodels \
        scipy \
        matplotlib \
        seaborn \
        nltk \
        transformers
    
    # -----------------------------------------------------------------------------
    # Stage 3: Node.js Image for React Frontend
    # -----------------------------------------------------------------------------
    FROM node:18-alpine AS node-base
    
    WORKDIR /app
    
    # Install common frontend dependencies
    RUN npm install -g npm@latest
    
    # -----------------------------------------------------------------------------
    # Stage 4: Combined Image (Optional - if you want a single image with everything)
    # -----------------------------------------------------------------------------
    FROM pytorch-base AS combined-base
    
    # Install Node.js
    RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
        && apt-get install -y nodejs \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*
    
    # Verify installations
    RUN python --version && \
        node --version && \
        npm --version && \
        python -c "import torch; print(f'PyTorch {torch.__version__}')" && \
        python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
    
    # Set user to appuser for better security
    USER appuser