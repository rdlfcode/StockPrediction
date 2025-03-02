-- Model architecture reference table
CREATE TABLE model_management.model_architectures (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_architecture_name UNIQUE (name)
);

-- Insert supported architectures
INSERT INTO model_management.model_architectures (name, type, description)
VALUES
    ('TemporalFusionTransformer', 'deep_learning', 'Temporal Fusion Transformer for Interpretable Multi-horizon Time Series Forecasting'),
    ('VanillaTransformer', 'deep_learning', 'Standard Transformer architecture adapted for time series'),
    ('LSTM', 'deep_learning', 'Long Short-Term Memory recurrent neural network'),
    ('BiLSTM', 'deep_learning', 'Bidirectional LSTM neural network'),
    ('ARIMA', 'statistical', 'AutoRegressive Integrated Moving Average'),
    ('GARCH', 'statistical', 'Generalized Autoregressive Conditional Heteroskedasticity'),
    ('ExponentialSmoothing', 'statistical', 'Exponential smoothing state-space model'),
    ('Prophet', 'statistical', 'Facebook Prophet forecasting procedure'),
    ('LinearRegression', 'statistical', 'Simple linear regression model'),
    ('RandomForest', 'ensemble', 'Random forest regression model'),
    ('XGBoost', 'ensemble', 'XGBoost gradient boosting model'),
    ('EnsembleModel', 'ensemble', 'Weighted ensemble of multiple models');

-- Models table
CREATE TABLE model_management.models (
    id SERIAL PRIMARY KEY,
    architecture_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(20) NOT NULL,
    hyperparameters JSONB,
    feature_config JSONB,
    training_dataset_config JSONB,
    model_path TEXT,
    status VARCHAR(20) DEFAULT 'created',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_architecture FOREIGN KEY (architecture_id) REFERENCES model_management.model_architectures(id),
    CONSTRAINT unique_model_name_version UNIQUE (name, version)
);

-- Create index on model status for filtering
CREATE INDEX idx_models_status ON model_management.models(status);

-- Model training history
CREATE TABLE model_management.training_history (
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running',
    train_loss NUMERIC(10,6),
    validation_loss NUMERIC(10,6),
    metrics JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_model FOREIGN KEY (model_id) REFERENCES model_management.models(id) ON DELETE CASCADE
);

-- Create index on training status
CREATE INDEX idx_training_history_status ON model_management.training_history(status);
CREATE INDEX idx_training_history_model_id ON model_management.training_history(model_id);

-- Feature importance table
CREATE TABLE model_management.feature_importance (
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    importance_score NUMERIC(10,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_model FOREIGN KEY (model_id) REFERENCES model_management.models(id) ON DELETE CASCADE,
    CONSTRAINT unique_model_feature UNIQUE (model_id, feature_name)
);