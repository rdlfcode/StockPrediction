import React, { useState, useEffect } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { AlertCircle, BarChart4, TrendingUp, List } from 'lucide-react';

import StockSelector from './StockSelector';
import ModelSelector from './ModelSelector';
import ModelComparisonChart from './ModelComparisonChart';
import FeatureImportanceChart from './FeatureImportanceChart';
import ModelMetricsTable from './ModelMetricsTable';
import PredictionsTable from './PredictionsTable';

const Dashboard = () => {
  const [stocks, setStocks] = useState([]);
  const [models, setModels] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [selectedModels, setSelectedModels] = useState([]);
  const [dateRange, setDateRange] = useState({
    from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    to: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000) // 5 days in future
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch stocks
        const stocksResponse = await fetch('/api/stocks');
        if (!stocksResponse.ok) {
          throw new Error('Failed to fetch stocks');
        }
        const stocksData = await stocksResponse.json();
        setStocks(stocksData);
        
        // Fetch models
        const modelsResponse = await fetch('/api/models');
        if (!modelsResponse.ok) {
          throw new Error('Failed to fetch models');
        }
        const modelsData = await modelsResponse.json();
        setModels(modelsData);
        
        // Set defaults
        if (stocksData.length > 0) {
          setSelectedStock(stocksData[0].id);
        }
        
        if (modelsData.length > 0) {
          setSelectedModels([modelsData[0].id]);
        }
        
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  const handleStockChange = (stockId) => {
    setSelectedStock(stockId);
  };
  
  const handleModelChange = (modelIds) => {
    setSelectedModels(modelIds);
  };
  
  const handleDateRangeChange = (range) => {
    setDateRange(range);
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">Loading dashboard data...</div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="max-w-lg p-4 bg-red-100 text-red-800 rounded-lg">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            <div className="font-semibold">Error loading dashboard</div>
          </div>
          <div className="mt-2">{error}</div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Stock Prediction Platform</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-6">
        <div className="md:col-span-6">
          <StockSelector 
            stocks={stocks} 
            selectedStock={selectedStock} 
            onStockChange={handleStockChange} 
          />
        </div>
        <div className="md:col-span-6">
          <ModelSelector 
            models={models} 
            selectedModels={selectedModels} 
            onModelChange={handleModelChange} 
          />
        </div>
      </div>
      
      {selectedStock && selectedModels.length > 0 && (
        <Tabs defaultValue="comparison" className="w-full">
          <TabsList className="mb-4">
            <TabsTrigger value="comparison">
              <TrendingUp className="w-4 h-4 mr-2" />
              Model Comparison
            </TabsTrigger>
            <TabsTrigger value="features">
              <BarChart4 className="w-4 h-4 mr-2" />
              Feature Importance
            </TabsTrigger>
            <TabsTrigger value="metrics">
              <List className="w-4 h-4 mr-2" />
              Performance Metrics
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="comparison" className="space-y-6">
            <ModelComparisonChart 
              stockId={selectedStock} 
              selectedModels={selectedModels} 
              dateRange={dateRange} 
              onDateRangeChange={handleDateRangeChange}
            />
            
            <PredictionsTable 
              stockId={selectedStock} 
              selectedModels={selectedModels}
            />
          </TabsContent>
          
          <TabsContent value="features" className="space-y-6">
            {selectedModels.map(modelId => (
              <Card key={modelId} className="w-full">
                <CardHeader>
                  <CardTitle>
                    Feature Importance: {models.find(m => m.id === modelId)?.name || `Model ${modelId}`}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <FeatureImportanceChart modelId={modelId} />
                </CardContent>
              </Card>
            ))}
          </TabsContent>
          
          <TabsContent value="metrics" className="space-y-6">
            <ModelMetricsTable 
              stockId={selectedStock} 
              selectedModels={selectedModels}
              models={models}
            />
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};

export default Dashboard;