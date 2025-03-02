-- Predictions table
CREATE TABLE predictions.stock_predictions (
    id BIGSERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL,
    stock_id INTEGER NOT NULL,
    prediction_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    target_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    predicted_value NUMERIC(19,6) NOT NULL,
    confidence_lower NUMERIC(19,6),
    confidence_upper NUMERIC(19,6),
    features_used JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_model FOREIGN KEY (model_id) REFERENCES model_management.models(id) ON DELETE CASCADE,
    CONSTRAINT fk_stock FOREIGN KEY (stock_id) REFERENCES stock_data.stocks(id) ON DELETE CASCADE
);

-- Create index for fast lookups
CREATE INDEX idx_predictions_model_stock ON predictions.stock_predictions(model_id, stock_id, target_timestamp DESC);
CREATE INDEX idx_predictions_target_date ON predictions.stock_predictions(target_timestamp);

-- Create hypertable for predictions (this will be executed on TimescaleDB instance)
-- SELECT create_hypertable('predictions.stock_predictions', 'prediction_timestamp');

-- Prediction batches table for grouping related predictions
CREATE TABLE predictions.prediction_batches (
    id SERIAL PRIMARY KEY,
    batch_identifier VARCHAR(100) NOT NULL,
    model_id INTEGER NOT NULL,
    prediction_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    config JSONB,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_model FOREIGN KEY (model_id) REFERENCES model_management.models(id) ON DELETE CASCADE
);

-- Create index for prediction batches
CREATE INDEX idx_prediction_batches_identifier ON predictions.prediction_batches(batch_identifier);