import time
from fastapi import Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable

# Define metrics
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10)
)

MODEL_PREDICTION_DURATION = Histogram(
    'model_prediction_duration_seconds',
    'Model prediction duration in seconds',
    ['model_type'],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 7.5, 10, 20, 30, 60, 120)
)

MODEL_PREDICTION_ERROR = Counter(
    'model_prediction_error',
    'Model prediction errors',
    ['model_type', 'error_type']
)

DATA_INGESTION_DURATION = Histogram(
    'data_ingestion_duration_seconds',
    'Data ingestion duration in seconds',
    ['data_type'],
    buckets=(0.1, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300, 600)
)

MODEL_TRAINING_TOTAL = Counter(
    'model_training_total',
    'Total number of model training operations',
    ['model_type', 'status']
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint to avoid circular calls
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Record request start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Record request end time and calculate duration
        duration = time.time() - start_time
        
        # Extract endpoint and method
        endpoint = request.url.path
        method = request.method
        status = response.status_code
        
        # Update metrics
        HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status).inc()
        HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        return response

async def metrics_endpoint():
    """Endpoint for exposing Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )