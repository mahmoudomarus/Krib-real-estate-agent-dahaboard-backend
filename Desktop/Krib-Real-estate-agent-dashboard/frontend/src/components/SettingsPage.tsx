import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Separator } from './ui/separator'
import { Switch } from './ui/switch'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog'
import { useApp } from '../contexts/AppContext'
import { toast } from 'sonner'

interface UserSettings {
  displayName: string
  email: string
  phoneNumber: string
  notifications: {
    bookings: boolean
    marketing: boolean
    systemUpdates: boolean
  }
  preferences: {
    currency: string
    timezone: string
    language: string
  }
}

export function SettingsPage() {
  const { 
    user, 
    signOut, 
    updateUserProfile, 
    updateUserSettings, 
    changePassword, 
    getUserNotifications, 
    updateUserNotifications 
  } = useApp()
  
  const [isLoading, setIsLoading] = useState(false)
  const [showPasswordDialog, setShowPasswordDialog] = useState(false)
  const [passwordData, setPasswordData] = useState({
    current: '',
    new: '',
    confirm: ''
  })
  const [settings, setSettings] = useState<UserSettings>({
    displayName: user?.name || '',
    email: user?.email || '',
    phoneNumber: (user as any)?.phone || '',
    notifications: {
      bookings: true,
      marketing: false,
      systemUpdates: true
    },
    preferences: {
      currency: 'USD',
      timezone: 'America/New_York',
      language: 'English'
    }
  })
  
  // Load user settings on component mount
  useEffect(() => {
    loadUserSettings()
  }, [user])
  
  const loadUserSettings = async () => {
    if (!user) return
    
    try {
      const notifications = await getUserNotifications()
      setSettings(prev => ({
        ...prev,
        displayName: user.name || '',
        email: user.email || '',
        phoneNumber: (user as any)?.phone || '',
        notifications: notifications.notifications || prev.notifications
      }))
    } catch (error) {
      console.error('Failed to load user settings:', error)
    }
  }

  const handleSaveSettings = async () => {
    setIsLoading(true)
    try {
      // Update profile information
      await updateUserProfile({
        name: settings.displayName,
        phone: settings.phoneNumber
      })
      
      // Update notifications
      await updateUserNotifications(settings.notifications)
      
      // Update preferences (stored in user settings)
      await updateUserSettings({
        notifications: settings.notifications,
        preferences: settings.preferences
      })
      
      toast.success('Settings saved successfully')
    } catch (error: any) {
      console.error('Settings save error:', error)
      toast.error(error.message || 'Failed to save settings')
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleChangePassword = async () => {
    if (passwordData.new !== passwordData.confirm) {
      toast.error('New passwords do not match')
      return
    }
    
    if (passwordData.new.length < 6) {
      toast.error('Password must be at least 6 characters long')
      return
    }
    
    // Check if user is OAuth user (no current password required)
    const isOAuthUser = user?.email && !passwordData.current
    
    try {
      await changePassword(passwordData.current || '', passwordData.new, passwordData.confirm)
      toast.success(isOAuthUser ? 'Password set successfully' : 'Password changed successfully')
      setShowPasswordDialog(false)
      setPasswordData({ current: '', new: '', confirm: '' })
    } catch (error: any) {
      console.error('Password change error:', error)
      toast.error(error.message || 'Failed to change password')
    }
  }
  
  // Check if user is OAuth user (determine if current password is needed)
  const isOAuthUser = user?.email && !user?.app_metadata?.provider === 'email'

  const handleSignOut = async () => {
    try {
      await signOut()
      toast.success('Signed out successfully')
    } catch (error) {
      toast.error('Failed to sign out')
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1>Account Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and preferences
        </p>
      </div>

      <div className="grid gap-6">
        {/* Profile Information */}
        <Card className="krib-card">
          <CardHeader>
            <CardTitle>Profile Information</CardTitle>
            <CardDescription>
              Update your personal information and contact details
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="displayName">Display Name</Label>
                <Input
                  id="displayName"
                  value={settings.displayName}
                  onChange={(e) => setSettings({
                    ...settings,
                    displayName: e.target.value
                  })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  value={settings.email}
                  onChange={(e) => setSettings({
                    ...settings,
                    email: e.target.value
                  })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={settings.phoneNumber}
                  onChange={(e) => setSettings({
                    ...settings,
                    phoneNumber: e.target.value
                  })}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card className="krib-card">
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>
              Choose what notifications you'd like to receive
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Booking Notifications</Label>
                <p className="text-sm text-muted-foreground">
                  Get notified about new bookings, cancellations, and updates
                </p>
              </div>
              <Switch
                checked={settings.notifications.bookings}
                onCheckedChange={(checked) => setSettings({
                  ...settings,
                  notifications: { ...settings.notifications, bookings: checked }
                })}
              />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Marketing Communications</Label>
                <p className="text-sm text-muted-foreground">
                  Receive tips, product updates, and promotional content
                </p>
              </div>
              <Switch
                checked={settings.notifications.marketing}
                onCheckedChange={(checked) => setSettings({
                  ...settings,
                  notifications: { ...settings.notifications, marketing: checked }
                })}
              />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>System Updates</Label>
                <p className="text-sm text-muted-foreground">
                  Get notified about system maintenance and important updates
                </p>
              </div>
              <Switch
                checked={settings.notifications.systemUpdates}
                onCheckedChange={(checked) => setSettings({
                  ...settings,
                  notifications: { ...settings.notifications, systemUpdates: checked }
                })}
              />
            </div>
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card className="krib-card">
          <CardHeader>
            <CardTitle>Preferences</CardTitle>
            <CardDescription>
              Customize your dashboard experience
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="currency">Currency</Label>
                <select
                  id="currency"
                  className="w-full px-3 py-2 border border-input bg-background rounded-md"
                  value={settings.preferences.currency}
                  onChange={(e) => setSettings({
                    ...settings,
                    preferences: { ...settings.preferences, currency: e.target.value }
                  })}
                >
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                  <option value="CAD">CAD (C$)</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="timezone">Timezone</Label>
                <select
                  id="timezone"
                  className="w-full px-3 py-2 border border-input bg-background rounded-md"
                  value={settings.preferences.timezone}
                  onChange={(e) => setSettings({
                    ...settings,
                    preferences: { ...settings.preferences, timezone: e.target.value }
                  })}
                >
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                  <option value="Europe/London">GMT</option>
                  <option value="Europe/Paris">CET</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="language">Language</Label>
                <select
                  id="language"
                  className="w-full px-3 py-2 border border-input bg-background rounded-md"
                  value={settings.preferences.language}
                  onChange={(e) => setSettings({
                    ...settings,
                    preferences: { ...settings.preferences, language: e.target.value }
                  })}
                >
                  <option value="English">English</option>
                  <option value="Spanish">Spanish</option>
                  <option value="French">French</option>
                  <option value="German">German</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Account Actions */}
        <Card className="krib-card">
          <CardHeader>
            <CardTitle>Account Actions</CardTitle>
            <CardDescription>
              Manage your account and security settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-3">
              <Button 
                onClick={handleSaveSettings} 
                disabled={isLoading}
                className="krib-button-primary"
              >
                {isLoading ? 'Saving...' : 'Save Changes'}
              </Button>
              
              <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline">
                    Change Password
                  </Button>
                </DialogTrigger>
                <DialogContent className="krib-card">
                  <DialogHeader>
                    <DialogTitle>{isOAuthUser ? 'Set Password' : 'Change Password'}</DialogTitle>
                    <DialogDescription>
                      {isOAuthUser 
                        ? 'Set a password for your account to enable email/password sign-in.'
                        : 'Enter your current password and choose a new one.'
                      }
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    {!isOAuthUser && (
                      <div className="space-y-2">
                        <Label htmlFor="current-password" className="text-sm font-medium text-gray-700">Current Password</Label>
                        <Input
                          id="current-password"
                          type="password"
                          placeholder="Enter current password"
                          className="h-12 rounded-xl border-gray-200 focus:border-krib-lime focus:ring-2 focus:ring-krib-lime/20"
                          value={passwordData.current}
                          onChange={(e) => setPasswordData(prev => ({ ...prev, current: e.target.value }))}
                        />
                      </div>
                    )}
                    <div className="space-y-2">
                      <Label htmlFor="new-password" className="text-sm font-medium text-gray-700">New Password</Label>
                      <Input
                        id="new-password"
                        type="password"
                        placeholder="Enter new password"
                        className="h-12 rounded-xl border-gray-200 focus:border-krib-lime focus:ring-2 focus:ring-krib-lime/20"
                        value={passwordData.new}
                        onChange={(e) => setPasswordData(prev => ({ ...prev, new: e.target.value }))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="confirm-password" className="text-sm font-medium text-gray-700">Confirm New Password</Label>
                      <Input
                        id="confirm-password"
                        type="password"
                        placeholder="Confirm new password"
                        className="h-12 rounded-xl border-gray-200 focus:border-krib-lime focus:ring-2 focus:ring-krib-lime/20"
                        value={passwordData.confirm}
                        onChange={(e) => setPasswordData(prev => ({ ...prev, confirm: e.target.value }))}
                      />
                    </div>
                    <div className="flex gap-3 pt-4">
                      <Button 
                        onClick={handleChangePassword}
                        className="flex-1 krib-button-primary"
                        disabled={
                          (!isOAuthUser && !passwordData.current) || 
                          !passwordData.new || 
                          !passwordData.confirm
                        }
                      >
                        {isOAuthUser ? 'Set Password' : 'Change Password'}
                      </Button>
                      <Button 
                        variant="outline" 
                        onClick={() => setShowPasswordDialog(false)}
                        className="flex-1"
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
              
              <Button variant="destructive" onClick={handleSignOut}>
                Sign Out
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}