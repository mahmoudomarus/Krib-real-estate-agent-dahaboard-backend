# 🚀 Krib AI Upgrade Guide: From Mock to Real

This guide will help you upgrade your Krib AI project from mockup data to a fully functional application with FastAPI backend, real AI integration, and S3 storage.

## 📋 What We've Built

### ✅ Completed (New Backend)
- **FastAPI Backend** with async support
- **Real Supabase Integration** (database, auth, storage)
- **AI Services** (OpenAI/Anthropic for descriptions, amenities, pricing)
- **S3 Storage** for scalable image handling
- **Real Analytics** with actual data calculations
- **Comprehensive API** with full CRUD operations
- **JWT Authentication** with Supabase
- **Database Schema** with proper relationships and constraints

### 🔄 Needs Updating (Frontend)
- Replace mock data with real API calls
- Update components to use new API endpoints
- Implement real image upload functionality
- Connect AI features to actual services

## 🛠️ Step 1: Set Up the Backend

### 1.1 Install and Configure Backend
```bash
cd backend
python setup.py
```

### 1.2 Configure API Keys
Edit `backend/.env` with your keys:
```env
# Required: OpenAI or Anthropic for AI features
OPENAI_API_KEY=sk-your-openai-key
# OR
ANTHROPIC_API_KEY=your-anthropic-key

# Required: AWS S3 for image uploads
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
S3_BUCKET_NAME=your-rental-ai-bucket

# Already configured from your Supabase project
SUPABASE_URL=https://bpomacnqaqzgeuahhlka.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 1.3 Start the Backend
```bash
cd backend
./run.sh  # Unix/macOS
# or
run.bat   # Windows
```

The API will be available at `http://localhost:8000`

## 🔄 Step 2: Update Frontend Configuration

### 2.1 Update AppContext to Use Real API

Replace the current `contexts/AppContext.tsx` with API calls to your FastAPI backend:

```typescript
// contexts/AppContext.tsx
const API_BASE_URL = 'http://localhost:8000/api'

// Update signIn function
const signIn = async (email: string, password: string): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/signin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    
    if (response.ok) {
      const data = await response.json()
      setAccessToken(data.access_token)
      setUser(data.user)
      await loadProperties()
      await loadBookings()
      return true
    }
    return false
  } catch (error) {
    console.error('Sign in error:', error)
    return false
  }
}

// Update createProperty function
const createProperty = async (propertyData: any): Promise<Property | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/properties/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(propertyData)
    })
    
    if (response.ok) {
      const data = await response.json()
      setProperties(prev => [...prev, data])
      return data
    }
    return null
  } catch (error) {
    console.error('Create property error:', error)
    return null
  }
}
```

### 2.2 Update Property Components

#### PropertyList.tsx - Use Real Data
Replace the hardcoded properties array:

```typescript
// Remove hardcoded properties array
// const properties = [...]

// Use properties from context
const { properties, loadProperties } = useApp()

useEffect(() => {
  loadProperties()
}, [])
```

#### AddPropertyWizard.tsx - Real AI Integration
Update the AI description generation:

```typescript
const generateDescription = async () => {
  setIsGeneratingDescription(true)
  
  try {
    const response = await fetch(`${API_BASE_URL}/properties/ai/generate-description`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        property_data: {
          property_type: propertyData.propertyType,
          city: propertyData.location,
          bedrooms: parseInt(propertyData.bedrooms),
          bathrooms: parseInt(propertyData.bathrooms),
          max_guests: parseInt(propertyData.maxGuests),
          price_per_night: parseInt(propertyData.price),
          amenities: propertyData.amenities
        },
        use_anthropic: false // or true for Claude
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      setPropertyData(prev => ({ ...prev, description: result.description }))
      
      // Update AI messages with real response
      setAiMessages(prev => [...prev, {
        role: 'ai',
        content: `I've generated a compelling description for your property. Here it is:`
      }])
    }
  } catch (error) {
    console.error('AI description generation failed:', error)
  } finally {
    setIsGeneratingDescription(false)
  }
}
```

### 2.3 Update Image Upload Component

Replace the mock image upload in `ImageUpload.tsx`:

```typescript
const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
  const files = Array.from(event.target.files || [])
  if (files.length === 0) return

  setIsUploading(true)

  try {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })

    const response = await fetch(`${API_BASE_URL}/upload/property/${propertyId}/images`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      },
      body: formData
    })

    if (response.ok) {
      const results = await response.json()
      const newImageUrls = results.map(result => result.url)
      onImagesChange([...images, ...newImageUrls])
      toast.success(`${files.length} image(s) uploaded successfully`)
    } else {
      toast.error('Failed to upload images')
    }
  } catch (error) {
    toast.error('Upload failed')
  } finally {
    setIsUploading(false)
  }
}
```

### 2.4 Update Analytics Dashboard

Replace mock data in `AnalyticsDashboard.tsx`:

```typescript
const { getAnalytics } = useApp()
const [analyticsData, setAnalyticsData] = useState(null)

useEffect(() => {
  const loadAnalytics = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/analytics/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setAnalyticsData(data)
      }
    } catch (error) {
      console.error('Failed to load analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  loadAnalytics()
}, [])
```

### 2.5 Update Booking Management

Replace mock bookings in `BookingManagement.tsx`:

```typescript
const { bookings, loadBookings } = useApp()

useEffect(() => {
  loadBookings()
}, [])

// Remove hardcoded bookings array
// const bookings = [...]
```

## 🧪 Step 3: Test the Integration

### 3.1 Test Authentication
1. Sign up with a new account
2. Sign in with existing credentials
3. Verify user session persistence

### 3.2 Test Property Management
1. Create a new property (watch AI generate description)
2. Upload images to S3
3. Edit property details
4. Publish property

### 3.3 Test AI Features
1. Generate property descriptions
2. Get amenities suggestions
3. Try title optimization
4. Test pricing strategy

### 3.4 Test Analytics
1. View dashboard overview
2. Check property performance
3. Review analytics charts with real data

## 📝 Step 4: Environment Configuration

### 4.1 Frontend Environment
Create `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_SUPABASE_URL=https://bpomacnqaqzgeuahhlka.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4.2 Update API Base URL
Create a constants file `frontend/src/config/api.ts`:
```typescript
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY
```

## 🚀 Step 5: Production Deployment

### 5.1 Deploy Backend
**Option A: Railway**
```bash
# Connect to Railway
railway login
railway init
railway add postgresql
railway deploy
```

**Option B: Render**
1. Connect GitHub repository
2. Set environment variables
3. Deploy as web service

### 5.2 Deploy Frontend
**Option A: Vercel**
```bash
vercel --prod
```

**Option B: Netlify**
```bash
netlify deploy --prod
```

### 5.3 Update Environment Variables
Update production environment variables:
- Backend API URL in frontend
- CORS origins in backend
- Database connection strings
- API keys and secrets

## 🔧 Step 6: Additional Features to Implement

### 6.1 Real-time Features (Optional)
- WebSocket connections for live updates
- Real-time booking notifications
- Live analytics updates

### 6.2 Advanced AI Features (Optional)
- Market analysis integration
- Automated pricing adjustments
- Competitive analysis
- Review sentiment analysis

### 6.3 Payment Integration (Optional)
- Stripe/PayPal integration
- Booking payment processing
- Automatic payout calculations

## 🐛 Troubleshooting

### Common Issues:

1. **CORS Errors**
   - Ensure frontend URL is in backend CORS settings
   - Check API_BASE_URL configuration

2. **Authentication Failures**
   - Verify Supabase keys are correct
   - Check token expiration handling

3. **Image Upload Issues**
   - Confirm S3 bucket permissions
   - Verify AWS credentials

4. **AI Service Errors**
   - Check API key validity
   - Monitor usage limits
   - Implement fallback mechanisms

5. **Database Connection Issues**
   - Verify Supabase URL and keys
   - Check Row Level Security policies

## 📊 Monitoring and Analytics

### Set Up Monitoring:
1. **Backend Monitoring**
   - FastAPI built-in metrics
   - Supabase dashboard
   - AWS CloudWatch for S3

2. **Frontend Monitoring**
   - Error tracking (Sentry)
   - Performance monitoring
   - User analytics

3. **Business Metrics**
   - Property performance
   - User engagement
   - Revenue tracking

## 🎉 Congratulations!

You've successfully upgraded from a mockup to a fully functional AI-powered property management platform! 

Your application now includes:
- ✅ Real user authentication
- ✅ AI-powered property listing generation
- ✅ Scalable image storage
- ✅ Comprehensive analytics
- ✅ Real booking management
- ✅ Production-ready architecture

## 📞 Support

If you encounter issues during the upgrade:
1. Check the backend logs: `backend/logs/`
2. Review API documentation: `http://localhost:8000/docs`
3. Verify environment variables
4. Test individual API endpoints
5. Check Supabase dashboard for database issues

**Happy hosting! 🏠✨**
