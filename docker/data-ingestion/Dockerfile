FROM stock-prediction-platform/python:base

WORKDIR /app

# Copy requirements and install additional dependencies
COPY --chown=appuser:appuser services/data-ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY --chown=appuser:appuser services/data-ingestion /app/
COPY --chown=appuser:appuser services/common /app/common/

# Set environment variables
ENV PYTHONPATH=/app
ENV TZ=UTC
ENV LOG_LEVEL=INFO

# Switch to non-root user for better security
USER appuser

# Expose port
EXPOSE 8000

# Command to run the service
CMD ["python", "-m", "data_ingestion.main"]