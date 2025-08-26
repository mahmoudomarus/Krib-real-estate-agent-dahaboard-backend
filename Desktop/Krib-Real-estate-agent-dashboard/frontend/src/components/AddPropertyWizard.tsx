import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { ArrowLeft, ArrowRight, Bot, Upload, Check, MapPin, Home, Camera, Sparkles, X, Plus, Star, AlertCircle, Building, FileText, DollarSign } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { Textarea } from "./ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"
import { Checkbox } from "./ui/checkbox"
import { Badge } from "./ui/badge"
import { Progress } from "./ui/progress"
import { Alert, AlertDescription } from "./ui/alert"
import { useApp } from "../contexts/AppContext"
import { uploadMultipleImages } from "../services/imageUpload"

type WizardStep = 'basic-info' | 'details' | 'images' | 'amenities' | 'pricing' | 'preview' | 'published'

interface PropertyData {
  title: string
  address: string
  city: string
  state: string
  country: string
  property_type: string
  bedrooms: number
  bathrooms: number
  max_guests: number
  price_per_night: number
  description: string
  images: string[]
  amenities: string[]
}

// UAE-specific amenities and property types are loaded from the backend via useEffect

export function AddPropertyWizard() {
  const { 
    createProperty, 
    generateAIDescription, 
    getUAEEmirates, 
    getEmirateAreas, 
    getUAEPropertyTypes, 
    getUAEAmenities 
  } = useApp()
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState<WizardStep>('basic-info')
  const [isPublishing, setIsPublishing] = useState(false)
  const [isGeneratingDescription, setIsGeneratingDescription] = useState(false)
  const [isUploadingImages, setIsUploadingImages] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [uaeEmirates, setUAEEmirates] = useState<any[]>([])
  const [availableAreas, setAvailableAreas] = useState<string[]>([])
  const [uaePropertyTypes, setUAEPropertyTypes] = useState<any>({})
  const [uaeAmenities, setUAEAmenities] = useState<string[]>([])
  const [isLoadingAreas, setIsLoadingAreas] = useState(false)
  
  const [propertyData, setPropertyData] = useState<PropertyData>({
    title: '',
    address: '',
    city: '',
    state: '',
    country: 'UAE',
    property_type: '',
    bedrooms: 1,
    bathrooms: 1,
    max_guests: 2,
    price_per_night: 500, // Higher default for UAE market
    description: '',
    images: [],
    amenities: []
  })

  const steps = [
    { id: 'basic-info', title: 'Basic Info', icon: Building, description: 'Property basics' },
    { id: 'details', title: 'Details', icon: Home, description: 'Size & capacity' },
    { id: 'images', title: 'Photos', icon: Camera, description: 'Upload images' },
    { id: 'amenities', title: 'Amenities', icon: Sparkles, description: 'Features & perks' },
    { id: 'pricing', title: 'Pricing', icon: DollarSign, description: 'Set your rate' },
    { id: 'preview', title: 'Preview', icon: Check, description: 'Review & publish' },
  ]

  // Load UAE data on component mount
  useEffect(() => {
    loadUAEData()
  }, [])

  // Load areas when emirate changes
  useEffect(() => {
    if (propertyData.state) {
      loadEmirateAreas(propertyData.state)
    }
  }, [propertyData.state])

  const loadUAEData = async () => {
    try {
      const [emirates, propertyTypes, amenities] = await Promise.all([
        getUAEEmirates(),
        getUAEPropertyTypes(),
        getUAEAmenities()
      ])
      
      setUAEEmirates(emirates)
      setUAEPropertyTypes(propertyTypes)
      setUAEAmenities(amenities)
    } catch (error) {
      console.error('Failed to load UAE data from API, using fallback data:', error)
      
      // Fallback UAE data while API is being deployed
      setUAEEmirates([
        { value: "Dubai", label: "Dubai" },
        { value: "Abu Dhabi", label: "Abu Dhabi" },
        { value: "Sharjah", label: "Sharjah" },
        { value: "Ajman", label: "Ajman" },
        { value: "Ras Al Khaimah", label: "Ras Al Khaimah" },
        { value: "Fujairah", label: "Fujairah" },
        { value: "Umm Al Quwain", label: "Umm Al Quwain" }
      ])
      
      setUAEPropertyTypes({
        "apartment": "Apartment",
        "villa": "Villa", 
        "townhouse": "Townhouse",
        "penthouse": "Penthouse",
        "studio": "Studio",
        "duplex": "Duplex",
        "loft": "Loft",
        "compound": "Compound",
        "hotel_apartment": "Hotel Apartment",
        "office": "Office",
        "retail": "Retail Space"
      })
      
      setUAEAmenities([
        "Central Air Conditioning", "Maid's Room", "Driver's Room", "Built-in Wardrobes",
        "Covered Parking", "24/7 Security", "Swimming Pool", "Gym", "Children's Play Area",
        "WiFi", "Kitchen", "Washing Machine", "TV", "Balcony", "Sea View", "City View"
      ])
    }
  }

  const loadEmirateAreas = async (emirate: string) => {
    setIsLoadingAreas(true)
    try {
      const areas = await getEmirateAreas(emirate)
      setAvailableAreas(areas)
    } catch (error) {
      console.error('Failed to load emirate areas from API, using fallback data:', error)
      
      // Fallback areas data while API is being deployed
      const fallbackAreas: Record<string, string[]> = {
        "Dubai": [
          "Downtown Dubai", "Dubai Marina", "Jumeirah Beach Residence (JBR)",
          "Business Bay", "Palm Jumeirah", "Jumeirah", "Arabian Ranches",
          "Dubai Hills Estate", "City Walk", "DIFC", "Al Barsha", "The Greens"
        ],
        "Abu Dhabi": [
          "Abu Dhabi City", "Yas Island", "Saadiyat Island", "Al Reem Island",
          "Khalifa City", "Al Raha", "Masdar City", "Corniche", "Al Maryah Island"
        ],
        "Sharjah": [
          "Sharjah City", "Al Majaz", "Al Nahda", "Al Khan", "Al Qasba"
        ],
        "Ajman": [
          "Ajman City", "Al Nuaimiya", "Al Rashidiya", "Corniche Road"
        ],
        "Ras Al Khaimah": [
          "Ras Al Khaimah City", "Al Hamra", "Al Marjan Island", "Al Rams"
        ],
        "Fujairah": [
          "Fujairah City", "Dibba", "Kalba", "Khor Fakkan"
        ],
        "Umm Al Quwain": [
          "Umm Al Quwain City", "Al Salam City", "Falaj Al Mualla"
        ]
      }
      
      setAvailableAreas(fallbackAreas[emirate] || [])
    } finally {
      setIsLoadingAreas(false)
    }
  }

  const handleEmirateChange = (value: string) => {
    setPropertyData(prev => ({ 
      ...prev, 
      state: value,
      city: '' // Reset city when emirate changes
    }))
    setErrors(prev => ({ ...prev, state: '', city: '' }))
  }

  const currentStepIndex = steps.findIndex(step => step.id === currentStep)
  const progress = ((currentStepIndex + 1) / steps.length) * 100

  const validateStep = (step: WizardStep): boolean => {
    const newErrors: Record<string, string> = {}
    
    switch (step) {
      case 'basic-info':
        if (!propertyData.title.trim()) newErrors.title = 'Property title is required'
        if (!propertyData.address.trim()) newErrors.address = 'Address is required'
        if (!propertyData.city.trim()) newErrors.city = 'City is required'
        if (!propertyData.state.trim()) newErrors.state = 'State is required'
        if (!propertyData.property_type) newErrors.property_type = 'Property type is required'
        break
      case 'details':
        if (propertyData.bedrooms < 0) newErrors.bedrooms = 'Bedrooms cannot be negative'
        if (propertyData.bathrooms < 0) newErrors.bathrooms = 'Bathrooms cannot be negative'
        if (propertyData.max_guests < 1) newErrors.max_guests = 'Must accommodate at least 1 guest'
        break
      case 'pricing':
        if (propertyData.price_per_night < 1) newErrors.price_per_night = 'Price must be at least $1'
        if (!propertyData.description.trim()) newErrors.description = 'Description is required'
        break
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const nextStep = () => {
    if (validateStep(currentStep)) {
      const nextIndex = currentStepIndex + 1
      if (nextIndex < steps.length) {
        setCurrentStep(steps[nextIndex].id as WizardStep)
      }
    }
  }

  const prevStep = () => {
    const prevIndex = currentStepIndex - 1
    if (prevIndex >= 0) {
      setCurrentStep(steps[prevIndex].id as WizardStep)
    }
  }

  const handleImageUpload = async () => {
    // Create a file input element
    const input = document.createElement('input')
    input.type = 'file'
    input.multiple = true
    input.accept = 'image/*'
    
    input.onchange = async (e) => {
      const files = (e.target as HTMLInputElement).files
      if (files && files.length > 0) {
        setIsUploadingImages(true)
        setErrors(prev => ({ ...prev, images: '' }))
        
        try {
          console.log('Starting upload of', files.length, 'files')
          const uploadResults = await uploadMultipleImages(files, 'properties')
          
          const successfulUploads = uploadResults
            .filter(result => result.success && result.url)
            .map(result => result.url!)
          
          const failedUploads = uploadResults.filter(result => !result.success)
          
          if (successfulUploads.length > 0) {
            setPropertyData(prev => ({
              ...prev,
              images: [...prev.images, ...successfulUploads].slice(0, 10) // Limit to 10 images
            }))
            console.log('Successfully uploaded', successfulUploads.length, 'images')
          }
          
          if (failedUploads.length > 0) {
            const errorMsg = `Failed to upload ${failedUploads.length} image(s). ${failedUploads[0]?.error || 'Unknown error'}`
            setErrors(prev => ({ ...prev, images: errorMsg }))
            console.error('Upload failures:', failedUploads)
          }
        } catch (error: any) {
          console.error('Upload error:', error)
          setErrors(prev => ({ ...prev, images: 'Failed to upload images. Please try again.' }))
        } finally {
          setIsUploadingImages(false)
        }
      }
    }
    
    input.click()
  }

  const removeImage = (index: number) => {
    setPropertyData(prev => ({
      ...prev,
      images: prev.images.filter((_, i) => i !== index)
    }))
  }

  const toggleAmenity = (amenity: string) => {
    setPropertyData(prev => ({
      ...prev,
      amenities: prev.amenities.includes(amenity)
        ? prev.amenities.filter(a => a !== amenity)
        : [...prev.amenities, amenity]
    }))
  }

  const generateDescription = async () => {
    setIsGeneratingDescription(true)
    try {
      console.log('Generating AI description with data:', propertyData)
      const description = await generateAIDescription({
        property_type: propertyData.property_type,
        city: propertyData.city,
        state: propertyData.state,
        bedrooms: propertyData.bedrooms,
        bathrooms: propertyData.bathrooms,
        max_guests: propertyData.max_guests,
        amenities: propertyData.amenities,
        address: propertyData.address
      })
      console.log('Generated description:', description)
      setPropertyData(prev => ({ ...prev, description }))
    } catch (error: any) {
      console.error('Failed to generate description:', error)
      console.error('Error details:', error.message, error.status)
      // Fallback to a simple description
      const fallbackDescription = `Beautiful ${propertyData.property_type.toLowerCase()} in ${propertyData.city}, ${propertyData.state}. This ${propertyData.bedrooms}-bedroom property can accommodate up to ${propertyData.max_guests} guests. Perfect for your next getaway!`
      setPropertyData(prev => ({ ...prev, description: fallbackDescription }))
    } finally {
      setIsGeneratingDescription(false)
    }
  }

  const handlePublish = async () => {
    setIsPublishing(true)
    setErrors({})
    
    try {
      console.log('Publishing property with data:', propertyData)
      
      const propertyPayload = {
        title: propertyData.title,
        address: propertyData.address,
        city: propertyData.city,
        state: propertyData.state,
        country: propertyData.country,
        property_type: propertyData.property_type,
        bedrooms: propertyData.bedrooms,
        bathrooms: propertyData.bathrooms,
        max_guests: propertyData.max_guests,
        price_per_night: propertyData.price_per_night,
        description: propertyData.description,
        images: propertyData.images,
        amenities: propertyData.amenities,
        status: 'active' as const
      }

      console.log('Sending payload to backend:', propertyPayload)
      const createdProperty = await createProperty(propertyPayload)
      console.log('Property created successfully:', createdProperty)
      
      if (createdProperty) {
        setCurrentStep('published')
      } else {
        setErrors({ general: 'Failed to create property. Please try again.' })
      }
    } catch (error: any) {
      console.error('Error creating property:', error)
      setErrors({ 
        general: error.message || 'Failed to create property. Please check your connection and try again.' 
      })
    } finally {
      setIsPublishing(false)
    }
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 'basic-info':
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Let's start with the basics</h2>
              <p className="text-gray-600">Tell us about your property</p>
            </div>
            
            <div className="grid gap-6 md:grid-cols-2">
              <div className="md:col-span-2">
                <Label htmlFor="title">Property Title *</Label>
                  <Input 
                    id="title"
                    placeholder="e.g., Cozy Downtown Apartment"
                    value={propertyData.title}
                    onChange={(e) => setPropertyData(prev => ({ ...prev, title: e.target.value }))}
                  className={`input-enhanced ${errors.title ? 'border-red-500' : ''}`}
                  />
                {errors.title && <p className="text-red-500 text-sm mt-1">{errors.title}</p>}
                </div>
              
              <div className="md:col-span-2">
                <Label htmlFor="address">Address *</Label>
                  <Input 
                  id="address"
                  placeholder="123 Main Street"
                  value={propertyData.address}
                  onChange={(e) => setPropertyData(prev => ({ ...prev, address: e.target.value }))}
                  className={errors.address ? 'border-red-500' : ''}
                />
                {errors.address && <p className="text-red-500 text-sm mt-1">{errors.address}</p>}
              </div>
              
              <div>
                <Label htmlFor="state">Emirate *</Label>
                <Select value={propertyData.state} onValueChange={handleEmirateChange}>
                  <SelectTrigger className={errors.state ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select Emirate" />
                    </SelectTrigger>
                    <SelectContent>
                    {uaeEmirates.map((emirate) => (
                      <SelectItem key={emirate.value} value={emirate.value}>
                        {emirate.label}
                      </SelectItem>
                    ))}
                    </SelectContent>
                  </Select>
                {errors.state && <p className="text-red-500 text-sm mt-1">{errors.state}</p>}
                </div>
              
              <div>
                <Label htmlFor="city">Area/City *</Label>
                <Select 
                  value={propertyData.city} 
                  onValueChange={(value) => setPropertyData(prev => ({ ...prev, city: value }))}
                  disabled={!propertyData.state || isLoadingAreas}
                >
                  <SelectTrigger className={errors.city ? 'border-red-500' : ''}>
                    <SelectValue placeholder={
                      !propertyData.state ? "Select Emirate first" : 
                      isLoadingAreas ? "Loading areas..." : 
                      "Select Area/City"
                    } />
                    </SelectTrigger>
                    <SelectContent>
                    {availableAreas.map((area) => (
                      <SelectItem key={area} value={area}>
                        {area}
                      </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                {errors.city && <p className="text-red-500 text-sm mt-1">{errors.city}</p>}
                </div>
              
              <div>
                <Label htmlFor="country">Country</Label>
                <Select value={propertyData.country} onValueChange={(value) => setPropertyData(prev => ({ ...prev, country: value }))}>
                    <SelectTrigger>
                    <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                    <SelectItem value="UAE">United Arab Emirates 🇦🇪</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              
              <div>
                <Label htmlFor="property_type">Property Type *</Label>
                <Select value={propertyData.property_type} onValueChange={(value) => setPropertyData(prev => ({ ...prev, property_type: value }))}>
                  <SelectTrigger className={errors.property_type ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                    {Object.entries(uaePropertyTypes).map(([key, label]) => (
                      <SelectItem key={key} value={key}>
                        {label as string}
                      </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                {errors.property_type && <p className="text-red-500 text-sm mt-1">{errors.property_type}</p>}
              </div>
            </div>
                </div>
        )

      case 'details':
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Property Details</h2>
              <p className="text-gray-600">Help guests understand your space</p>
              </div>
              
            <div className="grid gap-6 md:grid-cols-3">
              <div>
                <Label htmlFor="bedrooms">Bedrooms</Label>
                <Input 
                  id="bedrooms"
                  type="number"
                  min="0"
                  value={propertyData.bedrooms}
                  onChange={(e) => setPropertyData(prev => ({ ...prev, bedrooms: parseInt(e.target.value) || 0 }))}
                  className={errors.bedrooms ? 'border-red-500' : ''}
                />
                {errors.bedrooms && <p className="text-red-500 text-sm mt-1">{errors.bedrooms}</p>}
              </div>
              
              <div>
                <Label htmlFor="bathrooms">Bathrooms</Label>
                <Input
                  id="bathrooms"
                  type="number"
                  min="0"
                  step="0.5"
                  value={propertyData.bathrooms}
                  onChange={(e) => setPropertyData(prev => ({ ...prev, bathrooms: parseFloat(e.target.value) || 0 }))}
                  className={errors.bathrooms ? 'border-red-500' : ''}
                />
                {errors.bathrooms && <p className="text-red-500 text-sm mt-1">{errors.bathrooms}</p>}
              </div>
              
              <div>
                <Label htmlFor="max_guests">Max Guests</Label>
                <Input
                  id="max_guests"
                  type="number"
                  min="1"
                  value={propertyData.max_guests}
                  onChange={(e) => setPropertyData(prev => ({ ...prev, max_guests: parseInt(e.target.value) || 1 }))}
                  className={errors.max_guests ? 'border-red-500' : ''}
                />
                {errors.max_guests && <p className="text-red-500 text-sm mt-1">{errors.max_guests}</p>}
                  </div>
                  </div>
                </div>
        )

      case 'images':
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Add Photos</h2>
              <p className="text-gray-600">Show off your space with beautiful photos</p>
            </div>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <Camera className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Upload Photos</h3>
              <p className="text-gray-600 mb-4">Add up to 10 high-quality photos of your property</p>
              <Button onClick={handleImageUpload} size="lg" disabled={isUploadingImages} className="krib-button-primary">
                    <Upload className="h-4 w-4 mr-2" />
                {isUploadingImages ? 'Uploading...' : 'Choose Photos'}
                  </Button>
              {errors.images && <p className="text-red-500 text-sm mt-2">{errors.images}</p>}
                </div>
            
            {propertyData.images.length > 0 && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {propertyData.images.map((image, index) => (
                  <div key={index} className="relative group">
                        <img 
                          src={image} 
                          alt={`Property ${index + 1}`}
                          className="w-full h-32 object-cover rounded-lg"
                        />
                    <button
                      onClick={() => removeImage(index)}
                      className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="h-4 w-4" />
                    </button>
                      </div>
                    ))}
                  </div>
            )}
                </div>
        )

      case 'amenities':
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Amenities</h2>
              <p className="text-gray-600">What does your property offer?</p>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {uaeAmenities.map((amenity) => (
                <div
                  key={amenity}
                  onClick={() => toggleAmenity(amenity)}
                  className={`p-3 border rounded-lg cursor-pointer transition-all ${
                    propertyData.amenities.includes(amenity)
                      ? 'border-krib-lime bg-krib-lime-soft text-krib-black'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Checkbox 
                      checked={propertyData.amenities.includes(amenity)}
                      onChange={() => {}} // Controlled by div onClick
                    />
                    <span className="text-sm font-medium">{amenity}</span>
                  </div>
                  </div>
                ))}
              </div>
          </div>
        )

      case 'pricing':
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Set Your Price</h2>
              <p className="text-gray-600">How much do you want to charge per night?</p>
            </div>
            
            <div className="max-w-md mx-auto">
              <Label htmlFor="price_per_night">Price per Night (AED)</Label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">AED</span>
                <Input
                  id="price_per_night"
                  type="number"
                  min="1"
                  value={propertyData.price_per_night}
                  onChange={(e) => setPropertyData(prev => ({ ...prev, price_per_night: parseInt(e.target.value) || 1 }))}
                  className={`pl-14 text-lg ${errors.price_per_night ? 'border-red-500' : ''}`}
                />
              </div>
              {errors.price_per_night && <p className="text-red-500 text-sm mt-1">{errors.price_per_night}</p>}
              </div>
              
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label htmlFor="description">Description</Label>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={generateDescription}
                  disabled={isGeneratingDescription}
                  className="h-10 px-4 rounded-xl border-2 border-krib-lime text-krib-lime hover:bg-krib-lime hover:text-krib-black transition-all duration-200 font-medium shadow-sm hover:shadow-md group"
                >
                  {isGeneratingDescription ? (
                    <div className="flex items-center">
                      <div className="animate-spin h-4 w-4 border-2 border-krib-lime border-t-transparent rounded-full mr-2"></div>
                      Generating...
                    </div>
                  ) : (
                    <div className="flex items-center">
                      <Bot className="h-4 w-4 mr-2 group-hover:scale-110 transition-transform duration-200" />
                      ✨ AI Generate
                    </div>
                  )}
                </Button>
              </div>
              <Textarea
                id="description"
                placeholder="Describe your property..."
                value={propertyData.description}
                onChange={(e) => setPropertyData(prev => ({ ...prev, description: e.target.value }))}
                rows={6}
                className={errors.description ? 'border-red-500' : ''}
              />
              {errors.description && <p className="text-red-500 text-sm mt-1">{errors.description}</p>}
            </div>
          </div>
        )

      case 'preview':
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Review Your Listing</h2>
              <p className="text-gray-600">Make sure everything looks perfect</p>
            </div>
            
            {errors.general && (
              <Alert className="mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{errors.general}</AlertDescription>
              </Alert>
            )}
            
            <Card className="krib-card">
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-xl font-bold">{propertyData.title}</h3>
                    <p className="text-gray-600">{propertyData.address}, {propertyData.city}, {propertyData.state}</p>
                  </div>
                  
                  <div className="flex gap-4 text-sm text-gray-600">
                    <span>{propertyData.bedrooms} bed</span>
                    <span>{propertyData.bathrooms} bath</span>
                    <span>{propertyData.max_guests} guests</span>
                    <span className="font-bold text-gray-900">AED {propertyData.price_per_night}/night</span>
                  </div>
                  
                  {propertyData.images.length > 0 && (
                    <div className="grid grid-cols-3 gap-2">
                      {propertyData.images.slice(0, 3).map((image, index) => (
                        <img 
                          key={index}
                          src={image} 
                          alt={`Property ${index + 1}`}
                          className="w-full h-24 object-cover rounded"
                        />
                      ))}
                    </div>
                  )}
                  
                  <p className="text-gray-700">{propertyData.description}</p>
                  
                  {propertyData.amenities.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Amenities</h4>
                    <div className="flex flex-wrap gap-2">
                        {propertyData.amenities.map((amenity) => (
                        <Badge key={amenity} variant="secondary">{amenity}</Badge>
                      ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )

      case 'published':
        return (
          <div className="text-center space-y-6">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <Check className="h-10 w-10 text-green-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">🎉 Property Published!</h2>
              <p className="text-gray-600">Your property is now live and ready to receive bookings.</p>
              </div>
            <div className="space-y-3">
              <Button 
                onClick={() => setCurrentStep('basic-info')} 
                variant="outline"
                className="w-full h-12 rounded-xl border-2 hover:bg-gray-50"
              >
                  Add Another Property
                </Button>
              <Button 
                onClick={() => navigate('/properties')}
                className="w-full h-12 rounded-xl krib-button-primary"
              >
                View My Properties
                </Button>
              </div>
          </div>
        )

      default:
        return null
    }
  }

  if (currentStep === 'published') {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        {renderStepContent()}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Add New Property</h1>
        <p className="text-gray-600">Create a stunning listing for your rental property</p>
      </div>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                index <= currentStepIndex 
                  ? 'bg-krib-lime text-krib-black' 
                  : 'bg-gray-200 text-gray-500'
              }`}>
                <step.icon className="h-5 w-5" />
              </div>
              {index < steps.length - 1 && (
                <div className={`w-16 h-1 mx-2 ${
                  index < currentStepIndex ? 'bg-krib-lime' : 'bg-gray-200'
                }`} />
              )}
            </div>
          ))}
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-600">
            Step {currentStepIndex + 1} of {steps.length}: {steps[currentStepIndex]?.description}
          </p>
        </div>
      </div>

      {/* Step Content */}
      <Card className="mb-8 card-elevated">
        <CardContent className="p-8 form-section">
          {renderStepContent()}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button 
          variant="outline" 
          onClick={prevStep}
          disabled={currentStepIndex === 0}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Previous
        </Button>
        
        <div className="flex gap-2">
          {currentStepIndex === steps.length - 1 ? (
            <Button 
              onClick={handlePublish}
              disabled={isPublishing}
              size="lg"
              className="px-8 krib-button-primary"
            >
              {isPublishing ? 'Publishing...' : 'Publish Property'}
            </Button>
          ) : (
            <Button onClick={nextStep} size="lg" className="px-8 krib-button-primary">
              Next
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}