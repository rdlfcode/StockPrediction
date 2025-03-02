import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';

const ModelSelector = ({ models, selectedModels, onModelChange }) => {
  const handleModelToggle = (modelId) => {
    if (selectedModels.includes(modelId)) {
      onModelChange(selectedModels.filter(id => id !== modelId));
    } else {
      onModelChange([...selectedModels, modelId]);
    }
  };
  
  // Group models by architecture
  const modelsByArchitecture = models.reduce((acc, model) => {
    // Find architecture name
    const architecture = model.architecture_id; // This would need to be mapped to actual names
    
    if (!acc[architecture]) {
      acc[architecture] = [];
    }
    acc[architecture].push(model);
    return acc;
  }, {});
  
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Select Models to Compare</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-96 overflow-y-auto border rounded-md p-2 space-y-4">
          {Object.entries(modelsByArchitecture).map(([architecture, architectureModels]) => (
            <div key={architecture} className="space-y-2">
              <h3 className="font-medium text-sm text-gray-500 px-2 py-1 bg-gray-50">
                {architecture}
              </h3>
              <div className="space-y-2">
                {architectureModels.map(model => (
                  <div key={model.id} className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded-md">
                    <Checkbox
                      id={`model-${model.id}`}
                      checked={selectedModels.includes(model.id)}
                      onCheckedChange={() => handleModelToggle(model.id)}
                    />
                    <div className="flex flex-col">
                      <Label htmlFor={`model-${model.id}`} className="font-medium cursor-pointer">
                        {model.name} <span className="text-xs text-gray-500">v{model.version}</span>
                      </Label>
                      <div className="flex items-center mt-1 space-x-2">
                        <Badge variant={model.status === 'ready' ? 'success' : model.status === 'training' ? 'warning' : 'secondary'}>
                          {model.status}
                        </Badge>
                        {model.hyperparameters && (
                          <span className="text-xs text-gray-500">
                            {Object.entries(model.hyperparameters)
                              .map(([key, value]) => `${key}: ${value}`)
                              .join(', ')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
          
          {models.length === 0 && (
            <div className="p-4 text-center text-gray-500">
              No models available. Create a model to get started.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ModelSelector;