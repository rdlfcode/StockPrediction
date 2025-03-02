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

# Copy service code
COPY --chown=appuser:appuser services/model-service /app/

USER appuser

# Expose port
EXPOSE 8000

# Command to run the service
CMD ["python", "-m", "model_service.main"]