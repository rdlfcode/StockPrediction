import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { DateRangePicker } from '@/components/ui/date-range-picker';
import { AlertCircle, Trending, TrendingDown, TrendingUp } from 'lucide-react';

const MODEL_COLORS = {
  'TemporalFusionTransformer': '#8884d8',
  'VanillaTransformer': '#82ca9d',
  'LSTM': '#ffc658',
  'ARIMA': '#ff8042',
  'GARCH': '#0088fe',
  'RandomForest': '#00C49F',
  'XGBoost': '#FFBB28',
  'EnsembleModel': '#FF8042',
};

const ModelComparisonChart = ({ stockId, selectedModels, dateRange }) => {
  const [predictionData, setPredictionData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('price');
  const [metrics, setMetrics] = useState({});

  useEffect(() => {
    if (!stockId || selectedModels.length === 0) {
      return;
    }

    setLoading(true);
    
    // Fetch prediction data
    const fetchPredictionData = async () => {
      try {
        const queryParams = new URLSearchParams({
          stock_id: stockId,
          start_date: dateRange.from.toISOString(),
          end_date: dateRange.to.toISOString(),
        });
        
        selectedModels.forEach(modelId => {
          queryParams.append('model_ids', modelId);
        });
        
        const response = await fetch(`/api/predictions/comparison?${queryParams.toString()}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch prediction data');
        }
        
        const data = await response.json();
        setPredictionData(data.predictions);
        setMetrics(data.metrics || {});
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };
    
    fetchPredictionData();
  }, [stockId, selectedModels, dateRange]);

  const renderMetricsTable = () => {
    if (!metrics || Object.keys(metrics).length === 0) {
      return <div>No metrics data available</div>;
    }

    return (
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="p-2 border text-left">Model</th>
              <th className="p-2 border text-right">MAE</th>
              <th className="p-2 border text-right">RMSE</th>
              <th className="p-2 border text-right">MAPE (%)</th>
              <th className="p-2 border text-right">Dir. Acc. (%)</th>
              <th className="p-2 border text-right">Sharpe Ratio</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(metrics).map(([modelName, modelMetrics]) => (
              <tr key={modelName}>
                <td className="p-2 border font-medium">{modelName}</td>
                <td className="p-2 border text-right">{modelMetrics.mae.toFixed(3)}</td>
                <td className="p-2 border text-right">{modelMetrics.rmse.toFixed(3)}</td>
                <td className="p-2 border text-right">{modelMetrics.mape.toFixed(2)}</td>
                <td className="p-2 border text-right">{modelMetrics.directional_accuracy.toFixed(2)}</td>
                <td className="p-2 border text-right">{modelMetrics.sharpe_ratio.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  if (loading) {
    return <div>Loading prediction data...</div>;
  }

  if (error) {
    return (
      <div className="flex items-center p-4 text-red-800 bg-red-100 rounded">
        <AlertCircle className="w-5 h-5 mr-2" />
        <span>{error}</span>
      </div>
    );
  }

  if (predictionData.length === 0) {
    return <div>No prediction data available for the selected criteria</div>;
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Model Comparison</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="price" onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="price">Price Predictions</TabsTrigger>
            <TabsTrigger value="metrics">Performance Metrics</TabsTrigger>
          </TabsList>
          
          <TabsContent value="price" className="pt-4">
            <ResponsiveContainer width="100%" height={400}>
              <LineChart
                data={predictionData}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(date) => new Date(date).toLocaleDateString()}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(date) => new Date(date).toLocaleDateString()}
                  formatter={(value, name) => [
                    `$${value.toFixed(2)}`, 
                    name === 'actual' ? 'Actual Price' : `${name} Prediction`
                  ]}
                />
                <Legend />
                <ReferenceLine x={new Date().toISOString()} 
                  stroke="#666" 
                  strokeDasharray="3 3"
                  label="Present" 
                />
                
                {/* Actual price */}
                <Line 
                  type="monotone" 
                  dataKey="actual" 
                  stroke="#333" 
                  strokeWidth={2}
                  dot={false}
                  name="actual"
                />
                
                {/* Model predictions */}
                {selectedModels.map(model => (
                  <Line 
                    key={model}
                    type="monotone" 
                    dataKey={`predictions.${model}`}
                    stroke={MODEL_COLORS[model] || '#999'}
                    strokeWidth={1.5}
                    dot={{ r: 3 }}
                    name={model}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </TabsContent>
          
          <TabsContent value="metrics" className="pt-4">
            {renderMetricsTable()}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default ModelComparisonChart;