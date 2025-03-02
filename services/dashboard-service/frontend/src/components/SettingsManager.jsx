import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent,
  CardFooter 
} from '@/components/ui/card';
import { 
  Tabs, 
  TabsList, 
  TabsTrigger, 
  TabsContent 
} from '@/components/ui/tabs';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { 
  Form, 
  FormField, 
  FormItem, 
  FormLabel, 
  FormControl, 
  FormDescription 
} from '@/components/ui/form';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { 
  AlertDialog, 
  AlertDialogAction, 
  AlertDialogCancel, 
  AlertDialogContent, 
  AlertDialogDescription, 
  AlertDialogFooter, 
  AlertDialogHeader, 
  AlertDialogTitle, 
  AlertDialogTrigger 
} from '@/components/ui/alert-dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { CheckIcon, PlusCircleIcon, Trash2Icon, SaveIcon } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { toast } from '@/components/ui/use-toast';

const SettingsManager = () => {
  const [profiles, setProfiles] = useState([]);
  const [activeProfile, setActiveProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingProfile, setEditingProfile] = useState(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [profilesToDelete, setProfilesToDelete] = useState(null);
  
  const newProfileForm = useForm({
    defaultValues: {
      name: '',
      is_active: true
    }
  });
  
  const settingsForm = useForm();
  
  // Fetch profiles on component mount
  useEffect(() => {
    fetchProfiles();
  }, []);
  
  // Fetch settings profiles from API
  const fetchProfiles = async () => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/settings/profiles');
      
      if (!response.ok) {
        throw new Error('Failed to fetch settings profiles');
      }
      
      const data = await response.json();
      setProfiles(data);
      
      // Find the active profile
      const active = data.find(profile => profile.is_active);
      
      if (active) {
        setActiveProfile(active);
        settingsForm.reset(active.settings);
      }
      
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching profiles:', error);
      toast({
        title: 'Error',
        description: 'Failed to load settings profiles',
        variant: 'destructive'
      });
      setIsLoading(false);
    }
  };
  
  // Create a new profile
  const createProfile = async (data) => {
    try {
      // Get current settings from form
      const settings = settingsForm.getValues();
      
      const response = await fetch('/api/settings/profiles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: data.name,
          is_active: data.is_active,
          settings: settings
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to create profile');
      }
      
      // Refresh profiles
      await fetchProfiles();
      
      setIsCreating(false);
      newProfileForm.reset();
      
      toast({
        title: 'Success',
        description: `Profile "${data.name}" created successfully`,
      });
    } catch (error) {
      console.error('Error creating profile:', error);
      toast({
        title: 'Error',
        description: 'Failed to create profile',
        variant: 'destructive'
      });
    }
  };
  
  // Update profile settings
  const updateProfileSettings = async () => {
    if (!activeProfile) return;
    
    try {
      const settings = settingsForm.getValues();
      
      const response = await fetch(`/api/settings/profiles/${activeProfile.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          settings: settings
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to update profile settings');
      }
      
      // Refresh profiles
      await fetchProfiles();
      
      toast({
        title: 'Success',
        description: 'Settings updated successfully',
      });
    } catch (error) {
      console.error('Error updating settings:', error);
      toast({
        title: 'Error',
        description: 'Failed to update settings',
        variant: 'destructive'
      });
    }
  };
  
  // Switch active profile
  const switchProfile = async (profileId) => {
    try {
      const profile = profiles.find(p => p.id === parseInt(profileId));
      
      if (!profile) return;
      
      if (profile.is_active) return;
      
      const response = await fetch(`/api/settings/profiles/${profile.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          is_active: true
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to switch profile');
      }
      
      // Refresh profiles
      await fetchProfiles();
      
      toast({
        title: 'Profile Switched',
        description: `Now using "${profile.name}" profile`,
      });
    } catch (error) {
      console.error('Error switching profile:', error);
      toast({
        title: 'Error',
        description: 'Failed to switch profile',
        variant: 'destructive'
      });
    }
  };
  
  // Delete profile
  const deleteProfile = async () => {
    if (!profilesToDelete) return;
    
    try {
      const response = await fetch(`/api/settings/profiles/${profilesToDelete.id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete profile');
      }
      
      // Refresh profiles
      await fetchProfiles();
      
      setShowDeleteDialog(false);
      setProfilesToDelete(null);
      
      toast({
        title: 'Success',
        description: `Profile "${profilesToDelete.name}" deleted successfully`,
      });
    } catch (error) {
      console.error('Error deleting profile:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete profile',
        variant: 'destructive'
      });
    }
  };
  
  // Handler for profile selection
  const handleProfileSelect = (profileId) => {
    switchProfile(profileId);
  };
  
  // Handler for profile delete button click
  const handleDeleteClick = (profile) => {
    setProfilesToDelete(profile);
    setShowDeleteDialog(true);
  };
  
  if (isLoading) {
    return <div>Loading settings...</div>;
  }
  
  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle>Settings</CardTitle>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Profile:</span>
            <Select 
              value={activeProfile?.id.toString()} 
              onValueChange={handleProfileSelect}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue>
                  {activeProfile ? (
                    <div className="flex items-center">
                      <span>{activeProfile.name}</span>
                      <Badge variant="outline" className="ml-2 px-1 py-0">
                        Active
                      </Badge>
                    </div>
                  ) : (
                    "Select a profile"
                  )}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {profiles.map((profile) => (
                  <SelectItem key={profile.id} value={profile.id.toString()}>
                    <div className="flex items-center">
                      <span>{profile.name}</span>
                      {profile.is_active && (
                        <CheckIcon className="ml-2 h-4 w-4 text-green-500" />
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <Dialog open={isCreating} onOpenChange={setIsCreating}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <PlusCircleIcon className="h-4 w-4 mr-2" />
                New Profile
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Settings Profile</DialogTitle>
                <DialogDescription>
                  Create a new profile with the current settings.
                </DialogDescription>
              </DialogHeader>
              
              <form onSubmit={newProfileForm.handleSubmit(createProfile)}>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <label htmlFor="name" className="text-sm font-medium">
                      Profile Name
                    </label>
                    <Input
                      id="name"
                      placeholder="My Profile"
                      {...newProfileForm.register("name", { required: true })}
                    />
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="is_active"
                      checked={newProfileForm.watch("is_active")}
                      onCheckedChange={(checked) => newProfileForm.setValue("is_active", checked)}
                    />
                    <label htmlFor="is_active" className="text-sm font-medium">
                      Set as active profile
                    </label>
                  </div>
                </div>
                
                <DialogFooter>
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => setIsCreating(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">Create Profile</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
          
          {activeProfile && (
            <AlertDialog
              open={showDeleteDialog}
              onOpenChange={setShowDeleteDialog}
            >
              <AlertDialogTrigger asChild>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleDeleteClick(activeProfile)}
                  disabled={profiles.length <= 1}
                >
                  <Trash2Icon className="h-4 w-4 mr-2" />
                  Delete
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Profile</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to delete the profile "{profilesToDelete?.name}"?
                    This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={deleteProfile}>
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}
        </div>
      </CardHeader>
      
      <Tabs defaultValue="data" className="w-full">
        <CardContent className="pt-6">
          <TabsList className="mb-6">
            <TabsTrigger value="data">Data Settings</TabsTrigger>
            <TabsTrigger value="models">Model Settings</TabsTrigger>
            <TabsTrigger value="ui">UI Settings</TabsTrigger>
            <TabsTrigger value="alerts">Alert Settings</TabsTrigger>
          </TabsList>
          
          <Form {...settingsForm}>
            <form onSubmit={(e) => e.preventDefault()}>
              <TabsContent value="data" className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <FormField
                    control={settingsForm.control}
                    name="data_fetch_interval_minutes"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Data Refresh Interval (minutes)</FormLabel>
                        <FormControl>
                          <div className="flex items-center space-x-4">
                            <Slider
                              min={5}
                              max={60}
                              step={5}
                              value={[field.value]}
                              onValueChange={(value) => field.onChange(value[0])}
                              className="flex-grow"
                            />
                            <span className="w-12 text-right">{field.value} min</span>
                          </div>
                        </FormControl>
                        <FormDescription>
                          How frequently to fetch new data from providers
                        </FormDescription>
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={settingsForm.control}
                    name="historical_data_days"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Historical Data Period (days)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min={30}
                            max={1825}
                            {...field}
                            onChange={(e) => field.onChange(parseInt(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Days of historical data to maintain (max: 5 years/1825 days)
                        </FormDescription>
                      </FormItem>
                    )}
                  />
                  
                  {/* Additional data settings would go here */}
                </div>
              </TabsContent>
              
              <TabsContent value="models" className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <FormField
                    control={settingsForm.control}
                    name="default_prediction_horizon"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Prediction Horizon (days)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min={1}
                            max={30}
                            {...field}
                            onChange={(e) => field.onChange(parseInt(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Number of days to forecast into the future
                        </FormDescription>
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={settingsForm.control}
                    name="default_lookback_window"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Lookback Window (days)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min={10}
                            max={200}
                            {...field}
                            onChange={(e) => field.onChange(parseInt(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Number of days of historical data used for predictions
                        </FormDescription>
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={settingsForm.control}
                    name="default_batch_size"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Training Batch Size</FormLabel>
                        <FormControl>
                          <Select
                            value={field.value.toString()}
                            onValueChange={(value) => field.onChange(parseInt(value))}
                          >
                            <SelectTrigger>
                              <SelectValue>{field.value}</SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="16">16</SelectItem>
                              <SelectItem value="32">32</SelectItem>
                              <SelectItem value="64">64</SelectItem>
                              <SelectItem value="128">128</SelectItem>
                            </SelectContent>
                          </Select>
                        </FormControl>
                        <FormDescription>
                          Batch size for model training (larger values use more memory)
                        </FormDescription>
                      </FormItem>
                    )}
                  />
                  
                  {/* Additional model settings would go here */}
                </div>
              </TabsContent>
              
              <TabsContent value="ui" className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <FormField
                    control={settingsForm.control}
                    name="chart_theme"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Chart Theme</FormLabel>
                        <FormControl>
                          <Select
                            value={field.value}
                            onValueChange={(value) => field.onChange(value)}
                          >
                            <SelectTrigger>
                              <SelectValue>{field.value}</SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="light">Light</SelectItem>
                              <SelectItem value="dark">Dark</SelectItem>
                            </SelectContent>
                          </Select>
                        </FormControl>
                        <FormDescription>
                          Color theme for charts and visualizations
                        </FormDescription>
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={settingsForm.control}
                    name="date_format"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Date Format</FormLabel>
                        <FormControl>
                          <Select
                            value={field.value}
                            onValueChange={(value) => field.onChange(value)}
                          >
                            <SelectTrigger>
                              <SelectValue>{field.value}</SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                              <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                              <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                            </SelectContent>
                          </Select>
                        </FormControl>
                        <FormDescription>
                          Format for displaying dates throughout the application
                        </FormDescription>
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={settingsForm.control}
                    name="default_page_size"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Items Per Page</FormLabel>
                        <FormControl>
                          <Select
                            value={field.value.toString()}
                            onValueChange={(value) => field.onChange(parseInt(value))}
                          >
                            <SelectTrigger>
                              <SelectValue>{field.value}</SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="10">10</SelectItem>
                              <SelectItem value="20">20</SelectItem>
                              <SelectItem value="50">50</SelectItem>
                              <SelectItem value="100">100</SelectItem>
                            </SelectContent>
                          </Select>
                        </FormControl>
                        <FormDescription>
                          Number of items to display per page in tables and lists
                        </FormDescription>
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={settingsForm.control}
                    name="auto_refresh_interval"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Dashboard Refresh Interval (seconds)</FormLabel>
                        <FormControl>
                          <div className="flex items-center space-x-4">
                            <Slider
                              min={0}
                              max={300}
                              step={30}
                              value={[field.value]}
                              onValueChange={(value) => field.onChange(value[0])}
                              className="flex-grow"
                            />
                            <span className="w-20 text-right">
                              {field.value === 0 ? "Off" : `${field.value}s`}
                            </span>
                          </div>
                        </FormControl>
                        <FormDescription>
                          How frequently the dashboard automatically refreshes (0 = off)
                        </FormDescription>
                      </FormItem>
                    )}
                  />
                  
                  {/* Additional UI settings would go here */}
                </div>
              </TabsContent>
              
              <TabsContent value="alerts" className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <FormField
                    control={settingsForm.control}
                    name="enable_price_alerts"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                        <div className="space-y-0.5">
                          <FormLabel className="text-base">Price Movement Alerts</FormLabel>
                          <FormDescription>
                            Receive alerts when stock prices move significantly
                          </FormDescription>
                        </div>
                        <FormControl>
                          <Switch
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={settingsForm.control}
                    name="price_alert_threshold"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Price Alert Threshold (%)</FormLabel>
                        <FormControl>
                          <div className="flex items-center space-x-4">
                            <Slider
                              min={1}
                              max={20}
                              step={0.5}
                              value={[field.value]}
                              onValueChange={(value) => field.onChange(value[0])}
                              disabled={!settingsForm.watch("enable_price_alerts")}
                              className="flex-grow"
                            />
                            <span className="w-16 text-right">{field.value}%</span>
                          </div>
                        </FormControl>
                        <FormDescription>
                          Minimum price movement to trigger an alert
                        </FormDescription>
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={settingsForm.control}
                    name="enable_prediction_alerts"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                        <div className="space-y-0.5">
                          <FormLabel className="text-base">Prediction Accuracy Alerts</FormLabel>
                          <FormDescription>
                            Receive alerts when prediction accuracy diverges from actual prices
                          </FormDescription>
                        </div>
                        <FormControl>
                          <Switch
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={settingsForm.control}
                    name="prediction_alert_threshold"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Prediction Alert Threshold (%)</FormLabel>
                        <FormControl>
                          <div className="flex items-center space-x-4">
                            <Slider
                              min={5}
                              max={30}
                              step={1}
                              value={[field.value]}
                              onValueChange={(value) => field.onChange(value[0])}
                              disabled={!settingsForm.watch("enable_prediction_alerts")}
                              className="flex-grow"
                            />
                            <span className="w-16 text-right">{field.value}%</span>
                          </div>
                        </FormControl>
                        <FormDescription>
                          Minimum divergence between prediction and actual price to trigger an alert
                        </FormDescription>
                      </FormItem>
                    )}
                  />
                  
                  {/* Additional alert settings would go here */}
                </div>
              </TabsContent>
            </form>
          </Form>
        </CardContent>
      </Tabs>
      
      <CardFooter className="flex justify-end">
        <Button onClick={updateProfileSettings} className="min-w-[120px]">
          <SaveIcon className="h-4 w-4 mr-2" />
          Save Settings
        </Button>
      </CardFooter>
    </Card>
  );
};

export default SettingsManager;