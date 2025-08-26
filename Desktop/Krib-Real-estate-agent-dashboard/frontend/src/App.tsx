import { useState, useEffect } from "react"
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { SidebarProvider } from "./components/ui/sidebar"
import { AppProvider, useApp } from "./contexts/AppContext"
import { AuthForm } from "./components/AuthForm"
import { DashboardSidebar } from "./components/DashboardSidebar"
import { DashboardOverview } from "./components/DashboardOverview"
import { PropertyList } from "./components/PropertyList"
import { AddPropertyWizard } from "./components/AddPropertyWizard"
import { AnalyticsDashboard } from "./components/AnalyticsDashboard"
import { BookingManagement } from "./components/BookingManagement"
import { FinancialDashboard } from "./components/FinancialDashboard"
import { SettingsPage } from "./components/SettingsPage"

export type NavigationItem = 'overview' | 'properties' | 'add-property' | 'analytics' | 'bookings' | 'financials' | 'settings'

function DashboardContent() {
  const { user, isLoading } = useApp()
  const location = useLocation()
  const navigate = useNavigate()
  
  // Map URL paths to navigation items
  const getActiveSection = (pathname: string): NavigationItem => {
    const path = pathname.replace('/', '') || 'overview'
    return ['overview', 'properties', 'add-property', 'analytics', 'bookings', 'financials', 'settings'].includes(path) 
      ? path as NavigationItem 
      : 'overview'
  }
  
  const [activeSection, setActiveSection] = useState<NavigationItem>(getActiveSection(location.pathname))
  
  // Update active section when URL changes
  useEffect(() => {
    setActiveSection(getActiveSection(location.pathname))
  }, [location.pathname])
  
  // Handle section changes with navigation
  const handleSectionChange = (section: NavigationItem) => {
    setActiveSection(section)
    navigate(section === 'overview' ? '/' : `/${section}`)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <AuthForm />
  }



  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
                <DashboardSidebar 
          activeSection={activeSection} 
          onSectionChange={handleSectionChange} 
        />
        <main className="flex-1 overflow-auto krib-dashboard-background" style={{ marginLeft: '16rem' }}>
          <Routes>
            <Route path="/" element={<DashboardOverview />} />
            <Route path="/overview" element={<DashboardOverview />} />
            <Route path="/properties" element={<PropertyList />} />
            <Route path="/add-property" element={<AddPropertyWizard />} />
            <Route path="/analytics" element={<AnalyticsDashboard />} />
            <Route path="/bookings" element={<BookingManagement />} />
            <Route path="/financials" element={<FinancialDashboard />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </SidebarProvider>
  )
}

function DashboardApp() {
  return (
    <Router>
      <DashboardContent />
    </Router>
  )
}

export default function App() {
  return (
    <AppProvider>
      <DashboardApp />
    </AppProvider>
  )
}