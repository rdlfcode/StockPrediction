import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';

const PredictionsTable = ({ stockId, selectedModels }) => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const fetchPredictions = async () => {
    try {
      setLoading(true);
      
      // Only get future predictions
      const today = new Date();
      const startDate = today.toISOString().split('T')[0];
      
      const response = await fetch(
        `/api/predictions/comparison?stock_id=${stockId}&${selectedModels.map(id => `model_ids=${id}`).join('&')}&start_date=${startDate}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch prediction data');
      }
      
      const data = await response.json();
      
      if (data.comparison_data) {
        // Filter to only include future predictions
        const futurePredictions = data.comparison_data.filter(d => 
          new Date(d.date) >= today && Object.keys(d.predictions).length > 0
        );
        
        // Sort by date
        futurePredictions.sort((a, b) => new Date(a.date) - new Date(b.date));
        
        setPredictions(futurePredictions);
      } else {
        setPredictions([]);
      }
      
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };
  
  useEffect(() => {
    if (stockId && selectedModels.length > 0) {
      fetchPredictions();
    }
  }, [stockId, selectedModels]);
  
  const handleRefresh = () => {
    fetchPredictions();
  };
  
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };
  
  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Future Predictions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-32 flex items-center justify-center">
            Loading predictions...
          </div>
        </CardContent>
      </Card>
    );
  }
  
  if (error) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Future Predictions</CardTitle>
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
  
  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Future Predictions</CardTitle>
        <Button variant="outline" size="sm" onClick={handleRefresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </CardHeader>
      <CardContent>
        {predictions.length === 0 ? (
          <div className="h-32 flex items-center justify-center text-gray-500">
            No future predictions available.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="p-2 border text-left">Date</th>
                  {selectedModels.map(modelId => (
                    <th key={modelId} className="p-2 border text-right">
                      Model {modelId}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {predictions.map((prediction) => (
                  <tr key={prediction.date}>
                    <td className="p-2 border font-medium">
                      {formatDate(prediction.date)}
                    </td>
                    {selectedModels.map(modelId => (
                      <td key={modelId} className="p-2 border text-right">
                        {prediction.predictions[modelId] !== undefined ? 
                          `$${prediction.predictions[modelId].toFixed(2)}` : 
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

export default PredictionsTable;