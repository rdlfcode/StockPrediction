FROM stock-prediction-platform/pytorch:base

WORKDIR /app

# Copy requirements and install additional dependencies
COPY --chown=appuser:appuser services/model-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY --chown=appuser:appuser services/model-service /app/
COPY --chown=appuser:appuser services/common /app/common/

# Set environment variables
ENV PYTHONPATH=/app
ENV TZ=UTC
ENV LOG_LEVEL=INFO

# Switch to non-root user for better security
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]