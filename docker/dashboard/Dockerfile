FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

# Copy frontend dependencies
COPY services/dashboard-service/frontend/package*.json ./
RUN npm ci

# Copy frontend source
COPY services/dashboard-service/frontend ./
RUN npm run build

FROM stock-prediction-platform/python:base

WORKDIR /app

# Copy requirements and install dependencies
COPY --chown=appuser:appuser services/dashboard-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY --chown=appuser:appuser services/dashboard-service /app/

# Copy built frontend assets
COPY --from=frontend-builder --chown=appuser:appuser /app/frontend/build /app/static

USER appuser

# Expose port
EXPOSE 8000

# Command to run the service
CMD ["python", "-m", "dashboard.main"]