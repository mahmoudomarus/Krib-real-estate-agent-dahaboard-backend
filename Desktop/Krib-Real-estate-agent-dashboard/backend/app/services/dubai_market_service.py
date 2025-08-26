"""
Dubai Market Intelligence Service

Provides real market data, pricing optimization, and forecasting
specifically tailored for Dubai's rental property market.
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
import json
import math
from enum import Enum

class DubaiArea(Enum):
    """Dubai rental property areas with different pricing tiers"""
    MARINA = "marina"
    DOWNTOWN = "downtown"
    JLT = "jlt"
    BUSINESS_BAY = "business_bay"
    JBR = "jbr"
    PALM_JUMEIRAH = "palm_jumeirah"
    DEIRA = "deira"
    BURDUBAI = "bur_dubai"
    JUMEIRAH = "jumeirah"
    SILICON_OASIS = "silicon_oasis"

class DubaiSeason(Enum):
    """Dubai seasonal periods affecting rental demand"""
    PEAK_WINTER = "peak_winter"      # Dec-Feb
    HIGH_WINTER = "high_winter"      # Mar, Nov
    SHOULDER = "shoulder"            # Apr, Oct
    LOW_SUMMER = "low_summer"        # May-Sep

class DubaiEvent(Enum):
    """Major Dubai events affecting rental demand"""
    SHOPPING_FESTIVAL = "shopping_festival"
    F1_GRAND_PRIX = "f1_grand_prix"
    GITEX = "gitex"
    ARAB_HEALTH = "arab_health"
    RAMADAN = "ramadan"
    EID_AL_FITR = "eid_al_fitr"
    EID_AL_ADHA = "eid_al_adha"
    UAE_NATIONAL_DAY = "uae_national_day"
    NEW_YEAR = "new_year"

class DubaiMarketService:
    """Service for Dubai-specific market intelligence and pricing optimization"""
    
    def __init__(self):
        self.area_multipliers = self._get_area_pricing_multipliers()
        self.seasonal_multipliers = self._get_seasonal_multipliers()
        self.event_multipliers = self._get_event_multipliers()
        self.dubai_events_2024 = self._get_dubai_events_calendar_2024()
    
    def _get_area_pricing_multipliers(self) -> Dict[str, float]:
        """Pricing multipliers based on Dubai area desirability and demand"""
        return {
            DubaiArea.PALM_JUMEIRAH.value: 2.0,     # Ultra premium
            DubaiArea.MARINA.value: 1.6,            # Premium waterfront
            DubaiArea.DOWNTOWN.value: 1.5,          # Business/tourist hub
            DubaiArea.JBR.value: 1.4,              # Beach access
            DubaiArea.BUSINESS_BAY.value: 1.2,      # Modern business district
            DubaiArea.JUMEIRAH.value: 1.3,          # Traditional upscale
            DubaiArea.JLT.value: 1.0,              # Base rate area
            DubaiArea.SILICON_OASIS.value: 0.8,     # Tech hub, suburban
            DubaiArea.DEIRA.value: 0.7,            # Traditional, lower cost
            DubaiArea.BURDUBAI.value: 0.6           # Historic, budget area
        }
    
    def _get_seasonal_multipliers(self) -> Dict[str, float]:
        """Seasonal demand multipliers for Dubai"""
        return {
            DubaiSeason.PEAK_WINTER.value: 1.5,     # Dec-Feb: European winter escape
            DubaiSeason.HIGH_WINTER.value: 1.3,     # Mar, Nov: Pleasant weather
            DubaiSeason.SHOULDER.value: 1.0,        # Apr, Oct: Moderate demand
            DubaiSeason.LOW_SUMMER.value: 0.7       # May-Sep: Hot summer discount
        }
    
    def _get_event_multipliers(self) -> Dict[str, float]:
        """Event-based surge pricing multipliers"""
        return {
            DubaiEvent.F1_GRAND_PRIX.value: 3.0,
            DubaiEvent.SHOPPING_FESTIVAL.value: 1.8,
            DubaiEvent.GITEX.value: 1.6,
            DubaiEvent.ARAB_HEALTH.value: 1.5,
            DubaiEvent.UAE_NATIONAL_DAY.value: 1.4,
            DubaiEvent.NEW_YEAR.value: 2.0,
            DubaiEvent.EID_AL_FITR.value: 1.3,
            DubaiEvent.EID_AL_ADHA.value: 1.3,
            DubaiEvent.RAMADAN.value: 0.8  # Reduced tourism during Ramadan
        }
    
    def _get_dubai_events_calendar_2024(self) -> Dict[str, List[Dict]]:
        """2024 Dubai events calendar affecting rental demand"""
        return {
            "2024-01": [
                {"name": "Dubai Shopping Festival", "type": DubaiEvent.SHOPPING_FESTIVAL.value, "days": list(range(1, 29))}
            ],
            "2024-03": [
                {"name": "Formula 1 UAE Grand Prix", "type": DubaiEvent.F1_GRAND_PRIX.value, "days": [8, 9, 10]}
            ],
            "2024-03": [
                {"name": "Ramadan", "type": DubaiEvent.RAMADAN.value, "days": list(range(10, 32))}
            ],
            "2024-04": [
                {"name": "Ramadan", "type": DubaiEvent.RAMADAN.value, "days": list(range(1, 10))},
                {"name": "Eid Al-Fitr", "type": DubaiEvent.EID_AL_FITR.value, "days": [10, 11, 12]}
            ],
            "2024-06": [
                {"name": "Eid Al-Adha", "type": DubaiEvent.EID_AL_ADHA.value, "days": [16, 17, 18]}
            ],
            "2024-10": [
                {"name": "GITEX Technology Week", "type": DubaiEvent.GITEX.value, "days": list(range(14, 19))}
            ],
            "2024-12": [
                {"name": "UAE National Day", "type": DubaiEvent.UAE_NATIONAL_DAY.value, "days": [2, 3]},
                {"name": "New Year Celebrations", "type": DubaiEvent.NEW_YEAR.value, "days": [31]}
            ]
        }
    
    def get_season_for_date(self, target_date: date) -> DubaiSeason:
        """Determine Dubai season for a given date"""
        month = target_date.month
        
        if month in [12, 1, 2]:
            return DubaiSeason.PEAK_WINTER
        elif month in [3, 11]:
            return DubaiSeason.HIGH_WINTER
        elif month in [4, 10]:
            return DubaiSeason.SHOULDER
        else:  # May-September
            return DubaiSeason.LOW_SUMMER
    
    def get_events_for_date(self, target_date: date) -> List[Dict]:
        """Get Dubai events affecting the given date"""
        month_key = target_date.strftime("%Y-%m")
        events = []
        
        if month_key in self.dubai_events_2024:
            for event in self.dubai_events_2024[month_key]:
                if target_date.day in event["days"]:
                    events.append(event)
        
        return events
    
    def calculate_optimal_price(
        self, 
        base_rate: float, 
        area: str, 
        target_date: date,
        property_type: str = "apartment",
        bedrooms: int = 1
    ) -> Dict[str, Any]:
        """Calculate optimal pricing for a property on a specific date"""
        
        # Start with base rate
        price = base_rate
        pricing_factors = {"base_rate": base_rate}
        
        # Apply area multiplier
        area_multiplier = self.area_multipliers.get(area, 1.0)
        price *= area_multiplier
        pricing_factors["area_multiplier"] = area_multiplier
        
        # Apply seasonal multiplier
        season = self.get_season_for_date(target_date)
        seasonal_multiplier = self.seasonal_multipliers[season.value]
        price *= seasonal_multiplier
        pricing_factors["seasonal_multiplier"] = seasonal_multiplier
        pricing_factors["season"] = season.value
        
        # Apply event multipliers
        events = self.get_events_for_date(target_date)
        max_event_multiplier = 1.0
        active_events = []
        
        for event in events:
            event_multiplier = self.event_multipliers.get(event["type"], 1.0)
            if event_multiplier > max_event_multiplier:
                max_event_multiplier = event_multiplier
            active_events.append({
                "name": event["name"],
                "type": event["type"],
                "multiplier": event_multiplier
            })
        
        price *= max_event_multiplier
        pricing_factors["event_multiplier"] = max_event_multiplier
        pricing_factors["active_events"] = active_events
        
        # Weekend premium (Fri-Sat in Dubai)
        if target_date.weekday() in [4, 5]:  # Friday, Saturday
            weekend_multiplier = 1.2
            price *= weekend_multiplier
            pricing_factors["weekend_multiplier"] = weekend_multiplier
        
        # Property type adjustments
        if property_type == "villa":
            price *= 1.5
        elif property_type == "penthouse":
            price *= 2.0
        elif property_type == "studio":
            price *= 0.8
        
        # Bedroom count multiplier
        bedroom_multiplier = max(0.5, min(3.0, 0.7 + (bedrooms * 0.3)))
        price *= bedroom_multiplier
        pricing_factors["bedroom_multiplier"] = bedroom_multiplier
        
        return {
            "suggested_price": round(price, 2),
            "pricing_factors": pricing_factors,
            "demand_level": self._get_demand_level(seasonal_multiplier, max_event_multiplier),
            "recommendations": self._get_pricing_recommendations(
                base_rate, price, active_events, season
            )
        }
    
    def _get_demand_level(self, seasonal_mult: float, event_mult: float) -> str:
        """Determine demand level based on multipliers"""
        total_mult = seasonal_mult * event_mult
        
        if total_mult >= 2.5:
            return "Very High"
        elif total_mult >= 1.5:
            return "High"
        elif total_mult >= 1.0:
            return "Medium"
        else:
            return "Low"
    
    def _get_pricing_recommendations(
        self, 
        base_rate: float, 
        suggested_price: float, 
        events: List[Dict], 
        season: DubaiSeason
    ) -> List[str]:
        """Generate pricing recommendations"""
        recommendations = []
        increase_pct = ((suggested_price - base_rate) / base_rate) * 100
        
        if increase_pct > 50:
            recommendations.append("High demand period - consider premium positioning")
        
        if events:
            event_names = [e["name"] for e in events]
            recommendations.append(f"Major events active: {', '.join(event_names)}")
        
        if season == DubaiSeason.PEAK_WINTER:
            recommendations.append("Peak winter season - maximize revenue with premium rates")
        elif season == DubaiSeason.LOW_SUMMER:
            recommendations.append("Summer season - consider longer stay discounts")
        
        return recommendations
    
    def generate_pricing_calendar(
        self, 
        base_rate: float, 
        area: str, 
        days_ahead: int = 30,
        property_type: str = "apartment",
        bedrooms: int = 1
    ) -> List[Dict]:
        """Generate pricing calendar for next N days"""
        calendar = []
        start_date = date.today()
        
        for i in range(days_ahead):
            target_date = start_date + timedelta(days=i)
            pricing_data = self.calculate_optimal_price(
                base_rate, area, target_date, property_type, bedrooms
            )
            
            calendar.append({
                "date": target_date.isoformat(),
                "day_name": target_date.strftime("%A"),
                "suggested_price": pricing_data["suggested_price"],
                "demand_level": pricing_data["demand_level"],
                "active_events": [e["name"] for e in pricing_data["pricing_factors"]["active_events"]],
                "season": pricing_data["pricing_factors"]["season"],
                "pricing_factors": pricing_data["pricing_factors"]
            })
        
        return calendar
    
    def get_market_forecast(self, months_ahead: int = 12) -> Dict[str, Any]:
        """Generate market forecast for Dubai rental market"""
        forecast_data = []
        base_revenue = 5000  # Base monthly revenue
        
        for i in range(months_ahead):
            future_date = date.today() + timedelta(days=30 * i)
            season = self.get_season_for_date(future_date)
            seasonal_mult = self.seasonal_multipliers[season.value]
            
            # Add some realistic variation
            variation = math.sin(i * 0.5) * 0.1 + 1  # ±10% variation
            forecasted_revenue = base_revenue * seasonal_mult * variation
            
            # Calculate confidence based on how far in future
            confidence = max(60, 95 - (i * 3))  # Decreasing confidence over time
            
            forecast_data.append({
                "month": future_date.strftime("%b %Y"),
                "month_short": future_date.strftime("%b"),
                "forecasted_revenue": round(forecasted_revenue, 2),
                "confidence": confidence,
                "season": season.value,
                "seasonal_multiplier": seasonal_mult
            })
        
        return {
            "forecast_data": forecast_data,
            "insights": {
                "peak_month": max(forecast_data, key=lambda x: x["forecasted_revenue"]),
                "low_month": min(forecast_data, key=lambda x: x["forecasted_revenue"]),
                "average_confidence": round(sum(f["confidence"] for f in forecast_data) / len(forecast_data), 1)
            }
        }
    
    def get_market_benchmarks(self, area: str, property_type: str = "apartment") -> Dict[str, Any]:
        """Get market benchmarks for a specific Dubai area"""
        area_mult = self.area_multipliers.get(area, 1.0)
        base_adr = 120  # Base Average Daily Rate
        
        market_adr = base_adr * area_mult
        
        # Simulate market data based on area
        benchmarks = {
            "market_metrics": {
                "average_daily_rate": round(market_adr, 2),
                "occupancy_rate": round(65 + (area_mult * 10), 1),
                "revpar": round(market_adr * (0.65 + area_mult * 0.1), 2),
                "market_health_score": round(60 + (area_mult * 20), 1)
            },
            "area_insights": {
                "area": area.replace("_", " ").title(),
                "tier": "Premium" if area_mult >= 1.4 else "Standard" if area_mult >= 1.0 else "Budget",
                "primary_demand": self._get_area_demand_profile(area),
                "seasonality_impact": "High" if area_mult >= 1.3 else "Medium"
            },
            "recommendations": self._get_area_recommendations(area, area_mult)
        }
        
        return benchmarks
    
    def _get_area_demand_profile(self, area: str) -> str:
        """Get primary demand profile for Dubai area"""
        profiles = {
            DubaiArea.MARINA.value: "Tourists & Business Travelers",
            DubaiArea.DOWNTOWN.value: "Business & Conference Attendees", 
            DubaiArea.JLT.value: "Corporate Housing & Expats",
            DubaiArea.BUSINESS_BAY.value: "Business Travelers",
            DubaiArea.JBR.value: "Leisure Tourists",
            DubaiArea.PALM_JUMEIRAH.value: "Luxury Tourists",
            DubaiArea.JUMEIRAH.value: "Family Tourists",
            DubaiArea.DEIRA.value: "Budget Travelers & Regional Visitors",
            DubaiArea.BURDUBAI.value: "Cultural Tourists & Budget Travelers",
            DubaiArea.SILICON_OASIS.value: "Tech Workers & Long-term Stays"
        }
        return profiles.get(area, "Mixed Demand")
    
    def _get_area_recommendations(self, area: str, multiplier: float) -> List[str]:
        """Get area-specific recommendations"""
        recommendations = []
        
        if multiplier >= 1.5:
            recommendations.append("Premium positioning - focus on luxury amenities")
            recommendations.append("Target high-end business and leisure travelers")
        elif multiplier >= 1.0:
            recommendations.append("Competitive rates with quality amenities")
            recommendations.append("Balanced approach for business and leisure")
        else:
            recommendations.append("Value positioning - emphasize cost-effectiveness")
            recommendations.append("Target budget-conscious and longer-stay guests")
        
        # Area-specific recommendations
        if area == DubaiArea.MARINA.value:
            recommendations.append("Highlight waterfront views and dining options")
        elif area == DubaiArea.DOWNTOWN.value:
            recommendations.append("Emphasize business facilities and metro access")
        elif area == DubaiArea.JLT.value:
            recommendations.append("Target corporate clients and metro connectivity")
        
        return recommendations

# Global instance
dubai_market_service = DubaiMarketService()
