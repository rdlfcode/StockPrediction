import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';

const ModelMetricsTable = ({ stockId, selectedModels, models }) => {
  const [metrics, setMetrics] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const fetchMetrics = async () => {
    try {
      setLoading(true);
      
      const response = await fetch(`/api/predictions/comparison?stock_id=${stockId}&${selectedModels.map(id => `model_ids=${id}`).join('&')}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch metrics data');
      }
      
      const data = await response.json();
      
      if (data.metrics) {
        setMetrics(data.metrics);
      } else {
        setMetrics({});
      }
      
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };
  
  useEffect(() => {
    if (stockId && selectedModels.length > 0) {
      fetchMetrics();
    }
  }, [stockId, selectedModels]);
  
  const getModelName = (modelId) => {
    const model = models.find(m => m.id === parseInt(modelId));
    return model ? `${model.name} v${model.version}` : `Model ${modelId}`;
  };
  
  const handleRefresh = () => {
    fetchMetrics();
  };
  
  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Model Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-32 flex items-center justify-center">
            Loading performance metrics...
          </div>
        </CardContent>
      </Card>
    );
  }
  
  if (error) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Model Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center p-4 text-red-800 bg-red-100 rounded">
            <AlertCircle className="w-5 h-5 mr-2" />
            <span>{error}</span>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  const metricNames = {
    mae: "Mean Absolute Error",
    rmse: "Root Mean Squared Error",
    mape: "Mean Absolute Percentage Error (%)",
    directional_accuracy: "Directional Accuracy (%)",
    sharpe_ratio: "Sharpe Ratio"
  };
  
  const metricFormats = {
    mae: (value) => value.toFixed(3),
    rmse: (value) => value.toFixed(3),
    mape: (value) => value.toFixed(2) + '%',
    directional_accuracy: (value) => value.toFixed(2) + '%',
    sharpe_ratio: (value) => value.toFixed(3)
  };
  
  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Model Performance Metrics</CardTitle>
        <Button variant="outline" size="sm" onClick={handleRefresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </CardHeader>
      <CardContent>
        {Object.keys(metrics).length === 0 ? (
          <div className="h-32 flex items-center justify-center text-gray-500">
            No metrics data available. Generate predictions first.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="p-2 border text-left">Model</th>
                  {Object.keys(metricNames).map(metric => (
                    <th key={metric} className="p-2 border text-right">
                      {metricNames[metric]}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(metrics).map(([modelId, modelMetrics]) => (
                  <tr key={modelId}>
                    <td className="p-2 border font-medium">
                      {getModelName(modelId)}
                    </td>
                    {Object.keys(metricNames).map(metric => (
                      <td key={metric} className="p-2 border text-right">
                        {modelMetrics[metric] !== undefined ? 
                          metricFormats[metric](modelMetrics[metric]) : 
                          'N/A'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ModelMetricsTable;