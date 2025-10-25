"""
Realistic Weather Model for Satellite RF Performance

Implements weather effects on satellite communications including:
- Rain fade (frequency dependent)
- Atmospheric attenuation
- Cloud cover effects
- Seasonal variations
- Geographic weather patterns
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class WeatherType(Enum):
    """Weather condition types affecting satellite communications."""
    CLEAR = "clear"
    LIGHT_RAIN = "light_rain"
    MODERATE_RAIN = "moderate_rain"
    HEAVY_RAIN = "heavy_rain"
    THUNDERSTORM = "thunderstorm"
    SNOW = "snow"
    FOG = "fog"
    CLOUDY = "cloudy"

@dataclass
class WeatherCondition:
    """Current weather conditions at a location."""
    weather_type: WeatherType
    rain_rate_mm_hr: float = 0.0      # Rain rate in mm/hour
    cloud_cover_percent: float = 0.0   # Cloud coverage 0-100%
    humidity_percent: float = 50.0     # Relative humidity
    temperature_c: float = 20.0        # Temperature in Celsius
    wind_speed_ms: float = 0.0         # Wind speed in m/s
    visibility_km: float = 50.0        # Visibility in kilometers
    
    def get_rain_attenuation_db(self, frequency_ghz: float, elevation_deg: float) -> float:
        """Calculate rain attenuation using ITU-R P.838 model (simplified)."""
        if self.rain_rate_mm_hr <= 0.1:
            return 0.05  # Clear sky minimal attenuation
        
        # ITU-R P.838 coefficients (simplified for key frequencies)
        if frequency_ghz < 2:
            k = 0.0001
            alpha = 0.5
        elif frequency_ghz < 8:
            k = 0.0003 + (frequency_ghz - 2) * 0.0002
            alpha = 0.7 + (frequency_ghz - 2) * 0.1
        elif frequency_ghz < 20:
            k = 0.003 + (frequency_ghz - 8) * 0.005
            alpha = 1.0 + (frequency_ghz - 8) * 0.2
        elif frequency_ghz < 40:
            k = 0.08 + (frequency_ghz - 20) * 0.01
            alpha = 1.5 + (frequency_ghz - 20) * 0.1
        else:  # V-band and above
            k = 0.3 + (frequency_ghz - 40) * 0.02
            alpha = 1.8
        
        # Rain attenuation
        rain_atten = k * (self.rain_rate_mm_hr ** alpha)
        
        # Path length correction for elevation
        elevation_rad = math.radians(max(elevation_deg, 5))
        path_correction = 1.0 / math.sin(elevation_rad)
        
        return rain_atten * path_correction
    
    def get_atmospheric_attenuation_db(self, frequency_ghz: float, elevation_deg: float) -> float:
        """Calculate atmospheric attenuation including water vapor and oxygen."""
        elevation_rad = math.radians(max(elevation_deg, 1))
        
        # Water vapor attenuation (frequency and humidity dependent)
        water_vapor_density = self.humidity_percent * 0.1 * math.exp(-self.temperature_c / 30)
        
        if frequency_ghz < 10:
            vapor_atten = 0.01 * water_vapor_density
        elif frequency_ghz < 30:
            # Water vapor resonance around 22 GHz
            vapor_atten = 0.05 + abs(frequency_ghz - 22) * 0.01
            vapor_atten *= water_vapor_density
        else:
            vapor_atten = 0.2 * water_vapor_density
        
        # Oxygen attenuation (around 60 GHz)
        if frequency_ghz > 50:
            oxygen_atten = 0.1 + abs(frequency_ghz - 60) * 0.02
        else:
            oxygen_atten = 0.02
        
        # Path length through atmosphere
        atmosphere_path = 8.0 / math.sin(elevation_rad)  # km
        
        total_atten = (vapor_atten + oxygen_atten) * atmosphere_path
        
        # Cloud attenuation
        if self.cloud_cover_percent > 20:
            cloud_factor = (self.cloud_cover_percent / 100) * 0.1
            total_atten += cloud_factor * frequency_ghz * 0.01
        
        return total_atten
    
    def get_scintillation_db(self, frequency_ghz: float, elevation_deg: float) -> float:
        """Calculate atmospheric scintillation (signal fluctuations)."""
        if elevation_deg > 20:
            return random.gauss(0, 0.2)  # Low scintillation at high elevation
        else:
            # Higher scintillation at low elevation
            scint_std = 0.5 * (30 - elevation_deg) / 30
            return random.gauss(0, scint_std)

@dataclass 
class WeatherRegion:
    """Regional weather characteristics."""
    name: str
    latitude: float
    longitude: float
    climate_type: str  # "tropical", "temperate", "arctic", "desert", "maritime"
    seasonal_rain_factor: float = 1.0
    base_humidity: float = 50.0
    base_temperature: float = 20.0

class WeatherSimulator:
    """Realistic weather simulation for satellite communications."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize weather simulator with optional random seed."""
        if seed is not None:
            random.seed(seed)
        
        # Define major weather regions
        self.regions = {
            "north_america_west": WeatherRegion("North America West", 37.0, -122.0, "temperate", 0.3, 45.0, 15.0),
            "north_america_east": WeatherRegion("North America East", 40.0, -74.0, "temperate", 0.7, 55.0, 12.0),
            "europe": WeatherRegion("Europe", 51.5, 0.0, "maritime", 0.8, 70.0, 10.0),
            "asia_east": WeatherRegion("East Asia", 35.7, 139.7, "temperate", 1.2, 65.0, 18.0),
            "tropical": WeatherRegion("Tropical", 1.3, 103.8, "tropical", 2.5, 80.0, 28.0),
            "south_america": WeatherRegion("South America", -23.5, -46.6, "tropical", 1.8, 70.0, 22.0),
            "australia": WeatherRegion("Australia", -33.9, 151.2, "temperate", 0.6, 50.0, 20.0),
            "africa": WeatherRegion("Africa", -1.3, 36.8, "tropical", 1.5, 60.0, 25.0),
            "arctic": WeatherRegion("Arctic", 64.1, -21.9, "arctic", 0.2, 80.0, -5.0),
        }
        
        # Weather transition probabilities
        self.weather_transitions = {
            WeatherType.CLEAR: {
                WeatherType.CLEAR: 0.7,
                WeatherType.CLOUDY: 0.2,
                WeatherType.LIGHT_RAIN: 0.08,
                WeatherType.FOG: 0.02
            },
            WeatherType.CLOUDY: {
                WeatherType.CLOUDY: 0.4,
                WeatherType.CLEAR: 0.3,
                WeatherType.LIGHT_RAIN: 0.2,
                WeatherType.MODERATE_RAIN: 0.1
            },
            WeatherType.LIGHT_RAIN: {
                WeatherType.LIGHT_RAIN: 0.3,
                WeatherType.MODERATE_RAIN: 0.3,
                WeatherType.CLOUDY: 0.3,
                WeatherType.CLEAR: 0.1
            },
            WeatherType.MODERATE_RAIN: {
                WeatherType.MODERATE_RAIN: 0.4,
                WeatherType.LIGHT_RAIN: 0.3,
                WeatherType.HEAVY_RAIN: 0.2,
                WeatherType.CLOUDY: 0.1
            },
            WeatherType.HEAVY_RAIN: {
                WeatherType.HEAVY_RAIN: 0.2,
                WeatherType.THUNDERSTORM: 0.3,
                WeatherType.MODERATE_RAIN: 0.4,
                WeatherType.LIGHT_RAIN: 0.1
            },
            WeatherType.THUNDERSTORM: {
                WeatherType.THUNDERSTORM: 0.1,
                WeatherType.HEAVY_RAIN: 0.4,
                WeatherType.MODERATE_RAIN: 0.3,
                WeatherType.CLOUDY: 0.2
            }
        }
        
        # Current weather state for each region
        self.current_weather: Dict[str, WeatherCondition] = {}
        self._initialize_weather()
    
    def _initialize_weather(self):
        """Initialize weather conditions for all regions."""
        for region_name, region in self.regions.items():
            # Start with region-appropriate weather
            if region.climate_type == "tropical":
                initial_weather = WeatherType.CLOUDY if random.random() < 0.6 else WeatherType.LIGHT_RAIN
            elif region.climate_type == "arctic":
                initial_weather = WeatherType.CLEAR if random.random() < 0.7 else WeatherType.SNOW
            elif region.climate_type == "desert":
                initial_weather = WeatherType.CLEAR
            else:  # temperate, maritime
                initial_weather = WeatherType.CLEAR if random.random() < 0.5 else WeatherType.CLOUDY
            
            self.current_weather[region_name] = self._generate_weather_condition(initial_weather, region)
    
    def _generate_weather_condition(self, weather_type: WeatherType, region: WeatherRegion) -> WeatherCondition:
        """Generate detailed weather condition based on type and region."""
        
        # Base parameters from region
        temp = region.base_temperature + random.gauss(0, 5)
        humidity = region.base_humidity + random.gauss(0, 10)
        humidity = max(20, min(100, humidity))
        
        # Weather-specific parameters
        if weather_type == WeatherType.CLEAR:
            rain_rate = 0.0
            cloud_cover = random.uniform(0, 20)
            visibility = random.uniform(40, 100)
            wind_speed = random.uniform(0, 5)
            
        elif weather_type == WeatherType.CLOUDY:
            rain_rate = 0.0
            cloud_cover = random.uniform(60, 90)
            visibility = random.uniform(20, 50)
            wind_speed = random.uniform(2, 8)
            humidity += 10
            
        elif weather_type == WeatherType.LIGHT_RAIN:
            rain_rate = random.uniform(0.5, 4.0) * region.seasonal_rain_factor
            cloud_cover = random.uniform(80, 95)
            visibility = random.uniform(5, 20)
            wind_speed = random.uniform(3, 10)
            humidity += 20
            temp -= 2
            
        elif weather_type == WeatherType.MODERATE_RAIN:
            rain_rate = random.uniform(4.0, 15.0) * region.seasonal_rain_factor
            cloud_cover = random.uniform(90, 100)
            visibility = random.uniform(2, 8)
            wind_speed = random.uniform(5, 15)
            humidity += 25
            temp -= 3
            
        elif weather_type == WeatherType.HEAVY_RAIN:
            rain_rate = random.uniform(15.0, 50.0) * region.seasonal_rain_factor
            cloud_cover = 100
            visibility = random.uniform(0.5, 3)
            wind_speed = random.uniform(8, 20)
            humidity = min(100, humidity + 30)
            temp -= 5
            
        elif weather_type == WeatherType.THUNDERSTORM:
            rain_rate = random.uniform(25.0, 100.0) * region.seasonal_rain_factor
            cloud_cover = 100
            visibility = random.uniform(0.2, 2)
            wind_speed = random.uniform(15, 35)
            humidity = min(100, humidity + 35)
            temp -= 8
            
        elif weather_type == WeatherType.SNOW:
            rain_rate = random.uniform(1.0, 10.0)  # Snow equivalent
            cloud_cover = random.uniform(70, 100)
            visibility = random.uniform(1, 10)
            wind_speed = random.uniform(5, 20)
            temp = min(temp, random.uniform(-10, 2))
            humidity += 15
            
        elif weather_type == WeatherType.FOG:
            rain_rate = random.uniform(0, 0.5)
            cloud_cover = random.uniform(90, 100)
            visibility = random.uniform(0.1, 1.0)
            wind_speed = random.uniform(0, 3)
            humidity = min(100, humidity + 40)
            
        else:  # Default to clear
            rain_rate = 0.0
            cloud_cover = 10
            visibility = 50
            wind_speed = 3
        
        return WeatherCondition(
            weather_type=weather_type,
            rain_rate_mm_hr=max(0, rain_rate),
            cloud_cover_percent=max(0, min(100, cloud_cover)),
            humidity_percent=max(20, min(100, humidity)),
            temperature_c=temp,
            wind_speed_ms=max(0, wind_speed),
            visibility_km=max(0.1, visibility)
        )
    
    def advance_weather(self, time_step_minutes: float = 5.0):
        """Advance weather simulation by time step."""
        # Weather changes more slowly than satellite simulation
        change_probability = time_step_minutes / 60.0  # Change probability per hour
        
        for region_name, current_condition in self.current_weather.items():
            if random.random() < change_probability:
                # Transition to new weather state
                current_type = current_condition.weather_type
                transitions = self.weather_transitions.get(current_type, {WeatherType.CLEAR: 1.0})
                
                # Choose new weather type based on transition probabilities
                rand_val = random.random()
                cumulative_prob = 0.0
                new_weather_type = current_type
                
                for weather_type, prob in transitions.items():
                    cumulative_prob += prob
                    if rand_val <= cumulative_prob:
                        new_weather_type = weather_type
                        break
                
                # Generate new weather condition
                region = self.regions[region_name]
                self.current_weather[region_name] = self._generate_weather_condition(new_weather_type, region)
    
    def get_weather_at_location(self, latitude: float, longitude: float) -> WeatherCondition:
        """Get current weather conditions at a specific location."""
        # Find closest weather region
        closest_region = None
        min_distance = float('inf')
        
        for region_name, region in self.regions.items():
            # Simple distance calculation
            lat_diff = latitude - region.latitude
            lon_diff = longitude - region.longitude
            distance = (lat_diff ** 2 + lon_diff ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_region = region_name
        
        return self.current_weather.get(closest_region, self._generate_weather_condition(WeatherType.CLEAR, self.regions["north_america_west"]))
    
    def get_weather_summary(self) -> Dict[str, Dict]:
        """Get summary of current weather in all regions."""
        summary = {}
        for region_name, condition in self.current_weather.items():
            summary[region_name] = {
                "weather_type": condition.weather_type.value,
                "rain_rate_mm_hr": round(condition.rain_rate_mm_hr, 1),
                "cloud_cover_percent": round(condition.cloud_cover_percent, 0),
                "temperature_c": round(condition.temperature_c, 1),
                "humidity_percent": round(condition.humidity_percent, 0),
                "visibility_km": round(condition.visibility_km, 1)
            }
        return summary