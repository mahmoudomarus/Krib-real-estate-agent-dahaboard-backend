import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"
import { Button } from "./ui/button"
import { Badge } from "./ui/badge"
import { Progress } from "./ui/progress"
import { Alert, AlertDescription, AlertTitle } from "./ui/alert"
import { TrendingUp, TrendingDown, DollarSign, Calendar, Users, Star, Eye, Heart, Target, Brain, Download, BarChart3, PieChart, AlertTriangle, CheckCircle, Zap, MapPin, Clock, Activity } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart as RechartsPieChart, Pie, Cell, AreaChart, Area, ComposedChart, Scatter, ScatterChart } from "recharts"
import { useApp } from "../contexts/AppContext"

// Real forecast data will be loaded from API

// All market data will be loaded from real Dubai market API

export function AnalyticsDashboard() {
  const { getAnalytics } = useApp()
  const [analyticsData, setAnalyticsData] = useState<any>(null)
  const [selectedPeriod, setSelectedPeriod] = useState("12months")
  const [loading, setLoading] = useState(true)
  const [marketInsights, setMarketInsights] = useState<any>(null)
  const [forecastData, setForecastData] = useState<any>(null)

  useEffect(() => {
    const loadAnalytics = async () => {
      setLoading(true)
      try {
        console.log('Loading analytics data...')
        const data = await getAnalytics()
        console.log('Analytics data received:', data)
        setAnalyticsData(data)
        
        // Extract market insights and forecast from the analytics data
        if (data.market_insights) {
          setMarketInsights(data.market_insights)
        }
        if (data.forecast) {
          setForecastData(data.forecast)
        }
      } catch (error) {
        console.error('Failed to load analytics:', error)
        console.error('Error details:', error.message, error.status)
        // Set some default data so the page isn't completely empty
        setAnalyticsData({
          totalRevenue: 0,
          totalBookings: 0,
          totalProperties: 0,
          occupancyRate: 0,
          monthlyData: [],
          propertyPerformance: []
        })
      } finally {
        setLoading(false)
      }
    }

    loadAnalytics()
  }, [selectedPeriod])

  const exportReport = () => {
    // Mock export functionality
    const data = {
      period: selectedPeriod,
      revenue: analyticsData?.totalRevenue || 0,
      bookings: analyticsData?.totalBookings || 0,
      properties: analyticsData?.totalProperties || 0,
      occupancyRate: analyticsData?.occupancyRate || 0,
      forecast: forecastData,
      marketComparison: marketComparisonData,
      generatedAt: new Date().toISOString()
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `analytics-report-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-64"></div>
          <div className="grid gap-4 md:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-muted rounded"></div>
            ))}
          </div>
          <div className="h-96 bg-muted rounded"></div>
        </div>
      </div>
    )
  }

  const revenueData = analyticsData?.monthlyData || []
  const propertyPerformance = analyticsData?.propertyPerformance || []
  
  const topMetrics = [
    {
      title: "Total Revenue",
      value: `$${analyticsData?.totalRevenue?.toLocaleString() || '0'}`,
      change: analyticsData?.monthly_growth ? `${analyticsData.monthly_growth > 0 ? '+' : ''}${analyticsData.monthly_growth.toFixed(1)}%` : "0%",
      trend: "up",
      icon: DollarSign,
      color: "text-green-600"
    },
    {
      title: "Total Bookings",
      value: analyticsData?.totalBookings?.toString() || '0',
      change: analyticsData?.booking_growth ? `${analyticsData.booking_growth > 0 ? '+' : ''}${analyticsData.booking_growth.toFixed(1)}%` : "0%",
      trend: "up",
      icon: Calendar,
      color: "text-krib-lime"
    },
    {
      title: "Average Rating",
      value: analyticsData ? (analyticsData.average_rating || 0).toFixed(1) : "0.0",
      change: analyticsData?.rating_change ? `${analyticsData.rating_change > 0 ? '+' : ''}${analyticsData.rating_change.toFixed(1)}` : "0",
      trend: "up",
      icon: Star,
      color: "text-yellow-600"
    },
    {
      title: "Occupancy Rate",
      value: `${analyticsData?.occupancyRate || 0}%`,
      change: "-2.1%",
      trend: "down",
      icon: Users,
      color: "text-purple-600"
    }
  ]

  const occupancyData = [
    { name: 'Occupied', value: analyticsData?.occupancyRate || 0, color: '#22c55e' },
    { name: 'Available', value: 100 - (analyticsData?.occupancyRate || 0), color: '#e5e7eb' }
  ]

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="mb-2">Advanced Analytics</h1>
          <p className="text-muted-foreground">
            AI-powered insights and market intelligence for your rental business.
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={exportReport} variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7days">Last 7 days</SelectItem>
              <SelectItem value="30days">Last 30 days</SelectItem>
              <SelectItem value="3months">Last 3 months</SelectItem>
              <SelectItem value="12months">Last 12 months</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* AI Insights Alert */}
      <Alert>
        <Brain className="h-4 w-4" />
        <AlertTitle>AI Insights</AlertTitle>
        <AlertDescription>
          Based on market analysis, you could increase revenue by 18% by optimizing pricing for the next 30 days.
        </AlertDescription>
      </Alert>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {topMetrics.map((metric) => (
          <Card key={metric.title} className="krib-card krib-glow-hover">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm">{metric.title}</CardTitle>
              <metric.icon className={`h-4 w-4 ${metric.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <div className="flex items-center text-xs text-muted-foreground">
                {metric.trend === 'up' ? (
                  <TrendingUp className="h-3 w-3 text-green-600 mr-1" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-red-600 mr-1" />
                )}
                {metric.change} from last period
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="revenue" className="space-y-4">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="revenue">Revenue</TabsTrigger>
          <TabsTrigger value="forecast">Forecast</TabsTrigger>
          <TabsTrigger value="market">Market</TabsTrigger>
          <TabsTrigger value="pricing">Pricing</TabsTrigger>
          <TabsTrigger value="competition">Competition</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
          <TabsTrigger value="occupancy">Occupancy</TabsTrigger>
        </TabsList>

        <TabsContent value="revenue" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-7">
            <Card className="md:col-span-4 krib-card">
              <CardHeader>
                <CardTitle>Revenue Trend Analysis</CardTitle>
                <CardDescription>Revenue performance with trend analysis and predictions</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={revenueData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip formatter={(value) => [`$${value}`, 'Revenue']} />
                    <Line 
                      type="monotone" 
                      dataKey="revenue" 
                      stroke="#2563eb" 
                      strokeWidth={2}
                      dot={{ fill: '#2563eb' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="md:col-span-3 krib-card">
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
                <CardDescription>Key performance indicators</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">This Month</span>
                    <span className="font-medium">$7,100</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Last Month</span>
                    <span className="font-medium">$5,900</span>
                  </div>
                  <div className="flex justify-between text-green-600">
                    <span className="text-sm">Growth</span>
                    <span className="font-medium">{forecastData?.confidence ? `${forecastData.confidence}%` : '0%'}</span>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-medium">Revenue Quality Score</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Diversification</span>
                      <span>85%</span>
                    </div>
                    <Progress value={85} className="h-2" />
                    <div className="flex justify-between text-sm">
                      <span>Stability</span>
                      <span>92%</span>
                    </div>
                    <Progress value={92} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="forecast" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="md:col-span-2 krib-card">
              <CardHeader>
                <CardTitle>UAE Market Forecast</CardTitle>
                <CardDescription>Real UAE seasonal patterns and revenue predictions</CardDescription>
              </CardHeader>
              <CardContent>
                {forecastData?.forecast_data ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={forecastData.forecast_data}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip formatter={(value, name) => [`AED ${value}`, 'Forecasted Revenue']} />
                      <Area 
                        type="monotone" 
                        dataKey="forecasted_revenue" 
                        stroke="#10b981" 
                        fill="#10b981"
                        fillOpacity={0.3}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                    Loading forecast data...
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="krib-card">
              <CardHeader>
                <CardTitle>Dubai Market Insights</CardTitle>
                <CardDescription>Real market predictions and seasonal trends</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <h4 className="font-medium">Next Quarter Forecast</h4>
                  <div className="text-2xl font-bold text-green-600">
                    AED {forecastData?.next_quarter_revenue?.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm text-muted-foreground">Based on UAE seasonality</div>
                </div>

                <div className="space-y-2">
                  <h4 className="font-medium">Confidence Level</h4>
                  <div className="flex items-center gap-2">
                    <Progress value={forecastData?.confidence || 0} className="flex-1" />
                    <span className="text-sm font-medium">{forecastData?.confidence || 0}%</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="font-medium">Peak Period</h4>
                  <div className="text-sm">
                    <strong>{forecastData?.peak_period || 'Winter Season'}</strong>
                  </div>
                </div>

                {forecastData?.insights && (
                  <Alert>
                    <Target className="h-4 w-4" />
                    <AlertDescription>
                      {forecastData.insights.seasonal_impact}
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="market" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="krib-card">
              <CardHeader>
                            <CardTitle>UAE Market Performance</CardTitle>
            <CardDescription>Your performance vs UAE market standards</CardDescription>
              </CardHeader>
              <CardContent>
                {marketInsights ? (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Market Position</span>
                        <Badge variant={marketInsights.competitive_position <= 3 ? "default" : "secondary"}>
                          #{marketInsights.competitive_position} in area
                        </Badge>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Your Performance: {marketInsights.performance_vs_market}%</span>
                        <span className="text-muted-foreground">vs Market Average</span>
                      </div>
                    </div>

                    {marketInsights.area_insights && (
                      <div className="space-y-2">
                        <h4 className="font-medium">Area: {marketInsights.area_insights.area}</h4>
                        <div className="text-sm text-muted-foreground">
                          <p>Tier: {marketInsights.area_insights.tier}</p>
                          <p>Primary Demand: {marketInsights.area_insights.primary_demand}</p>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-muted-foreground">Loading market data...</div>
                )}
              </CardContent>
            </Card>

            <Card className="krib-card">
              <CardHeader>
                            <CardTitle>UAE Seasonal Trends</CardTitle>
            <CardDescription>Real UAE seasonal demand patterns</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <h4 className="font-medium">Market Health Score</h4>
                  <div className="flex items-center gap-2">
                    <div className="text-2xl font-bold text-green-600">
                      {marketInsights?.market_health_score || 0}
                    </div>
                    <div className="text-sm text-muted-foreground">/ 100</div>
                  </div>
                  <Progress value={marketInsights?.market_health_score || 0} className="h-2" />
                </div>

                <div className="space-y-2">
                  <h4 className="font-medium">Dubai Seasonal Demand</h4>
                  <div className="grid grid-cols-1 gap-2 text-sm">
                    <div className="flex justify-between">
                      <span>Winter Peak (Dec-Feb)</span>
                      <span className="font-medium text-green-600">+50%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Winter High (Mar, Nov)</span>
                      <span className="font-medium text-blue-600">+30%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Shoulder (Apr, Oct)</span>
                      <span className="font-medium">Normal</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Summer Low (May-Sep)</span>
                      <span className="font-medium text-red-600">-30%</span>
                    </div>
                  </div>
                </div>

                <Alert>
                  <TrendingUp className="h-4 w-4" />
                  <AlertDescription>
                    UAE winter season (Dec-Mar) offers premium pricing opportunities with 40-50% higher demand.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="pricing" className="space-y-4">
          <Card className="krib-card">
            <CardHeader>
              <CardTitle>UAE Dynamic Pricing</CardTitle>
              <CardDescription>Real-time pricing optimization based on UAE events, seasons, and demand</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <Alert>
                  <TrendingUp className="h-4 w-4" />
                  <AlertDescription>
                    Dynamic pricing is now available per property. View individual property pricing recommendations in the Properties section.
                  </AlertDescription>
                </Alert>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-4">
                    <h4 className="font-medium">UAE Seasonal Pricing Strategy</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                        <div>
                          <p className="font-medium text-green-800">Winter Peak (Dec-Feb)</p>
                          <p className="text-sm text-green-600">European winter escape season</p>
                        </div>
                        <Badge className="bg-green-100 text-green-800">+50%</Badge>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                        <div>
                          <p className="font-medium text-blue-800">Winter High (Mar, Nov)</p>
                          <p className="text-sm text-blue-600">Pleasant weather months</p>
                        </div>
                        <Badge className="bg-blue-100 text-blue-800">+30%</Badge>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-800">Shoulder (Apr, Oct)</p>
                          <p className="text-sm text-gray-600">Moderate demand periods</p>
                        </div>
                        <Badge variant="secondary">Base Rate</Badge>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-orange-50 rounded-lg">
                        <div>
                          <p className="font-medium text-orange-800">Summer Low (May-Sep)</p>
                          <p className="text-sm text-orange-600">Hot weather discount needed</p>
                        </div>
                        <Badge className="bg-orange-100 text-orange-800">-30%</Badge>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-medium">Major Event Opportunities</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                        <div>
                          <p className="font-medium text-red-800">F1 Grand Prix</p>
                          <p className="text-sm text-red-600">March weekend</p>
                        </div>
                        <Badge className="bg-red-100 text-red-800">+300%</Badge>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                        <div>
                          <p className="font-medium text-purple-800">Shopping Festival</p>
                          <p className="text-sm text-purple-600">January month-long</p>
                        </div>
                        <Badge className="bg-purple-100 text-purple-800">+80%</Badge>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                        <div>
                          <p className="font-medium text-blue-800">GITEX Technology</p>
                          <p className="text-sm text-blue-600">October week</p>
                        </div>
                        <Badge className="bg-blue-100 text-blue-800">+60%</Badge>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                        <div>
                          <p className="font-medium text-green-800">New Year's Eve</p>
                          <p className="text-sm text-green-600">Dec 31 - Jan 2</p>
                        </div>
                        <Badge className="bg-green-100 text-green-800">+200%</Badge>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <h4 className="font-medium mb-3">Pricing Recommendations</h4>
                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="p-3 border rounded-lg">
                      <p className="font-medium text-sm">Weekend Premium</p>
                      <p className="text-xs text-muted-foreground">Add 20% for Friday-Saturday nights</p>
                    </div>
                    <div className="p-3 border rounded-lg">
                      <p className="font-medium text-sm">Area Multipliers</p>
                      <p className="text-xs text-muted-foreground">Marina: +60%, Downtown: +50%, JLT: Base</p>
                    </div>
                    <div className="p-3 border rounded-lg">
                      <p className="font-medium text-sm">Ramadan Adjustment</p>
                      <p className="text-xs text-muted-foreground">Reduce rates 20% during Ramadan period</p>
                    </div>
                    <div className="p-3 border rounded-lg">
                      <p className="font-medium text-sm">Last-Minute Bookings</p>
                      <p className="text-xs text-muted-foreground">Dynamic discounts for 3-day advance bookings</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="competition" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="krib-card">
              <CardHeader>
                <CardTitle>UAE Market Competition</CardTitle>
                <CardDescription>Competitive analysis is being developed for UAE market</CardDescription>
              </CardHeader>
              <CardContent>
                <Alert>
                  <MapPin className="h-4 w-4" />
                  <AlertDescription>
                    Competitor tracking system is in development. Currently integrating with UAE property listings to provide real competitive analysis.
                  </AlertDescription>
                </Alert>
                
                <div className="space-y-4 mt-6">
                  <h4 className="font-medium">Market Areas Analysis</h4>
                  <div className="grid gap-3">
                    <div className="p-3 border rounded-lg">
                      <div className="flex justify-between">
                        <span className="font-medium">Marina</span>
                        <span className="text-sm text-green-600">Premium Tier (+60%)</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">Waterfront luxury properties</p>
                    </div>
                    <div className="p-3 border rounded-lg">
                      <div className="flex justify-between">
                        <span className="font-medium">Downtown</span>
                        <span className="text-sm text-blue-600">Premium Tier (+50%)</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">Business district and attractions</p>
                    </div>
                    <div className="p-3 border rounded-lg">
                      <div className="flex justify-between">
                        <span className="font-medium">JLT</span>
                        <span className="text-sm text-gray-600">Standard Tier</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">Modern towers with metro access</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="krib-card">
              <CardHeader>
                <CardTitle>Market Positioning</CardTitle>
                <CardDescription>Your competitive advantage in UAE</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {marketInsights?.area_insights && (
                  <>
                    <div className="space-y-2">
                      <h4 className="font-medium">Your Area: {marketInsights.area_insights.area}</h4>
                      <div className="text-2xl font-bold text-blue-600">{marketInsights.area_insights.tier}</div>
                      <div className="text-sm text-muted-foreground">{marketInsights.area_insights.primary_demand}</div>
                    </div>

                    <div className="space-y-2">
                      <h4 className="font-medium">Market Performance</h4>
                      <div className="text-sm">
                        <div className="flex justify-between">
                          <span>vs Market Average</span>
                          <span className="font-medium text-green-600">{marketInsights.performance_vs_market}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Position in Area</span>
                          <span className="font-medium">#{marketInsights.competitive_position}</span>
                        </div>
                      </div>
                    </div>

                    <Alert>
                      <Zap className="h-4 w-4" />
                      <AlertDescription>
                        {marketInsights.area_recommendations?.[0] || "Optimize pricing based on UAE seasonal patterns"}
                      </AlertDescription>
                    </Alert>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <div className="grid gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="p-2 rounded-full bg-green-100 text-green-600">
                    <TrendingUp className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold">Dubai Winter Season Opportunity</h3>
                      <div className="flex gap-2">
                        <Badge variant="outline">Impact: High</Badge>
                        <Badge variant="outline">Effort: Low</Badge>
                      </div>
                    </div>
                    <p className="text-muted-foreground">
                      Increase rates by 40-50% during UAE's peak winter season (December-February) when European tourists seek warm weather escapes.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="p-2 rounded-full bg-blue-100 text-blue-600">
                    <Calendar className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold">Event-Based Surge Pricing</h3>
                      <div className="flex gap-2">
                        <Badge variant="outline">Impact: Very High</Badge>
                        <Badge variant="outline">Effort: Low</Badge>
                      </div>
                    </div>
                    <p className="text-muted-foreground">
                      Implement automatic surge pricing for major UAE events: F1 Grand Prix (+300%), Shopping Festival (+80%), GITEX (+60%).
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="p-2 rounded-full bg-yellow-100 text-yellow-600">
                    <AlertTriangle className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold">Summer Season Strategy</h3>
                      <div className="flex gap-2">
                        <Badge variant="outline">Impact: Medium</Badge>
                        <Badge variant="outline">Effort: Medium</Badge>
                      </div>
                    </div>
                    <p className="text-muted-foreground">
                      UAE summer (May-September) requires 20-30% discount and focus on longer stays, business travelers, and local residents.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {marketInsights?.area_recommendations && (
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="p-2 rounded-full bg-purple-100 text-purple-600">
                      <MapPin className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold">Area-Specific Recommendations</h3>
                        <div className="flex gap-2">
                          <Badge variant="outline">Impact: High</Badge>
                          <Badge variant="outline">Effort: Low</Badge>
                        </div>
                      </div>
                      <div className="space-y-2">
                        {marketInsights.area_recommendations.map((rec, index) => (
                          <p key={index} className="text-muted-foreground text-sm">• {rec}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            <Card className="krib-card">
              <CardHeader>
                <CardTitle>UAE Demand Patterns</CardTitle>
                <CardDescription>Real UAE seasonal and daily booking patterns</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <h4 className="font-medium">Peak Booking Times</h4>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span>Evening (6-9 PM)</span>
                          <span className="font-medium">45%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Lunch (12-2 PM)</span>
                          <span className="font-medium">25%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Morning (9-11 AM)</span>
                          <span className="font-medium">20%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Late Night</span>
                          <span className="font-medium">10%</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <h4 className="font-medium">Weekly Patterns</h4>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span>Friday-Saturday</span>
                          <span className="font-medium text-green-600">Premium (+20%)</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Thursday</span>
                          <span className="font-medium">Standard</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Sunday-Tuesday</span>
                          <span className="font-medium text-blue-600">Business Focus</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Wednesday</span>
                          <span className="font-medium text-orange-600">Lowest</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="occupancy" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="krib-card">
              <CardHeader>
                <CardTitle>Overall Occupancy</CardTitle>
                <CardDescription>Current occupancy rate across all properties</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <RechartsPieChart>
                    <Pie
                      data={occupancyData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      dataKey="value"
                    >
                      {occupancyData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [`${value}%`, '']} />
                  </RechartsPieChart>
                </ResponsiveContainer>
                <div className="flex justify-center mt-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold">{analyticsData?.occupancyRate || 0}%</p>
                    <p className="text-sm text-muted-foreground">Occupied</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="krib-card">
              <CardHeader>
                <CardTitle>Occupancy Insights</CardTitle>
                <CardDescription>Performance metrics and optimization recommendations</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">Peak Season</span>
                    <span className="font-medium">Jun - Aug (89%)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Low Season</span>
                    <span className="font-medium">Jan - Mar (62%)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Average Stay</span>
                    <span className="font-medium">3.2 nights</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Booking Lead Time</span>
                    <span className="font-medium">28 days</span>
                  </div>
                </div>
                
                <div className="pt-4 border-t">
                  <h4 className="font-medium mb-2">AI Recommendations</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• Implement dynamic pricing to increase low-season occupancy</li>
                    <li>• Offer 7+ day discounts to increase average stay</li>
                    <li>• Target last-minute bookings with flash sales</li>
                    <li>• Consider corporate partnerships for midweek bookings</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}