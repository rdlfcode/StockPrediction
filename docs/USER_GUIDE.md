# Stock Prediction Platform - User Guide

This guide provides instructions for using the Stock Prediction Platform to compare different machine learning architectures for stock prediction.

## Table of Contents

1. [Dashboard Overview](#dashboard-overview)
2. [Selecting Stocks](#selecting-stocks)
3. [Comparing Models](#comparing-models)
4. [Viewing Predictions](#viewing-predictions)
5. [Analyzing Feature Importance](#analyzing-feature-importance)
6. [Performance Metrics](#performance-metrics)
7. [Creating New Models](#creating-new-models)
8. [Troubleshooting](#troubleshooting)

## Dashboard Overview

The Stock Prediction Platform dashboard provides a comprehensive interface for:

- Comparing predictions from different machine learning models
- Visualizing historical and predicted stock prices
- Analyzing feature importance for different models
- Viewing performance metrics for model comparison
- Managing stocks and models

The dashboard is accessible at `http://localhost:8000` when running locally, or at your configured domain in production.

## Selecting Stocks

1. Use the **Stock Selector** panel on the left side of the dashboard to choose a stock to analyze.
2. Stocks are grouped by sector for easy navigation.
3. Use the search box to quickly find stocks by ticker symbol or company name.
4. Click on a stock to select it. The selected stock will be highlighted.

## Comparing Models

1. Use the **Model Selector** panel on the right side of the dashboard to choose one or more models to compare.
2. Models are grouped by architecture type (TFT, LSTM, ARIMA, etc.).
3. Check the boxes next to the models you want to include in the comparison.
4. The model status indicator shows whether a model is ready for use:
   - **Ready**: The model is trained and available for predictions
   - **Training**: The model is currently being trained
   - **Created**: The model has been created but not yet trained
   - **Failed**: The model training failed

## Viewing Predictions

1. Once you've selected a stock and one or more models, the **Model Comparison** tab will show a chart with:
   - Historical stock prices (solid line)
   - Model predictions (dotted lines)
   - A vertical line indicating the present day
2. Use the date range selector to adjust the time period for comparison.
3. Hover over the chart for detailed information at specific points in time.
4. The **Future Predictions** table below the chart shows the numerical predictions for future dates.

## Analyzing Feature Importance

1. Switch to the **Feature Importance** tab to see what features each model considers most important.
2. Each selected model will have its own feature importance chart.
3. The chart shows the relative importance of different features as a percentage.
4. This helps you understand what factors each model is using to make predictions.

## Performance Metrics

1. The **Performance Metrics** tab shows quantitative measures of model performance:
   - **MAE (Mean Absolute Error)**: The average absolute difference between predicted and actual values
   - **RMSE (Root Mean Squared Error)**: The square root of the average squared differences
   - **MAPE (Mean Absolute Percentage Error)**: The average percentage difference
   - **Directional Accuracy**: The percentage of times the model correctly predicts the direction of movement
   - **Sharpe Ratio**: A measure of risk-adjusted return if trading based on the model's predictions
2. Use these metrics to compare the performance of different models.
3. Click the **Refresh** button to update the metrics with the latest data.

## Creating New Models

To create and train a new model:

1. Use the Model Service API directly:
curl -X POST http://localhost:8002/api/models/train -H "Content-Type: application/json" -d '{
"architecture": "LSTM",
"name": "My Custom LSTM",
"version": "1.0.0",
"hyperparameters": {
"hidden_dim": 128,
"num_layers": 3,
"dropout": 0.3,
"learning_rate": 0.001,
"batch_size": 64,
"epochs": 100,
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

2. The model will be created and training will start in the background.
3. You can check the status of the model training through the API or the dashboard.
4. Once the model is trained, it will appear in the Model Selector with a "Ready" status.

## Troubleshooting

### Dashboard Issues

- **No data appears in charts**: Ensure you have selected both a stock and at least one model.
- **Models not appearing in selector**: Check if models have been created and trained. See logs for any training errors.
- **Slow dashboard performance**: Try selecting fewer models for comparison or a shorter date range.

### Data Issues

- **Missing stock data**: Check if the data ingestion service is running correctly. You may need to manually trigger data import.
- **No feature data**: Features are calculated automatically. Check data ingestion service logs for errors.

### Model Issues

- **Model training fails**: Check model service logs for specific errors. Common issues include:
- Insufficient data for the chosen lookback window
- GPU memory issues for large models
- Invalid hyperparameter combinations
- **Poor model performance**: Try adjusting the hyperparameters or using different features in the model configuration.

For additional support, check the service logs:
docker-compose logs -f data-ingestion
docker-compose logs -f model-service
docker-compose logs -f dashboard-service