FROM pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime as base

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m appuser

# Copy requirements and install dependencies
COPY --chown=appuser:appuser services/model-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install prometheus client for metrics
RUN pip install --no-cache-dir prometheus-client

# Copy service code
COPY --chown=appuser:appuser services/model-service /app/
COPY --chown=appuser:appuser services/common /app/common/

# Environment variables
ENV PYTHONPATH=/app
ENV TZ=UTC
ENV LOG_LEVEL=INFO

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]