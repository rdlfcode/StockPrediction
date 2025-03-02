import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Check, Search } from 'lucide-react';

const StockSelector = ({ stocks, selectedStock, onStockChange }) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  // Filter stocks based on search term
  const filteredStocks = stocks.filter(stock => 
    stock.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    stock.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (stock.sector && stock.sector.toLowerCase().includes(searchTerm.toLowerCase()))
  );
  
  // Group stocks by sector
  const stocksBySector = filteredStocks.reduce((acc, stock) => {
    const sector = stock.sector || 'Other';
    if (!acc[sector]) {
      acc[sector] = [];
    }
    acc[sector].push(stock);
    return acc;
  }, {});
  
  // Sort sectors
  const sortedSectors = Object.keys(stocksBySector).sort();
  
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Select Stock</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search stocks..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <div className="h-96 overflow-y-auto border rounded-md">
          {sortedSectors.map(sector => (
            <div key={sector} className="p-2">
              <h3 className="font-medium text-sm text-gray-500 px-2 py-1 bg-gray-50">
                {sector}
              </h3>
              <div className="space-y-1 mt-1">
                {stocksBySector[sector].map(stock => (
                  <Button
                    key={stock.id}
                    variant={selectedStock === stock.id ? "default" : "ghost"}
                    className="w-full justify-start text-left"
                    onClick={() => onStockChange(stock.id)}
                  >
                    <div className="flex items-center">
                      {selectedStock === stock.id && (
                        <Check className="h-4 w-4 mr-2 flex-shrink-0" />
                      )}
                      <div className="truncate">
                        <span className="font-semibold">{stock.ticker}</span>
                        <span className="ml-2 text-sm text-gray-600">{stock.name}</span>
                      </div>
                    </div>
                  </Button>
                ))}
              </div>
            </div>
          ))}
          
          {filteredStocks.length === 0 && (
            <div className="p-4 text-center text-gray-500">
              No stocks found matching "{searchTerm}"
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default StockSelector;