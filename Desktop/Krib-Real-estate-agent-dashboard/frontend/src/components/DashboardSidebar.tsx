import { Home, Building2, Plus, BarChart3, Calendar, Settings, Bot, LogOut, User, DollarSign } from "lucide-react"
import KribLogo from "../assets/krib-logo.svg"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from "./ui/sidebar"
import { NavigationItem } from "../App"
import { Button } from "./ui/button"
import { useApp } from "../contexts/AppContext"

interface DashboardSidebarProps {
  activeSection: NavigationItem
  onSectionChange: (section: NavigationItem) => void
}

const navigationItems = [
  {
    id: 'overview' as NavigationItem,
    title: 'Overview',
    icon: Home,
    description: 'Dashboard overview'
  },
  {
    id: 'properties' as NavigationItem,
    title: 'My Properties',
    icon: Building2,
    description: 'Manage your listings'
  },
  {
    id: 'add-property' as NavigationItem,
    title: 'Add Property',
    icon: Plus,
    description: 'AI-powered listing creation'
  },
  {
    id: 'analytics' as NavigationItem,
    title: 'Analytics',
    icon: BarChart3,
    description: 'Performance insights'
  },
  {
    id: 'bookings' as NavigationItem,
    title: 'Bookings',
    icon: Calendar,
    description: 'Manage reservations'
  },
  {
    id: 'financials' as NavigationItem,
    title: 'Financials',
    icon: DollarSign,
    description: 'Earnings & payouts'
  },
  {
    id: 'settings' as NavigationItem,
    title: 'Settings',
    icon: Settings,
    description: 'Account preferences'
  }
]

export function DashboardSidebar({ activeSection, onSectionChange }: DashboardSidebarProps) {
  const { user, signOut } = useApp()
  
  return (
    <Sidebar className="krib-sidebar">
      <SidebarHeader className="krib-sidebar-header border-b border-sidebar-border p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl krib-logo-container">
            <img src={KribLogo} alt="Krib" className="h-8 w-8" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-sidebar-foreground bg-gradient-to-r from-krib-gray-dark to-krib-black bg-clip-text">
              Krib
            </h2>
            <p className="text-sm text-sidebar-foreground/70 font-medium">Property Dashboard</p>
          </div>
        </div>
      </SidebarHeader>
      
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="krib-sidebar-group-label">Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="krib-sidebar-menu">
              {navigationItems.map((item) => (
                <SidebarMenuItem key={item.id}>
                  <SidebarMenuButton
                    onClick={() => onSectionChange(item.id)}
                    isActive={activeSection === item.id}
                    tooltip={item.description}
                    className={`transition-all duration-300 krib-sidebar-item ${
                      activeSection === item.id ? 'krib-sidebar-active' : ''
                    }`}
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      
      <SidebarFooter className="border-t border-sidebar-border p-4 krib-sidebar-header">
        <div className="space-y-3">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/50 border border-krib-lime/10">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-krib-lime/20 to-krib-lime-light/10">
              <User className="h-4 w-4 text-krib-gray-dark" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">{user?.name || 'User'}</p>
              <p className="text-xs text-sidebar-foreground/70 truncate">{user?.email}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={signOut}
            className="w-full justify-start text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-red-50 transition-all duration-200"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Sign Out
          </Button>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}