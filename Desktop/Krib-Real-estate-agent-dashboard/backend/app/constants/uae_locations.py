# UAE Location Constants
# Comprehensive Emirates and Cities data for the property system

UAE_EMIRATES = {
    "Dubai": {
        "name": "Dubai",
        "name_ar": "دبي",
        "code": "DXB",
        "major_areas": [
            "Downtown Dubai", "Dubai Marina", "Jumeirah Beach Residence (JBR)",
            "Business Bay", "Dubai Investment Park", "Jumeirah", "Deira", 
            "Bur Dubai", "Dubai Hills Estate", "Arabian Ranches", "Dubai South",
            "Palm Jumeirah", "The Greens", "Emirates Hills", "Al Barsha",
            "International City", "Discovery Gardens", "Jumeirah Village Circle (JVC)",
            "Jumeirah Village Triangle (JVT)", "Motor City", "Sports City",
            "Dubai Silicon Oasis", "Dubai Studio City", "Academic City",
            "Healthcare City", "Internet City", "Media City", "Knowledge Village",
            "Al Furjan", "The Springs", "The Meadows", "The Lakes",
            "Mirdif", "Festival City", "Culture Village", "Old Town",
            "DIFC (Dubai International Financial Centre)", "City Walk",
            "Al Khail Gate", "Town Square", "Akoya Oxygen", "Damac Hills",
            "Dubai Land", "Mudon", "Serena", "Villanova", "Reem", "Mag 5 Boulevard"
        ]
    },
    "Abu Dhabi": {
        "name": "Abu Dhabi",
        "name_ar": "أبو ظبي",
        "code": "AUH",
        "major_areas": [
            "Abu Dhabi City", "Al Ain", "Liwa Oasis", "Khalifa City",
            "Al Raha", "Yas Island", "Saadiyat Island", "Al Reef",
            "Masdar City", "Corniche", "Tourist Club Area", "Hamdan Street",
            "Electra Street", "Al Zahiyah", "Al Markaziyah", "Al Bateen",
            "Al Karamah", "Shakhbout City", "Mohammed Bin Zayed City",
            "Khalifa City A", "Al Raha Beach", "Yas Acres", "West Yas",
            "Bloom Gardens", "The Gate District", "Reem Island", "Al Maryah Island",
            "Sowwah Island", "Hudayriyat Island", "Al Shamkha", "Al Wathba",
            "Baniyas", "Al Dhafra", "Madinat Zayed", "Mirfa", "Ruwais",
            "Al Sila", "Ghayathi", "Gayathi", "Habshan", "Shah"
        ]
    },
    "Sharjah": {
        "name": "Sharjah",
        "name_ar": "الشارقة",
        "code": "SHJ",
        "major_areas": [
            "Sharjah City", "Kalba", "Khorfakkan", "Dibba Al-Hisn",
            "Al Dhaid", "Mleiha", "Al Madam", "Al Qasimia", "Al Majaz",
            "Al Nahda", "Al Taawun", "Al Ghubaiba", "Al Qasba", "Al Khan",
            "Al Mamzar", "Al Fisht", "Al Rolla", "King Faisal Street",
            "Al Nud", "Industrial Area", "Muwailih", "Al Ramtha", "Tilal City",
            "University City", "Al Rahmaniya", "Al Jurf", "Al Saja",
            "Al Sajaa", "Wasit", "Al Batayeh", "Hamriyah", "Al Hamriyah Port"
        ]
    },
    "Ajman": {
        "name": "Ajman",
        "name_ar": "عجمان",
        "code": "AJM",
        "major_areas": [
            "Ajman City", "Al Nuaimiya", "Al Rawda", "Al Jurf", "Al Tallah",
            "Al Rashidiya", "Al Helio", "Al Manama", "Corniche Road",
            "Sheikh Rashid Street", "Industrial Area", "New Industrial Area",
            "Ajman Marina", "Al Zorah", "Masfout", "Al Hamidiyah"
        ]
    },
    "Ras Al Khaimah": {
        "name": "Ras Al Khaimah",
        "name_ar": "رأس الخيمة",
        "code": "RAK",
        "major_areas": [
            "Ras Al Khaimah City", "Al Hamra", "Al Marjan Island", "Al Rams",
            "Digdaga", "Al Jeer", "Al Qusaidat", "Khuzam", "Al Nakheel",
            "Corniche Road", "Al Muntasir", "Al Mamoura", "Al Seer",
            "Mina Al Arab", "Al Dhait", "Khatt", "Masafi", "Wadi Bih",
            "Shaam", "Ghalilah", "Khor Khwair"
        ]
    },
    "Fujairah": {
        "name": "Fujairah",
        "name_ar": "الفجيرة",
        "code": "FUJ",
        "major_areas": [
            "Fujairah City", "Dibba", "Kalba", "Khor Fakkan", "Al Bidiyah",
            "Masafi", "Al Hayl", "Al Aqah", "Al Fujairah Corniche",
            "Al Gurfa", "Mirbah", "Qidfa", "Sakamkam", "Al Taybah", "Madhab"
        ]
    },
    "Umm Al Quwain": {
        "name": "Umm Al Quwain",
        "name_ar": "أم القيوين",
        "code": "UAQ",
        "major_areas": [
            "Umm Al Quwain City", "Al Salam City", "Falaj Al Mualla",
            "Ras Al Khaimah Road", "Al Rashid", "Al Maydaq", "Al Sinniyah Island",
            "Al Khor", "Dreamland Aqua Park Area"
        ]
    }
}

# Most popular cities/areas for real estate
POPULAR_UAE_LOCATIONS = [
    # Dubai
    "Downtown Dubai", "Dubai Marina", "Jumeirah Beach Residence (JBR)",
    "Business Bay", "Palm Jumeirah", "Jumeirah", "Arabian Ranches",
    "Dubai Hills Estate", "City Walk", "DIFC", "Al Barsha", "The Greens",
    
    # Abu Dhabi
    "Abu Dhabi City", "Yas Island", "Saadiyat Island", "Al Reem Island",
    "Khalifa City", "Al Raha", "Masdar City", "Corniche", "Al Maryah Island",
    
    # Sharjah
    "Sharjah City", "Al Majaz", "Al Nahda", "Al Khan", "Al Qasba",
    
    # Others
    "Ajman City", "Ras Al Khaimah City", "Fujairah City", "Umm Al Quwain City"
]

# UAE-specific property features and amenities
UAE_SPECIFIC_AMENITIES = [
    "Central Air Conditioning", "Maid's Room", "Driver's Room", "Laundry Room",
    "Built-in Wardrobes", "Floor-to-Ceiling Windows", "Walk-in Closet",
    "Marble Floors", "Covered Parking", "Visitor Parking", "24/7 Security",
    "Concierge Service", "Valet Parking", "Housekeeping", "Children's Play Area",
    "BBQ Area", "Shared Pool", "Private Pool", "Jacuzzi", "Steam Room",
    "Sauna", "Mosque Nearby", "School Nearby", "Hospital Nearby",
    "Metro Station Nearby", "Mall Nearby", "Beach Access", "Golf Course View",
    "Burj Khalifa View", "Sea View", "City View", "Park View", "Pool View",
    "Fountain View", "Marina View", "Garden View", "Partial Sea View"
]

# Property types specific to UAE market
UAE_PROPERTY_TYPES = {
    "apartment": "Apartment",
    "villa": "Villa", 
    "townhouse": "Townhouse",
    "penthouse": "Penthouse",
    "studio": "Studio",
    "duplex": "Duplex",
    "loft": "Loft",
    "compound": "Compound",
    "chalet": "Chalet",
    "bulk_unit": "Bulk Sale Unit",
    "hotel_apartment": "Hotel Apartment",
    "whole_building": "Whole Building",
    "warehouse": "Warehouse",
    "office": "Office",
    "retail": "Retail Space",
    "land": "Land/Plot"
}

def get_emirate_areas(emirate_name: str) -> list:
    """Get all areas for a specific emirate"""
    emirate = UAE_EMIRATES.get(emirate_name)
    return emirate["major_areas"] if emirate else []

def get_all_emirates() -> list:
    """Get list of all emirates"""
    return [{"value": name, "label": data["name"], "label_ar": data["name_ar"]} 
            for name, data in UAE_EMIRATES.items()]

def validate_uae_location(emirate: str, area: str) -> bool:
    """Validate if the area exists in the specified emirate"""
    if emirate not in UAE_EMIRATES:
        return False
    return area in UAE_EMIRATES[emirate]["major_areas"]

def get_popular_locations() -> list:
    """Get most popular UAE locations for autocomplete"""
    return POPULAR_UAE_LOCATIONS

def get_uae_amenities() -> list:
    """Get UAE-specific amenities"""
    return UAE_SPECIFIC_AMENITIES

def get_uae_property_types() -> dict:
    """Get UAE property types"""
    return UAE_PROPERTY_TYPES
