# Multi-stage build for the dashboard service

# Frontend build stage
FROM stock-prediction-platform/node:base as frontend-builder

WORKDIR /app/frontend

# Copy frontend dependencies
COPY services/dashboard-service/frontend/package*.json ./
RUN npm ci

# Copy frontend source
COPY services/dashboard-service/frontend ./
RUN npm run build

# Backend stage
FROM stock-prediction-platform/python:base

WORKDIR /app

# Copy requirements and install dependencies
COPY --chown=appuser:appuser services/dashboard-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY --chown=appuser:appuser services/dashboard-service /app/
COPY --chown=appuser:appuser services/common /app/common/

# Copy built frontend assets from the frontend-builder stage
COPY --from=frontend-builder --chown=appuser:appuser /app/frontend/build /app/static

# Set environment variables
ENV PYTHONPATH=/app
ENV TZ=UTC
ENV LOG_LEVEL=INFO

# Switch to non-root user for better security
USER appuser

# Expose port
EXPOSE 8000

# Command to run the service
CMD ["python", "-m", "dashboard.main"]