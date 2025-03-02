FROM stock-prediction-platform/python:base

WORKDIR /app

# Copy requirements and install dependencies
COPY --chown=appuser:appuser services/data-ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY --chown=appuser:appuser services/data-ingestion /app/

# Expose port
EXPOSE 8000

# Command to run the service
CMD ["python", "-m", "data_ingestion.main"]