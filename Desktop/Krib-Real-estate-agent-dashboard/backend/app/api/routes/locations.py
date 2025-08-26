"""
UAE Locations API endpoints
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from app.constants.uae_locations import (
    get_all_emirates, 
    get_emirate_areas, 
    get_popular_locations,
    get_uae_amenities,
    get_uae_property_types,
    UAE_EMIRATES
)

router = APIRouter()

@router.get("/emirates", response_model=List[Dict[str, str]])
async def get_emirates():
    """Get all UAE emirates"""
    return get_all_emirates()

@router.get("/emirates/{emirate}/areas", response_model=List[str])
async def get_areas_by_emirate(emirate: str):
    """Get all areas for a specific emirate"""
    areas = get_emirate_areas(emirate)
    if not areas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emirate '{emirate}' not found"
        )
    return areas

@router.get("/popular", response_model=List[str])
async def get_popular_uae_locations():
    """Get most popular UAE locations for autocomplete"""
    return get_popular_locations()

@router.get("/amenities", response_model=List[str])
async def get_uae_specific_amenities():
    """Get UAE-specific amenities"""
    return get_uae_amenities()

@router.get("/property-types", response_model=Dict[str, str])
async def get_uae_property_types_endpoint():
    """Get UAE property types"""
    return get_uae_property_types()

@router.get("/search")
async def search_locations(q: str = ""):
    """Search for locations across all emirates"""
    if not q or len(q) < 2:
        return {"suggestions": get_popular_locations()[:20]}
    
    query_lower = q.lower()
    suggestions = []
    
    # Search through all emirates and areas
    for emirate_name, emirate_data in UAE_EMIRATES.items():
        # Check if emirate name matches
        if query_lower in emirate_name.lower():
            suggestions.append({
                "type": "emirate",
                "name": emirate_name,
                "full_name": f"{emirate_name}, UAE",
                "emirate": emirate_name,
                "area": None
            })
        
        # Check areas within emirate
        for area in emirate_data["major_areas"]:
            if query_lower in area.lower():
                suggestions.append({
                    "type": "area",
                    "name": area,
                    "full_name": f"{area}, {emirate_name}, UAE",
                    "emirate": emirate_name,
                    "area": area
                })
    
    # Limit results and sort by relevance
    suggestions = suggestions[:15]
    
    return {"suggestions": suggestions}

@router.get("/validate")
async def validate_location(emirate: str, area: str = None):
    """Validate if a location combination is valid"""
    if emirate not in UAE_EMIRATES:
        return {
            "valid": False,
            "error": f"Invalid emirate. Available: {', '.join(UAE_EMIRATES.keys())}"
        }
    
    if area:
        valid_areas = UAE_EMIRATES[emirate]["major_areas"]
        if area not in valid_areas:
            return {
                "valid": False,
                "error": f"Area '{area}' not found in {emirate}",
                "suggestions": [a for a in valid_areas if area.lower() in a.lower()][:5]
            }
    
    return {"valid": True}

@router.get("/nearby/{emirate}/{area}")
async def get_nearby_amenities(emirate: str, area: str):
    """Get nearby amenities for a specific area (placeholder for future Google Places integration)"""
    if emirate not in UAE_EMIRATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emirate not found"
        )
    
    areas = UAE_EMIRATES[emirate]["major_areas"]
    if area not in areas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found in specified emirate"
        )
    
    # Placeholder response - will be enhanced with Google Places API
    nearby_amenities = {
        "shopping": ["Mall", "Supermarket", "Retail Center"],
        "transport": ["Metro Station", "Bus Stop", "Taxi Stand"],
        "healthcare": ["Hospital", "Clinic", "Pharmacy"],
        "education": ["School", "University", "Training Center"],
        "recreation": ["Park", "Beach", "Gym", "Restaurant"]
    }
    
    return {
        "location": f"{area}, {emirate}, UAE",
        "nearby": nearby_amenities,
        "note": "Enhanced with Google Places API integration coming soon"
    }
