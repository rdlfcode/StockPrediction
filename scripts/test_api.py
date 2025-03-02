#!/usr/bin/env python

import argparse
import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Default service URLs
DEFAULT_DATA_SERVICE_URL = "http://localhost:8001/api"
DEFAULT_MODEL_SERVICE_URL = "http://localhost:8002/api"
DEFAULT_DASHBOARD_SERVICE_URL = "http://localhost:8000/api"

async def test_data_ingestion_api(url: str):
    """Test the data ingestion API."""
    print("=== Testing Data Ingestion API ===")
    
    async with httpx.AsyncClient() as client:
        # Test adding a stock
        print("Testing adding a stock...")
        response = await client.post(
            f"{url}/stocks",
            json={"ticker": "AAPL"}
        )
        
        if response.status_code == 200:
            stock_data = response.json()
            stock_id = stock_data["id"]
            print(f"Successfully added stock AAPL with ID {stock_id}")
        else:
            print(f"Failed to add stock: {response.text}")
            # Try to get the stock if it already exists
            response = await client.get(f"{url}/stocks")
            if response.status_code == 200:
                stocks = response.json()
                for stock in stocks:
                    if stock["ticker"] == "AAPL":
                        stock_id = stock["id"]
                        print(f"Found existing stock AAPL with ID {stock_id}")
                        break
                else:
                    print("Could not find AAPL stock")
                    return
            else:
                print(f"Failed to get stocks: {response.text}")
                return
        
        # Test importing historical data
        print("Testing importing historical data...")
        response = await client.post(
            f"{url}/data/import_historical",
            json={"days": 30},
            params={"stock_id": stock_id}
        )
        
        if response.status_code == 200:
            print(f"Successfully imported historical data: {response.json()}")
        else:
            print(f"Failed to import historical data: {response.text}")
        
        # Test generating features
        print("Testing generating features...")
        response = await client.post(
            f"{url}/features/generate/{stock_id}",
            params={"days": 30}
        )
        
        if response.status_code == 200:
            print(f"Successfully generated features: {response.json()}")
        else:
            print(f"Failed to generate features: {response.text}")
        
        # Test getting latest data
        print("Testing getting latest data...")
        response = await client.get(f"{url}/data/latest/{stock_id}")
        
        if response.status_code == 200:
            print(f"Successfully retrieved latest data: {response.json()}")
        else:
            print(f"Failed to retrieve latest data: {response.text}")
    
    print("Data Ingestion API tests completed")

async def test_model_service_api(url: str):
    """Test the model service API."""
    print("=== Testing Model Service API ===")
    
    async with httpx.AsyncClient() as client:
        # Test creating a model
        print("Testing creating a model...")
        model_config = {
            "architecture": "LSTM",
            "name": "LSTM_Test",
            "version": "1.0.0",
            "hyperparameters": {
                "hidden_dim": 64,
                "num_layers": 2,
                "dropout": 0.2,
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 10,
                "lookback_window": 20,
                "forecast_horizon": 5
            },
            "feature_config": {
                "time_varying_features": ["open", "high", "low", "close", "volume"]
            },
            "training_dataset_config": {
                "train_test_split": 0.8,
                "lookback_window": 20,
                "forecast_horizon": 5,
                "stocks": "all"
            }
        }
        
        response = await client.post(
            f"{url}/models",
            json=model_config
        )
        
        if response.status_code == 200:
            model_data = response.json()
            model_id = model_data["id"]
            print(f"Successfully created model with ID {model_id}")
        else:
            print(f"Failed to create model: {response.text}")
            # Try to get an existing model
            response = await client.get(f"{url}/models")
            if response.status_code == 200:
                models = response.json()
                if models:
                    model_id = models[0]["id"]
                    print(f"Using existing model with ID {model_id}")
                else:
                    print("No models found")
                    return
            else:
                print(f"Failed to get models: {response.text}")
                return
        
        # Test training a model
        print("Testing training a model...")
        response = await client.post(
            f"{url}/models/{model_id}/train"
        )
        
        if response.status_code == 200:
            print(f"Successfully started model training: {response.json()}")
        else:
            print(f"Failed to start model training: {response.text}")
        
        # Wait for training to complete
        print("Waiting for training to complete (10 seconds)...")
        await asyncio.sleep(10)
        
        # Test model status
        print("Testing model status...")
        response = await client.get(f"{url}/models/{model_id}")
        
        if response.status_code == 200:
            print(f"Model status: {response.json()['status']}")
        else:
            print(f"Failed to get model status: {response.text}")
        
        # Test generating predictions
        print("Testing generating predictions...")
        # Get a stock ID
        response = await client.get(f"{url.replace('/api', '')}/api/stocks")
        
        if response.status_code == 200:
            stocks = response.json()
            if stocks:
                stock_id = stocks[0]["id"]
                print(f"Using stock with ID {stock_id}")
                
                # Generate predictions
                response = await client.post(
                    f"{url}/predictions",
                    json={
                        "model_id": model_id,
                        "stock_id": stock_id,
                        "save_to_db": True
                    }
                )
                
                if response.status_code == 200:
                    print(f"Successfully generated predictions: {response.json()}")
                else:
                    print(f"Failed to generate predictions: {response.text}")
            else:
                print("No stocks found")
        else:
            print(f"Failed to get stocks: {response.text}")
    
    print("Model Service API tests completed")

async def test_dashboard_api(url: str):
    """Test the dashboard API."""
    print("=== Testing Dashboard API ===")
    
    async with httpx.AsyncClient() as client:
        # Test getting stocks
        print("Testing getting stocks...")
        response = await client.get(f"{url}/stocks")
        
        if response.status_code == 200:
            stocks = response.json()
            print(f"Successfully retrieved {len(stocks)} stocks")
            if stocks:
                stock_id = stocks[0]["id"]
            else:
                print("No stocks found")
                return
        else:
            print(f"Failed to get stocks: {response.text}")
            return
        
        # Test getting models
        print("Testing getting models...")
        response = await client.get(f"{url}/models")
        
        if response.status_code == 200:
            models = response.json()
            print(f"Successfully retrieved {len(models)} models")
            if models:
                model_id = models[0]["id"]
            else:
                print("No models found")
                return
        else:
            print(f"Failed to get models: {response.text}")
            return
        
        # Test getting prediction comparison
        print("Testing getting prediction comparison...")
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
        end_date = (datetime.now() + timedelta(days=5)).isoformat()
        
        response = await client.get(
            f"{url}/predictions/comparison",
            params={
                "stock_id": stock_id,
                "model_ids": [model_id],
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        if response.status_code == 200:
            print(f"Successfully retrieved prediction comparison")
        else:
            print(f"Failed to get prediction comparison: {response.text}")
        
        # Test getting feature importance
        print("Testing getting feature importance...")
        response = await client.get(f"{url}/models/{model_id}/feature_importance")
        
        if response.status_code == 200:
            print(f"Successfully retrieved feature importance")
        else:
            print(f"Failed to get feature importance: {response.text}")
    
    print("Dashboard API tests completed")

async def main():
    parser = argparse.ArgumentParser(description="Test the Stock Prediction Platform APIs")
    parser.add_argument("--data-url", default=DEFAULT_DATA_SERVICE_URL, help="Data ingestion service URL")
    parser.add_argument("--model-url", default=DEFAULT_MODEL_SERVICE_URL, help="Model service URL")
    parser.add_argument("--dashboard-url", default=DEFAULT_DASHBOARD_SERVICE_URL, help="Dashboard service URL")
    parser.add_argument("--test-data", action="store_true", help="Test data ingestion API")
    parser.add_argument("--test-model", action="store_true", help="Test model service API")
    parser.add_argument("--test-dashboard", action="store_true", help="Test dashboard API")
    parser.add_argument("--test-all", action="store_true", help="Test all APIs")
    
    args = parser.parse_args()
    
    # If no specific tests selected, test all
    if not (args.test_data or args.test_model or args.test_dashboard):
        args.test_all = True
    
    if args.test_all or args.test_data:
        await test_data_ingestion_api(args.data_url)
        print()
    
    if args.test_all or args.test_model:
        await test_model_service_api(args.model_url)
        print()
    
    if args.test_all or args.test_dashboard:
        await test_dashboard_api(args.dashboard_url)

if __name__ == "__main__":
    asyncio.run(main())