import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { supabase } from '../utils/supabase/client'

// Environment configuration - FORCE HTTPS in production
const PRODUCTION_API_URL = 'https://krib-host-dahsboard-backend.onrender.com/api'
const DEVELOPMENT_API_URL = import.meta.env.VITE_API_URL || PRODUCTION_API_URL

// Always use HTTPS in production (Vercel), allow override only in development
const API_BASE_URL = window.location.protocol === 'https:' ? PRODUCTION_API_URL : DEVELOPMENT_API_URL

// Extra safety: ensure HTTPS is used regardless
const SECURE_API_URL = API_BASE_URL.replace('http://', 'https://')

// Debug logging for API URL
console.log('🔒 API Configuration [FORCE UPDATE v2]:', {
  protocol: window.location.protocol,
  hostname: window.location.hostname,
  isDevelopment: window.location.hostname === 'localhost',
  original: API_BASE_URL,
  final: SECURE_API_URL,
  environment: import.meta.env.VITE_API_URL,
  timestamp: new Date().toISOString()
})

// EMERGENCY: Log every API call to debug
console.log('🚨 SECURE_API_URL being used for all calls:', SECURE_API_URL)

interface User {
  id: string
  email: string
  name: string
  phone?: string
  avatar_url?: string
  settings?: {
    notifications?: {
      bookings?: boolean
      marketing?: boolean
      system_updates?: boolean
    }
    preferences?: {
      currency?: string
      timezone?: string
      language?: string
    }
  }
  total_revenue?: number
  created_at?: string
}

interface Property {
  id: string
  title: string
  description?: string
  address: string
  city: string
  state: string
  country: string
  property_type: string
  bedrooms: number
  bathrooms: number
  max_guests: number
  price_per_night: number
  amenities: string[]
  images: string[]
  status: 'draft' | 'active' | 'inactive' | 'suspended'
  rating?: number
  review_count?: number
  booking_count?: number
  total_revenue?: number
  views_count?: number
  featured?: boolean
  created_at: string
  updated_at: string
}

interface Booking {
  id: string
  property_id: string
  property_title?: string
  property_city?: string
  property_state?: string
  guest_name: string
  guest_email: string
  guest_phone?: string
  check_in: string
  check_out: string
  nights: number
  guests: number
  total_amount: number
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed' | 'no_show'
  payment_status: 'pending' | 'paid' | 'refunded' | 'partially_refunded'
  special_requests?: string
  booking_source?: string
  created_at: string
}

interface Analytics {
  total_properties: number
  total_bookings: number
  total_revenue: number
  occupancy_rate: number
  monthly_revenue: Array<{
    month_year: string
    revenue: number
    bookings: number
  }>
  property_performance: Array<{
    property_id: string
    property_title: string
    total_revenue: number
    booking_count: number
    avg_rating: number
    review_count: number
    occupancy_rate: number
  }>
}

interface AppContextType {
  // Auth state
  user: User | null
  isLoading: boolean
  
  // Data state
  properties: Property[]
  bookings: Booking[]
  analytics: Analytics | null
  
  // Auth methods
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, name: string) => Promise<void>
  signInWithGoogle: () => Promise<void>
  signOut: () => Promise<void>
  
  // Property methods
  createProperty: (propertyData: Partial<Property>) => Promise<Property>
  updateProperty: (id: string, propertyData: Partial<Property>) => Promise<Property>
  deleteProperty: (id: string) => Promise<void>
  loadProperties: () => Promise<void>
  generateAIDescription: (propertyData: Partial<Property>) => Promise<string>
  
  // Booking methods
  loadBookings: () => Promise<void>
  updateBooking: (id: string, bookingData: Partial<Booking>) => Promise<Booking>
  
  // Analytics methods
  getAnalytics: () => Promise<any>
  
  // Financial methods
  getFinancialSummary: (period?: string) => Promise<any>
  getBankAccounts: () => Promise<any>
  addBankAccount: (accountData: any) => Promise<any>
  requestPayout: (amount: number) => Promise<any>
  getTransactions: (limit?: number) => Promise<any>
  updatePayoutSettings: (settings: any) => Promise<any>
  
  // Settings methods
  getUserProfile: () => Promise<User>
  updateUserProfile: (updates: Partial<User>) => Promise<User>
  updateUserSettings: (settings: any) => Promise<void>
  changePassword: (currentPassword: string, newPassword: string, confirmPassword: string) => Promise<void>
  getUserNotifications: () => Promise<any>
  updateUserNotifications: (notifications: any) => Promise<void>
  
  // UAE Location methods
  getUAEEmirates: () => Promise<any>
  getEmirateAreas: (emirate: string) => Promise<string[]>
  getPopularLocations: () => Promise<string[]>
  searchLocations: (query: string) => Promise<any>
  validateLocation: (emirate: string, area?: string) => Promise<any>
  getUAEAmenities: () => Promise<string[]>
  getUAEPropertyTypes: () => Promise<any>
}

const AppContext = createContext<AppContextType | null>(null)

// API utility functions
class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'APIError'
  }
}

async function makeAPIRequest(endpoint: string, options: RequestInit = {}) {
  // Get the current Supabase session token
  const { data: { session } } = await supabase.auth.getSession()
  const token = session?.access_token
  
  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  }

  const fullUrl = `${SECURE_API_URL}${endpoint}`
  console.log('🔥 MAKING API CALL TO:', fullUrl)
  const response = await fetch(fullUrl, config)
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: 'Unknown error' }))
    throw new APIError(response.status, errorData.message || `HTTP ${response.status}`)
  }

  return response.json()
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [properties, setProperties] = useState<Property[]>([])
  const [bookings, setBookings] = useState<Booking[]>([])
  const [analytics, setAnalytics] = useState<Analytics | null>(null)

  // Initialize auth state
  useEffect(() => {
    initializeAuth()
  }, [])

  async function initializeAuth() {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      
      if (session?.access_token) {
        localStorage.setItem('auth_token', session.access_token)
        await getCurrentUser()
      }
    } catch (error) {
      console.error('Auth initialization error:', error)
    } finally {
      setIsLoading(false)
    }

    // Listen for auth changes
    supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session?.access_token) {
        localStorage.setItem('auth_token', session.access_token)
        await getCurrentUser()
      } else if (event === 'SIGNED_OUT') {
        localStorage.removeItem('auth_token')
        setUser(null)
        setProperties([])
        setBookings([])
        setAnalytics(null)
      }
    })
  }

  async function getCurrentUser() {
    try {
      // Get user data from Supabase session instead of backend
      const { data: { session } } = await supabase.auth.getSession()
      
      if (session?.user) {
        setUser({
          id: session.user.id,
          email: session.user.email || '',
          name: session.user.user_metadata?.full_name || session.user.email || 'User',
          created_at: session.user.created_at
        })
        
        // Load user data from Supabase directly instead of backend
        // TODO: Replace these with direct Supabase queries
        console.log('User authenticated with Supabase:', session.user)
      } else {
        console.log('No Supabase session found')
      }
    } catch (error) {
      console.error('Get current user error:', error)
      localStorage.removeItem('auth_token')
    }
  }

  // Auth methods
  async function signIn(email: string, password: string) {
    try {
      setIsLoading(true)
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      
      if (error) throw error
      
      if (data.session?.access_token) {
        localStorage.setItem('auth_token', data.session.access_token)
        await getCurrentUser()
      }
    } catch (error: any) {
      throw new Error(error.message || 'Failed to sign in')
    } finally {
      setIsLoading(false)
    }
  }

  async function signUp(email: string, password: string, name: string) {
    try {
      setIsLoading(true)
      
      // Sign up with Supabase
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { name }
        }
      })
      
      if (error) throw error
      
      if (data.session?.access_token) {
        localStorage.setItem('auth_token', data.session.access_token)
        
        // Create user profile in our backend
        await makeAPIRequest('/auth/signup', {
          method: 'POST',
          body: JSON.stringify({ name, email })
        })
        
        await getCurrentUser()
      }
    } catch (error: any) {
      throw new Error(error.message || 'Failed to sign up')
    } finally {
      setIsLoading(false)
    }
  }

  async function signInWithGoogle() {
    try {
      console.log('Starting Google OAuth...')
      setIsLoading(true)
      
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      })
      
      console.log('Google OAuth response:', { data, error })
      
      if (error) {
        console.error('Google OAuth error:', error)
        throw error
      }
      
      // The redirect will happen automatically if successful
      console.log('Google OAuth initiated successfully')
      
    } catch (error: any) {
      console.error('Google sign-in error:', error)
      setIsLoading(false)
      throw new Error(error.message || 'Failed to sign in with Google')
    }
  }

  async function signOut() {
    try {
      await supabase.auth.signOut()
      localStorage.removeItem('auth_token')
      setUser(null)
      setProperties([])
      setBookings([])
      setAnalytics(null)
    } catch (error) {
      console.error('Sign out error:', error)
    }
  }

  // Property methods
  async function createProperty(propertyData: Partial<Property>): Promise<Property> {
    const property = await makeAPIRequest('/properties', {
      method: 'POST',
      body: JSON.stringify(propertyData)
    })
    
    setProperties(prev => [property, ...prev])
    return property
  }

  async function updateProperty(id: string, propertyData: Partial<Property>): Promise<Property> {
    const property = await makeAPIRequest(`/properties/${id}`, {
      method: 'PUT',
      body: JSON.stringify(propertyData)
    })
    
    setProperties(prev => prev.map(p => p.id === id ? property : p))
    return property
  }

  async function deleteProperty(id: string): Promise<void> {
    await makeAPIRequest(`/properties/${id}`, {
      method: 'DELETE'
    })
    
    setProperties(prev => prev.filter(p => p.id !== id))
  }

  async function loadProperties() {
    try {
      const propertiesData = await makeAPIRequest('/properties')
      setProperties(propertiesData)
    } catch (error) {
      console.error('Load properties error:', error)
    }
  }

  async function generateAIDescription(propertyData: Partial<Property>): Promise<string> {
    const requestBody = {
      property_data: propertyData,
      use_anthropic: false  // Default to OpenAI, can be made configurable later
    }
    
    console.log('Sending AI description request:', requestBody)
    
    const response = await makeAPIRequest('/properties/ai/generate-description', {
      method: 'POST',
      body: JSON.stringify(requestBody)
    })
    
    console.log('AI description response:', response)
    return response.description
  }

  // Booking methods
  async function loadBookings() {
    try {
      const bookingsData = await makeAPIRequest('/bookings')
      setBookings(bookingsData)
    } catch (error) {
      console.error('Load bookings error:', error)
    }
  }

  async function updateBooking(id: string, bookingData: Partial<Booking>): Promise<Booking> {
    const booking = await makeAPIRequest(`/bookings/${id}`, {
      method: 'PUT',
      body: JSON.stringify(bookingData)
    })
    
    setBookings(prev => prev.map(b => b.id === id ? booking : b))
    return booking
  }

  // Analytics methods
  async function getAnalytics() {
    try {
      const analyticsData = await makeAPIRequest('/analytics')
      setAnalytics(analyticsData)
      return analyticsData
    } catch (error) {
      console.error('Get analytics error:', error)
      throw error
    }
  }

  // Financial methods
  async function getFinancialSummary(period: string = '30days') {
    try {
      return await makeAPIRequest(`/financials/summary?period=${period}`)
    } catch (error) {
      console.error('Get financial summary error:', error)
      throw error
    }
  }

  async function getBankAccounts() {
    try {
      return await makeAPIRequest('/financials/bank-accounts')
    } catch (error) {
      console.error('Get bank accounts error:', error)
      throw error
    }
  }

  async function addBankAccount(accountData: any) {
    try {
      return await makeAPIRequest('/financials/bank-accounts', {
        method: 'POST',
        body: JSON.stringify(accountData)
      })
    } catch (error) {
      console.error('Add bank account error:', error)
      throw error
    }
  }

  async function requestPayout(amount: number) {
    try {
      return await makeAPIRequest('/financials/payouts/request', {
        method: 'POST',
        body: JSON.stringify({ amount })
      })
    } catch (error) {
      console.error('Request payout error:', error)
      throw error
    }
  }

  async function getTransactions(limit: number = 50) {
    try {
      return await makeAPIRequest(`/financials/transactions?limit=${limit}`)
    } catch (error) {
      console.error('Get transactions error:', error)
      throw error
    }
  }

  async function updatePayoutSettings(settings: any) {
    try {
      return await makeAPIRequest('/financials/payout-settings', {
        method: 'PUT',
        body: JSON.stringify(settings)
      })
    } catch (error) {
      console.error('Update payout settings error:', error)
      throw error
    }
  }

  // User/Settings methods
  async function getUserProfile(): Promise<User> {
    try {
      return await makeAPIRequest('/users/profile')
    } catch (error) {
      console.error('Get user profile error:', error)
      throw error
    }
  }

  async function updateUserProfile(updates: Partial<User>): Promise<User> {
    try {
      const updatedUser = await makeAPIRequest('/users/profile', {
        method: 'PUT',
        body: JSON.stringify(updates)
      })
      setUser(updatedUser)
      return updatedUser
    } catch (error) {
      console.error('Update user profile error:', error)
      throw error
    }
  }

  async function updateUserSettings(settings: any): Promise<void> {
    try {
      await makeAPIRequest('/users/settings', {
        method: 'PUT',
        body: JSON.stringify(settings)
      })
    } catch (error) {
      console.error('Update user settings error:', error)
      throw error
    }
  }

  async function changePassword(currentPassword: string, newPassword: string, confirmPassword: string): Promise<void> {
    try {
      await makeAPIRequest('/users/change-password', {
        method: 'POST',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmPassword
        })
      })
    } catch (error) {
      console.error('Change password error:', error)
      throw error
    }
  }

  async function getUserNotifications(): Promise<any> {
    try {
      return await makeAPIRequest('/users/notifications')
    } catch (error) {
      console.error('Get user notifications error:', error)
      throw error
    }
  }

  async function updateUserNotifications(notifications: any): Promise<void> {
    try {
      await makeAPIRequest('/users/notifications', {
        method: 'PUT',
        body: JSON.stringify(notifications)
      })
    } catch (error) {
      console.error('Update user notifications error:', error)
      throw error
    }
  }

  // UAE Location Services
  async function getUAEEmirates(): Promise<any> {
    try {
      return await makeAPIRequest('/locations/emirates')
    } catch (error) {
      console.error('Get UAE emirates error:', error)
      throw error
    }
  }

  async function getEmirateAreas(emirate: string): Promise<string[]> {
    try {
      return await makeAPIRequest(`/locations/emirates/${emirate}/areas`)
    } catch (error) {
      console.error('Get emirate areas error:', error)
      throw error
    }
  }

  async function getPopularLocations(): Promise<string[]> {
    try {
      return await makeAPIRequest('/locations/popular')
    } catch (error) {
      console.error('Get popular locations error:', error)
      throw error
    }
  }

  async function searchLocations(query: string): Promise<any> {
    try {
      return await makeAPIRequest(`/locations/search?q=${encodeURIComponent(query)}`)
    } catch (error) {
      console.error('Search locations error:', error)
      throw error
    }
  }

  async function validateLocation(emirate: string, area?: string): Promise<any> {
    try {
      const params = new URLSearchParams({ emirate })
      if (area) params.append('area', area)
      
      return await makeAPIRequest(`/locations/validate?${params.toString()}`)
    } catch (error) {
      console.error('Validate location error:', error)
      throw error
    }
  }

  async function getUAEAmenities(): Promise<string[]> {
    try {
      return await makeAPIRequest('/locations/amenities')
    } catch (error) {
      console.error('Get UAE amenities error:', error)
      throw error
    }
  }

  async function getUAEPropertyTypes(): Promise<any> {
    try {
      return await makeAPIRequest('/locations/property-types')
    } catch (error) {
      console.error('Get UAE property types error:', error)
      throw error
    }
  }

  const contextValue: AppContextType = {
    // State
    user,
    isLoading,
    properties,
    bookings,
    analytics,
    
    // Auth methods
    signIn,
    signUp,
    signInWithGoogle,
    signOut,
    
    // Property methods
    createProperty,
    updateProperty,
    deleteProperty,
    loadProperties,
    generateAIDescription,
    
    // Booking methods
    loadBookings,
    updateBooking,
    
    // Analytics methods
    getAnalytics,
    
    // Financial methods
    getFinancialSummary,
    getBankAccounts,
    addBankAccount,
    requestPayout,
    getTransactions,
    updatePayoutSettings,
    
    // User/Settings methods
    getUserProfile,
    updateUserProfile,
    updateUserSettings,
    changePassword,
    getUserNotifications,
    updateUserNotifications,
    
    // UAE Location methods
    getUAEEmirates,
    getEmirateAreas,
    getPopularLocations,
    searchLocations,
    validateLocation,
    getUAEAmenities,
    getUAEPropertyTypes,
  }

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useApp must be used within an AppProvider')
  }
  return context
}