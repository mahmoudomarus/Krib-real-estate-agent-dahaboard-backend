import { useState, useEffect } from "react"
import { Search, Filter, Edit, Eye, Trash2, MapPin, Star, Building2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Input } from "./ui/input"
import { Button } from "./ui/button"
import { Badge } from "./ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog"
import { Textarea } from "./ui/textarea"
import { Label } from "./ui/label"
import { ImageWithFallback } from "./figma/ImageWithFallback"
import { useApp } from "../contexts/AppContext"

// Property type inferred from the context
type Property = NonNullable<ReturnType<typeof useApp>['properties'][0]>

export function PropertyList() {
  const { properties, loadProperties, deleteProperty, updateProperty } = useApp()
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null)
  const [isViewModalOpen, setIsViewModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [editFormData, setEditFormData] = useState<Partial<Property>>({})

  useEffect(() => {
    loadProperties()
  }, [])

  const filteredProperties = properties.filter(property => {
    const matchesSearch = property.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         property.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         property.state.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === "all" || property.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-gray-100 text-gray-800'
      case 'draft': return 'bg-yellow-100 text-yellow-800'
      case 'suspended': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const handleViewProperty = (property: Property) => {
    setSelectedProperty(property)
    setIsViewModalOpen(true)
  }

  const handleEditProperty = (property: Property) => {
    setSelectedProperty(property)
    setEditFormData({
      title: property.title,
      description: property.description,
      price_per_night: property.price_per_night,
      bedrooms: property.bedrooms,
      bathrooms: property.bathrooms,
      max_guests: property.max_guests,
      status: property.status
    })
    setIsEditModalOpen(true)
  }

  const handleUpdateProperty = async () => {
    if (!selectedProperty) return
    
    try {
      await updateProperty(selectedProperty.id, editFormData)
      setIsEditModalOpen(false)
      setSelectedProperty(null)
      setEditFormData({})
    } catch (error) {
      console.error('Failed to update property:', error)
    }
  }

  const handleDeleteProperty = async (propertyId: string) => {
    if (confirm('Are you sure you want to delete this property?')) {
      try {
        await deleteProperty(propertyId)
      } catch (error) {
        console.error('Failed to delete property:', error)
      }
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1>Properties</h1>
        <p className="text-muted-foreground">
          Manage your rental properties and track their performance.
        </p>
      </div>

      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search properties..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-4">
        {filteredProperties.map((property) => (
          <Card key={property.id} className="p-6 krib-card krib-glow-hover">
            <div className="flex items-center gap-6">
              {/* Property Image */}
              <div className="w-32 h-24 relative flex-shrink-0">
                <ImageWithFallback
                  src={property.images && property.images.length > 0 && !property.images[0].startsWith('blob:') 
                    ? property.images[0] 
                    : "/placeholder-property.jpg"}
                  alt={property.title}
                  className="object-cover w-full h-full rounded-lg"
                />
                {property.images && property.images[0] && property.images[0].startsWith('blob:') && (
                  <div className="absolute bottom-1 left-1 bg-yellow-100 text-yellow-800 text-xs px-1 py-0.5 rounded text-[10px]">
                    Image Issue
                  </div>
                )}
              </div>

              {/* Property Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lg truncate">{property.title}</h3>
                      <Badge className={getStatusColor(property.status)}>
                        {property.status.charAt(0).toUpperCase() + property.status.slice(1)}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center text-muted-foreground mb-2">
                      <MapPin className="h-4 w-4 mr-1" />
                      <span className="text-sm">{property.city}, {property.state}</span>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
                      <span>{property.bedrooms} bed</span>
                      <span>{property.bathrooms} bath</span>
                      <span>{property.max_guests} guests</span>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="flex items-baseline">
                        <span className="font-bold text-lg text-green-600">${property.price_per_night}</span>
                        <span className="text-muted-foreground text-sm ml-1">/night</span>
                      </div>
                      {property.rating && (
                        <div className="flex items-center">
                          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                          <span className="ml-1 text-sm font-medium">{property.rating}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 ml-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewProperty(property)}
                      className="h-8"
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      View
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEditProperty(property)}
                      className="h-8"
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteProperty(property.id)}
                      className="h-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {filteredProperties.length === 0 && (
        <Card className="p-12 krib-card">
          <div className="text-center">
            <Building2 className="h-16 w-16 mx-auto text-muted-foreground mb-6" />
            <h3 className="text-xl font-semibold mb-3">No properties found</h3>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              {properties.length === 0 
                ? "You haven't created any properties yet. Get started by adding your first property to begin managing your rentals!" 
                : "Try adjusting your search terms or filter criteria to find the properties you're looking for."}
            </p>
            {properties.length === 0 && (
              <Button size="lg" className="bg-primary hover:bg-primary/90">
                <Building2 className="h-5 w-5 mr-2" />
                Add Your First Property
              </Button>
            )}
          </div>
        </Card>
      )}

      {/* View Property Modal */}
      <Dialog open={isViewModalOpen} onOpenChange={setIsViewModalOpen}>
        <DialogContent className="max-w-2xl bg-white border shadow-lg">
          <DialogHeader className="pb-4 border-b">
            <DialogTitle className="text-xl font-semibold text-gray-900">Property Details</DialogTitle>
          </DialogHeader>
          {selectedProperty && (
            <div className="space-y-6 p-6 bg-gray-50 rounded-lg">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-md border">
                  <Label className="font-semibold text-gray-700">Title</Label>
                  <p className="text-gray-900 mt-1">{selectedProperty.title}</p>
                </div>
                <div className="bg-white p-4 rounded-md border">
                  <Label className="font-semibold text-gray-700">Status</Label>
                  <div className="mt-1">
                    <Badge className={getStatusColor(selectedProperty.status)}>
                      {selectedProperty.status.charAt(0).toUpperCase() + selectedProperty.status.slice(1)}
                    </Badge>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-4 rounded-md border">
                <Label className="font-semibold text-gray-700">Description</Label>
                <p className="text-gray-900 mt-2 leading-relaxed">{selectedProperty.description || 'No description provided'}</p>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white p-4 rounded-md border">
                  <Label className="font-semibold text-gray-700">Price per night</Label>
                  <p className="text-green-600 font-bold text-lg mt-1">${selectedProperty.price_per_night}</p>
                </div>
                <div className="bg-white p-4 rounded-md border">
                  <Label className="font-semibold text-gray-700">Bedrooms</Label>
                  <p className="text-gray-900 font-medium mt-1">{selectedProperty.bedrooms}</p>
                </div>
                <div className="bg-white p-4 rounded-md border">
                  <Label className="font-semibold text-gray-700">Bathrooms</Label>
                  <p className="text-gray-900 font-medium mt-1">{selectedProperty.bathrooms}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-md border">
                  <Label className="font-semibold text-gray-700">Max Guests</Label>
                  <p className="text-gray-900 font-medium mt-1">{selectedProperty.max_guests}</p>
                </div>
                <div className="bg-white p-4 rounded-md border">
                  <Label className="font-semibold text-gray-700">Location</Label>
                  <p className="text-gray-900 font-medium mt-1">{selectedProperty.city}, {selectedProperty.state}</p>
                </div>
              </div>

              {selectedProperty.amenities && selectedProperty.amenities.length > 0 && (
                <div className="bg-white p-4 rounded-md border">
                  <Label className="font-semibold text-gray-700">Amenities</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {selectedProperty.amenities.map((amenity, index) => (
                      <Badge key={index} variant="secondary" className="bg-blue-100 text-blue-800 hover:bg-blue-200">
                        {amenity}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Property Modal */}
      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
        <DialogContent className="max-w-2xl bg-white border shadow-lg">
          <DialogHeader className="pb-4 border-b">
            <DialogTitle className="text-xl font-semibold text-gray-900">Edit Property</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 p-6 bg-gray-50 rounded-lg">
            <div className="bg-white p-4 rounded-md border">
              <Label htmlFor="edit-title" className="font-semibold text-gray-700">Title</Label>
              <Input
                id="edit-title"
                value={editFormData.title || ''}
                onChange={(e) => setEditFormData(prev => ({ ...prev, title: e.target.value }))}
                className="mt-2 bg-white border-gray-300 focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div className="bg-white p-4 rounded-md border">
              <Label htmlFor="edit-description" className="font-semibold text-gray-700">Description</Label>
              <Textarea
                id="edit-description"
                value={editFormData.description || ''}
                onChange={(e) => setEditFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
                className="mt-2 bg-white border-gray-300 focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white p-4 rounded-md border">
                <Label htmlFor="edit-price" className="font-semibold text-gray-700">Price per night ($)</Label>
                <Input
                  id="edit-price"
                  type="number"
                  value={editFormData.price_per_night || ''}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, price_per_night: Number(e.target.value) }))}
                  className="mt-2 bg-white border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div className="bg-white p-4 rounded-md border">
                <Label htmlFor="edit-status" className="font-semibold text-gray-700">Status</Label>
                <Select
                  value={editFormData.status || ''}
                  onValueChange={(value) => setEditFormData(prev => ({ ...prev, status: value as any }))}
                >
                  <SelectTrigger className="mt-2 bg-white border-gray-300 focus:border-blue-500 focus:ring-blue-500">
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent className="bg-white border shadow-lg">
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                    <SelectItem value="suspended">Suspended</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white p-4 rounded-md border">
                <Label htmlFor="edit-bedrooms" className="font-semibold text-gray-700">Bedrooms</Label>
                <Input
                  id="edit-bedrooms"
                  type="number"
                  min="1"
                  value={editFormData.bedrooms || ''}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, bedrooms: Number(e.target.value) }))}
                  className="mt-2 bg-white border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div className="bg-white p-4 rounded-md border">
                <Label htmlFor="edit-bathrooms" className="font-semibold text-gray-700">Bathrooms</Label>
                <Input
                  id="edit-bathrooms"
                  type="number"
                  min="1"
                  value={editFormData.bathrooms || ''}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, bathrooms: Number(e.target.value) }))}
                  className="mt-2 bg-white border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div className="bg-white p-4 rounded-md border">
                <Label htmlFor="edit-max-guests" className="font-semibold text-gray-700">Max Guests</Label>
                <Input
                  id="edit-max-guests"
                  type="number"
                  min="1"
                  value={editFormData.max_guests || ''}
                  onChange={(e) => setEditFormData(prev => ({ ...prev, max_guests: Number(e.target.value) }))}
                  className="mt-2 bg-white border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-6 border-t bg-white p-4 rounded-md">
              <Button variant="outline" onClick={() => setIsEditModalOpen(false)} className="px-6">
                Cancel
              </Button>
              <Button onClick={handleUpdateProperty} className="px-6 krib-button-primary">
                Save Changes
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}