import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { AlertCircle } from 'lucide-react';

const FeatureImportanceChart = ({ modelId }) => {
  const [featureImportance, setFeatureImportance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchFeatureImportance = async () => {
      try {
        setLoading(true);
        
        const response = await fetch(`/api/models/${modelId}/feature_importance`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch feature importance data');
        }
        
        const data = await response.json();
        
        if (!data.feature_importance) {
          setFeatureImportance([]);
          setLoading(false);
          return;
        }
        
        // Transform data for chart
        const chartData = Object.entries(data.feature_importance)
          .map(([feature, importance]) => ({
            feature,
            importance: parseFloat(importance)
          }))
          .sort((a, b) => b.importance - a.importance);
        
        setFeatureImportance(chartData);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };
    
    if (modelId) {
      fetchFeatureImportance();
    }
  }, [modelId]);
  
  if (loading) {
    return <div className="h-72 flex items-center justify-center">Loading feature importance...</div>;
  }
  
  if (error) {
    return (
      <div className="h-72 flex items-center justify-center">
        <div className="flex items-center p-4 text-red-800 bg-red-100 rounded">
          <AlertCircle className="w-5 h-5 mr-2" />
          <span>{error}</span>
        </div>
      </div>
    );
  }
  
  if (featureImportance.length === 0) {
    return (
      <div className="h-72 flex items-center justify-center text-gray-500">
        No feature importance data available for this model.
      </div>
    );
  }
  
  return (
    <div className="h-96">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={featureImportance}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" domain={[0, Math.max(...featureImportance.map(d => d.importance)) * 1.1]} />
          <YAxis dataKey="feature" type="category" width={90} />
          <Tooltip 
            formatter={(value) => [`${(value * 100).toFixed(2)}%`, 'Importance']}
          />
          <Legend />
          <Bar 
            dataKey="importance" 
            fill="#8884d8" 
            name="Feature Importance"
            label={{
              position: 'right',
              formatter: (value) => `${(value * 100).toFixed(1)}%`,
              fontSize: 12
            }}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default FeatureImportanceChart;