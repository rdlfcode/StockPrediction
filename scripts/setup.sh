#!/bin/bash

# Stock Prediction Platform Setup Script
set -e

# Function to display usage information
usage() {
  echo "Usage: $0 [OPTIONS]"
  echo "Setup the Stock Prediction Platform"
  echo
  echo "Options:"
  echo "  -e, --env ENV         Environment (development, staging, production)"
  echo "  -h, --help            Display this help and exit"
}

# Default values
ENV="development"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -e|--env)
      ENV="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: Unknown option $1"
      usage
      exit 1
      ;;
  esac
done

# Load environment variables
if [ -f ".env.$ENV" ]; then
  echo "Loading environment variables from .env.$ENV"
  export $(cat ".env.$ENV" | grep -v '^#' | xargs)
elif [ -f ".env" ]; then
  echo "Loading environment variables from .env"
  export $(cat ".env" | grep -v '^#' | xargs)
else
  echo "Error: No .env file found"
  exit 1
fi

# Install uv if it's not already installed
if ! command -v uv &> /dev/null; then
  echo "Installing uv..."
  pip install uvloop
fi

# Use uv to install Python dependencies
echo "Installing Python dependencies..."
uv install

# Start services if they are not running
if ! docker-compose ps | grep -q "Up"; then
  echo "Starting services..."
  docker-compose up -d

  # Wait for services to start
  echo "Waiting for services to start..."
  sleep 10
fi

# Initialize database
echo "Initializing database..."

echo "Creating schemas and tables..."
docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/01_create_schema.sql
docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/02_stock_data_tables.sql
docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/03_model_management_tables.sql
docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/04_predictions_tables.sql
docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/05_metrics_tables.sql

echo "Initializing TimescaleDB..."
docker-compose exec timescaledb psql -U "$POSTGRES_USER" -d "${POSTGRES_DB}_timeseries" -c "
    CREATE EXTENSION IF NOT EXISTS timescaledb;
    SELECT create_hypertable('stock_data.price_data', 'timestamp', if_not_exists => TRUE);
    SELECT create_hypertable('stock_data.feature_data', 'timestamp', if_not_exists => TRUE);
    SELECT create_hypertable('predictions.stock_predictions', 'prediction_timestamp', if_not_exists => TRUE);
  "

echo "Initializing MinIO buckets..."
docker-compose exec minio mc alias set myminio "http://localhost:9000" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
docker-compose exec minio mc mb myminio/"$MODELS_BUCKET" --ignore-existing
docker-compose exec minio mc mb myminio/"$DATASETS_BUCKET" --ignore-existing

echo "Database initialization completed"

# Import initial stock data
echo "Importing stock data..."

# Import S&P 500 stocks
echo "Importing S&P 500 stocks..."
curl -X POST "http://localhost:8001/api/stocks/import" -H "Content-Type: application/json" -d '{"source": "sp500"}'

# Import historical data
echo "Importing historical data (this may take a while)..."
curl -X POST "http://localhost:8001/api/data/import_historical" -H "Content-Type: application/json" -d '{"days": 730}'

# Enable real-time data ingestion
echo "Enabling real-time data ingestion..."
curl -X POST "http://localhost:8001/api/data/enable_realtime" -H "Content-Type: application/json" -d '{"interval_minutes": 15}'

echo "Data import completed"

# Train initial models
echo "Training initial models..."

# Train TFT model
echo "Training Temporal Fusion Transformer model..."
curl -X POST "http://localhost:8002/api/models/train" -H "Content-Type: application/json" -d '{
    "architecture": "TemporalFusionTransformer",
    "name": "TFT-Base",
    "version": "1.0.0",
    "hyperparameters": {
      "hidden_dim": 64,
      "num_heads": 4,
      "dropout": 0.1,
      "learning_rate": 0.001,
      "batch_size": 64,
      "epochs": 50,
      "lookback_window": 30,
      "forecast_horizon": 5
    },
    "feature_config": {
      "static_features": ["sector", "market_cap"],
      "time_varying_features": ["open", "high", "low", "close", "volume", "ma_5", "ma_20", "rsi_14"]
    },
    "training_dataset_config": {
      "train_test_split": 0.8,
      "lookback_window": 30,
      "forecast_horizon": 5,
      "stocks": "all"
    }
  }'

# Train LSTM model
echo "Training LSTM model..."
curl -X POST "http://localhost:8002/api/models/train" -H "Content-Type: application/json" -d '{
    "architecture": "LSTM",
    "name": "LSTM-Base",
    "version": "1.0.0",
    "hyperparameters": {
      "hidden_dim": 64,
      "num_layers": 2,
      "dropout": 0.2,
      "learning_rate": 0.001,
      "batch_size": 64,
      "epochs": 50,
      "lookback_window": 30,
      "forecast_horizon": 5
    },
    "feature_config": {
      "time_varying_features": ["open", "high", "low", "close", "volume", "ma_5", "ma_20", "rsi_14"]
    },
    "training_dataset_config": {
      "train_test_split": 0.8,
      "lookback_window": 30,
      "forecast_horizon": 5,
      "stocks": "all"
    }
  }'

# Train ARIMA model
echo "Training ARIMA model..."
curl -X POST "http://localhost:8002/api/models/train" -H "Content-Type: application/json" -d '{
    "architecture": "ARIMA",
    "name": "ARIMA-Base",
    "version": "1.0.0",
    "hyperparameters": {
      "p": 5,
      "d": 1,
      "q": 0,
      "forecast_horizon": 5
    },
    "training_dataset_config": {
      "train_test_split": 0.8,
      "lookback_window": 100,
      "forecast_horizon": 5,
      "stocks": "all"
    }
  }'

echo "Model training initiated"
echo "Note: Training will continue in the background and may take some time to complete"

echo "Setup completed!"
echo "The services are available at:"
echo "  - Dashboard: http://localhost:8000"
echo "  - Data Ingestion API: http://localhost:8001"
echo "  - Model Service API: http://localhost:8002"
echo "  - MinIO Console: http://localhost:9001"