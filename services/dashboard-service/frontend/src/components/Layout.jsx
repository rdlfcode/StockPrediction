import React, { useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { 
  BarChart, 
  LucideSettings,
  Home,
  Users
} from 'lucide-react';

import Dashboard from './Dashboard';
import SettingsManager from './SettingsManager';

const Layout = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="h-full w-16 md:w-64 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold hidden md:block">Stock Prediction</h1>
          <div className="md:hidden flex justify-center">
            <BarChart className="h-6 w-6" />
          </div>
        </div>
        
        <nav className="flex-1 p-2">
          <ul className="space-y-2">
            <li>
              <Button
                variant={activeTab === 'dashboard' ? 'default' : 'ghost'}
                className="w-full justify-start"
                onClick={() => setActiveTab('dashboard')}
              >
                <Home className="h-5 w-5 mr-2" />
                <span className="hidden md:inline">Dashboard</span>
              </Button>
            </li>
            {/* Additional navigation items would go here */}
            <li>
              <Button
                variant={activeTab === 'settings' ? 'default' : 'ghost'}
                className="w-full justify-start"
                onClick={() => setActiveTab('settings')}
              >
                <LucideSettings className="h-5 w-5 mr-2" />
                <span className="hidden md:inline">Settings</span>
              </Button>
            </li>
          </ul>
        </nav>
      </div>
      
      {/* Main content */}
      <div className="flex-1 overflow-auto p-4 md:p-6">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'settings' && <SettingsManager />}
      </div>
    </div>
  );
};

export default Layout;