"""
Contact Prediction System

Predicts communication windows between satellites and ground stations
based on orbital mechanics and visibility constraints.
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import numpy as np

from .mechanics import OrbitalMechanics, SatelliteState, KeplerianElements, GeodeticPosition


@dataclass
class ContactWindow:
    """Communication contact window between two nodes."""
    contact_id: str
    source_id: str
    target_id: str
    start_time: datetime
    end_time: datetime
    max_elevation: float  # degrees
    max_range: float  # km
    data_rate: float  # Mbps
    quality_factor: float = 1.0  # 0-1 link quality
    is_predicted: bool = True
    
    @property
    def duration(self) -> timedelta:
        """Contact duration."""
        return self.end_time - self.start_time
    
    @property
    def duration_seconds(self) -> float:
        """Contact duration in seconds."""
        return self.duration.total_seconds()


@dataclass
class GroundStation:
    """Ground station configuration."""
    station_id: str
    name: str
    position: GeodeticPosition
    elevation_mask: float = 10.0  # Minimum elevation angle (degrees)
    max_range: float = 2000.0  # Maximum communication range (km)
    antenna_gain: float = 40.0  # dBi
    power: float = 100.0  # Watts


@dataclass
class LinkBudget:
    """RF link budget parameters."""
    frequency: float = 2.4e9  # Hz (default S-band)
    tx_power: float = 10.0  # Watts
    tx_gain: float = 20.0  # dBi
    rx_gain: float = 20.0  # dBi
    noise_temp: float = 300.0  # Kelvin
    bandwidth: float = 10e6  # Hz
    required_snr: float = 10.0  # dB
    band_name: str = "S-band"  # Human-readable band name
    
    @classmethod
    def create_preset(cls, band_type: str = "s-band"):
        """Create RF parameters for common satellite bands."""
        presets = {
            "l-band": cls(
                frequency=1.575e9,     # GPS L1 frequency
                tx_power=50.0,         # 50W for L-band
                tx_gain=12.0,          # Lower gain, wider beam
                rx_gain=35.0,          # Ground station L-band antenna
                noise_temp=180.0,      # Good L-band LNA
                bandwidth=20e6,        # 20 MHz bandwidth
                required_snr=6.0,      # Lower SNR requirement
                band_name="L-band"
            ),
            "s-band": cls(
                frequency=2.4e9,       # S-band ISM
                tx_power=20.0,         # 20W typical
                tx_gain=18.0,          # Medium gain
                rx_gain=40.0,          # S-band ground antenna
                noise_temp=150.0,      # S-band system noise
                bandwidth=10e6,        # 10 MHz bandwidth
                required_snr=8.0,      # Standard requirement
                band_name="S-band"
            ),
            "c-band": cls(
                frequency=6.0e9,       # C-band uplink
                tx_power=15.0,         # 15W for C-band
                tx_gain=25.0,          # Higher gain
                rx_gain=50.0,          # Large C-band dish
                noise_temp=120.0,      # Low noise C-band
                bandwidth=36e6,        # 36 MHz transponder
                required_snr=10.0,     # Higher SNR needed
                band_name="C-band"
            ),
            "ku-band": cls(
                frequency=14.0e9,      # Ku-band uplink
                tx_power=10.0,         # 10W for Ku-band
                tx_gain=35.0,          # High gain, narrow beam
                rx_gain=55.0,          # High gain Ku dish
                noise_temp=100.0,      # Excellent LNA
                bandwidth=50e6,        # 50 MHz bandwidth
                required_snr=12.0,     # Higher SNR requirement
                band_name="Ku-band"
            ),
            "ka-band": cls(
                frequency=20.0e9,      # Ka-band (Starlink-like)
                tx_power=5.0,          # 5W for Ka-band
                tx_gain=42.0,          # Very high gain
                rx_gain=60.0,          # High-performance Ka dish
                noise_temp=80.0,       # Excellent Ka LNA
                bandwidth=250e6,       # 250 MHz wide bandwidth
                required_snr=15.0,     # High SNR for high data rates
                band_name="Ka-band"
            ),
            "v-band": cls(
                frequency=60.0e9,      # V-band experimental
                tx_power=2.0,          # 2W for V-band
                tx_gain=50.0,          # Extremely high gain
                rx_gain=65.0,          # Very high gain V-band
                noise_temp=200.0,      # Higher noise at V-band
                bandwidth=1000e6,      # 1 GHz bandwidth
                required_snr=18.0,     # Very high SNR needed
                band_name="V-band"
            )
        }
        
        return presets.get(band_type.lower(), presets["s-band"])
    
    def calculate_data_rate(self, range_km: float, elevation: float) -> float:
        """Calculate achievable data rate based on realistic link budget."""
        # Free space path loss (Friis equation)
        wavelength = 3e8 / self.frequency  # c = λf
        path_loss_db = 20 * math.log10(4 * math.pi * range_km * 1000 / wavelength)
        
        # Frequency-dependent atmospheric losses
        atm_loss_db = self._calculate_atmospheric_loss(elevation)
        
        # Rain fade (frequency dependent)
        rain_loss_db = self._calculate_rain_loss(elevation)
        
        # Total path loss
        total_loss_db = path_loss_db + atm_loss_db + rain_loss_db
        
        # Link budget calculation
        eirp_dbw = 10 * math.log10(self.tx_power) + self.tx_gain  # dBW
        rx_power_dbw = eirp_dbw - total_loss_db + self.rx_gain
        
        # Thermal noise power
        k_boltzmann = 1.38e-23  # Boltzmann constant
        noise_power_dbw = 10 * math.log10(k_boltzmann * self.noise_temp * self.bandwidth)
        
        # Signal-to-noise ratio
        snr_db = rx_power_dbw - noise_power_dbw
        
        # Shannon capacity with realistic coding gain
        if snr_db >= self.required_snr:
            snr_linear = 10**(snr_db / 10)
            # Shannon capacity
            shannon_capacity = self.bandwidth * math.log2(1 + snr_linear) / 1e6  # Mbps
            
            # Apply realistic coding efficiency (typically 0.6-0.8 for satellite links)
            coding_efficiency = 0.75
            practical_data_rate = shannon_capacity * coding_efficiency
            
            # Band-specific maximum data rates (realistic limits)
            max_rates = {
                "L-band": 10.0,      # L-band: up to 10 Mbps
                "S-band": 50.0,      # S-band: up to 50 Mbps  
                "C-band": 200.0,     # C-band: up to 200 Mbps
                "Ku-band": 500.0,    # Ku-band: up to 500 Mbps
                "Ka-band": 2000.0,   # Ka-band: up to 2 Gbps
                "V-band": 10000.0    # V-band: up to 10 Gbps
            }
            
            max_rate = max_rates.get(self.band_name, 100.0)
            return min(practical_data_rate, max_rate)
        else:
            return 0.0  # Link margin insufficient
    
    def _calculate_atmospheric_loss(self, elevation: float) -> float:
        """Calculate frequency-dependent atmospheric absorption."""
        # Atmospheric loss increases with frequency and decreases with elevation
        elevation_rad = math.radians(max(elevation, 1.0))
        
        # Frequency-dependent atmospheric absorption (dB/km)
        if self.frequency < 2e9:        # L-band
            absorption_rate = 0.005
        elif self.frequency < 8e9:      # S/C-band  
            absorption_rate = 0.01
        elif self.frequency < 20e9:     # X/Ku-band
            absorption_rate = 0.02
        elif self.frequency < 40e9:     # Ka-band
            absorption_rate = 0.05
        else:                           # V-band and above
            absorption_rate = 0.15
        
        # Path length through atmosphere (simplified)
        atmosphere_thickness = 50.0  # km effective thickness
        path_length = atmosphere_thickness / math.sin(elevation_rad)
        
        return absorption_rate * path_length
    
    def _calculate_rain_loss(self, elevation: float) -> float:
        """Calculate rain fade based on frequency and elevation."""
        # Rain attenuation increases dramatically with frequency
        # ITU-R P.838 model (simplified)
        
        if self.frequency < 10e9:       # Below 10 GHz: minimal rain fade
            return 0.1
        elif self.frequency < 20e9:     # Ku-band: moderate rain fade
            rain_rate = 2.0  # dB for moderate rain
        elif self.frequency < 40e9:     # Ka-band: significant rain fade
            rain_rate = 5.0  # dB for moderate rain
        else:                           # V-band: severe rain fade
            rain_rate = 15.0  # dB for moderate rain
        
        # Rain fade decreases with higher elevation (shorter path)
        elevation_factor = math.sin(math.radians(max(elevation, 5.0)))
        return rain_rate * (1.0 - elevation_factor * 0.5)


class ContactPredictor:
    """Predicts contact windows for satellite networks."""
    
    def __init__(self):
        self.orbital_mechanics = OrbitalMechanics()
        self.link_budget = LinkBudget()
        self.prediction_cache: Dict[str, List[ContactWindow]] = {}
    
    def predict_contacts(
        self,
        satellites: Dict[str, KeplerianElements],
        ground_stations: Dict[str, GroundStation],
        start_time: datetime,
        duration_hours: float,
        time_step_seconds: float = 60.0
    ) -> List[ContactWindow]:
        """Predict all contact windows in the given time period."""
        
        contacts = []
        end_time = start_time + timedelta(hours=duration_hours)
        current_time = start_time
        
        # Track ongoing contacts
        active_contacts: Dict[str, Dict] = {}
        
        while current_time <= end_time:
            # Update satellite positions
            sat_states = {}
            for sat_id, elements in satellites.items():
                sat_states[sat_id] = self.orbital_mechanics.propagate_orbit(
                    elements, current_time
                )
            
            # Check satellite-to-ground contacts
            for sat_id, sat_state in sat_states.items():
                for gs_id, ground_station in ground_stations.items():
                    contact_key = f"{sat_id}_{gs_id}"
                    
                    # Calculate visibility
                    elevation, azimuth, range_km = self.orbital_mechanics.calculate_contact_geometry(
                        sat_state,
                        ground_station.position.latitude,
                        ground_station.position.longitude,
                        ground_station.position.altitude
                    )
                    
                    # Check if contact is possible
                    if (elevation >= ground_station.elevation_mask and 
                        range_km <= ground_station.max_range):
                        
                        # Calculate data rate
                        data_rate = self.link_budget.calculate_data_rate(range_km, elevation)
                        
                        if data_rate > 0:
                            if contact_key not in active_contacts:
                                # New contact starting
                                active_contacts[contact_key] = {
                                    'start_time': current_time,
                                    'max_elevation': elevation,
                                    'max_range': range_km,
                                    'max_data_rate': data_rate,
                                    'sat_id': sat_id,
                                    'gs_id': gs_id
                                }
                            else:
                                # Update ongoing contact
                                if elevation > active_contacts[contact_key]['max_elevation']:
                                    active_contacts[contact_key]['max_elevation'] = elevation
                                if data_rate > active_contacts[contact_key]['max_data_rate']:
                                    active_contacts[contact_key]['max_data_rate'] = data_rate
                    else:
                        # Contact ended or not possible
                        if contact_key in active_contacts:
                            # End the contact
                            contact_info = active_contacts[contact_key]
                            
                            contact = ContactWindow(
                                contact_id=f"contact_{len(contacts):06d}",
                                source_id=contact_info['sat_id'],
                                target_id=contact_info['gs_id'],
                                start_time=contact_info['start_time'],
                                end_time=current_time,
                                max_elevation=contact_info['max_elevation'],
                                max_range=contact_info['max_range'],
                                data_rate=contact_info['max_data_rate']
                            )
                            contacts.append(contact)
                            del active_contacts[contact_key]
            
            # Check satellite-to-satellite contacts
            sat_list = list(sat_states.items())
            for i, (sat1_id, sat1_state) in enumerate(sat_list):
                for j, (sat2_id, sat2_state) in enumerate(sat_list[i+1:], i+1):
                    contact_key = f"{sat1_id}_{sat2_id}"
                    
                    # Calculate inter-satellite distance
                    dx = sat1_state.position.x - sat2_state.position.x
                    dy = sat1_state.position.y - sat2_state.position.y
                    dz = sat1_state.position.z - sat2_state.position.z
                    distance = math.sqrt(dx**2 + dy**2 + dz**2)
                    
                    # Check if satellites can communicate (simplified)
                    max_isl_range = 5000.0  # km, typical for inter-satellite links
                    
                    if distance <= max_isl_range:
                        # Calculate data rate for ISL
                        isl_data_rate = self._calculate_isl_data_rate(distance)
                        
                        if isl_data_rate > 0:
                            if contact_key not in active_contacts:
                                # New ISL contact
                                active_contacts[contact_key] = {
                                    'start_time': current_time,
                                    'max_elevation': 90.0,  # Not applicable for ISL
                                    'max_range': distance,
                                    'max_data_rate': isl_data_rate,
                                    'sat_id': sat1_id,
                                    'gs_id': sat2_id
                                }
                            else:
                                # Update ISL contact
                                if isl_data_rate > active_contacts[contact_key]['max_data_rate']:
                                    active_contacts[contact_key]['max_data_rate'] = isl_data_rate
                    else:
                        # ISL contact ended
                        if contact_key in active_contacts:
                            contact_info = active_contacts[contact_key]
                            
                            contact = ContactWindow(
                                contact_id=f"isl_contact_{len(contacts):06d}",
                                source_id=contact_info['sat_id'],
                                target_id=contact_info['gs_id'],
                                start_time=contact_info['start_time'],
                                end_time=current_time,
                                max_elevation=contact_info['max_elevation'],
                                max_range=contact_info['max_range'],
                                data_rate=contact_info['max_data_rate']
                            )
                            contacts.append(contact)
                            del active_contacts[contact_key]
            
            current_time += timedelta(seconds=time_step_seconds)
        
        # Close any remaining active contacts
        for contact_key, contact_info in active_contacts.items():
            contact = ContactWindow(
                contact_id=f"final_contact_{len(contacts):06d}",
                source_id=contact_info['sat_id'],
                target_id=contact_info['gs_id'],
                start_time=contact_info['start_time'],
                end_time=end_time,
                max_elevation=contact_info['max_elevation'],
                max_range=contact_info['max_range'],
                data_rate=contact_info['max_data_rate']
            )
            contacts.append(contact)
        
        return contacts
    
    def _calculate_isl_data_rate(self, distance_km: float) -> float:
        """Calculate inter-satellite link data rate."""
        # Simplified ISL model - Ka-band typical
        if distance_km <= 5000:
            # Higher data rate for closer satellites
            base_rate = 1000.0  # Mbps
            return base_rate * (5000 / distance_km)**2
        else:
            return 0.0
    
    def get_active_contacts(
        self, 
        contacts: List[ContactWindow], 
        current_time: datetime
    ) -> List[ContactWindow]:
        """Get contacts that are active at the current time."""
        active = []
        for contact in contacts:
            if contact.start_time <= current_time <= contact.end_time:
                active.append(contact)
        return active
    
    def get_future_contacts(
        self,
        contacts: List[ContactWindow],
        current_time: datetime,
        lookahead_hours: float = 24.0
    ) -> List[ContactWindow]:
        """Get future contacts within the lookahead window."""
        future_cutoff = current_time + timedelta(hours=lookahead_hours)
        future = []
        
        for contact in contacts:
            if current_time < contact.start_time <= future_cutoff:
                future.append(contact)
        
        return sorted(future, key=lambda c: c.start_time)
    
    def calculate_contact_statistics(
        self,
        contacts: List[ContactWindow],
        node_id: str
    ) -> Dict[str, float]:
        """Calculate contact statistics for a node."""
        
        node_contacts = [
            c for c in contacts 
            if c.source_id == node_id or c.target_id == node_id
        ]
        
        if not node_contacts:
            return {
                'total_contacts': 0,
                'total_contact_time': 0.0,
                'average_contact_duration': 0.0,
                'contact_frequency': 0.0,
                'coverage_percentage': 0.0
            }
        
        total_time = sum(c.duration_seconds for c in node_contacts)
        avg_duration = total_time / len(node_contacts)
        
        # Calculate coverage percentage over 24 hours
        if contacts:
            time_span = max(c.end_time for c in contacts) - min(c.start_time for c in contacts)
            coverage_percentage = (total_time / time_span.total_seconds()) * 100
        else:
            coverage_percentage = 0.0
        
        return {
            'total_contacts': len(node_contacts),
            'total_contact_time': total_time,
            'average_contact_duration': avg_duration,
            'contact_frequency': len(node_contacts) / 24.0,  # contacts per hour
            'coverage_percentage': coverage_percentage
        }
    
    def optimize_contact_plan(
        self,
        contacts: List[ContactWindow],
        priority_nodes: List[str] = None
    ) -> List[ContactWindow]:
        """Optimize contact plan to avoid conflicts and maximize throughput."""
        
        # Sort contacts by start time
        sorted_contacts = sorted(contacts, key=lambda c: c.start_time)
        optimized_contacts = []
        
        # Simple greedy algorithm to avoid conflicts
        # In production, would use more sophisticated optimization
        
        active_nodes = set()
        
        for contact in sorted_contacts:
            # Check if either node is already busy
            if contact.source_id not in active_nodes and contact.target_id not in active_nodes:
                optimized_contacts.append(contact)
                active_nodes.add(contact.source_id)
                active_nodes.add(contact.target_id)
                
                # Schedule node release
                # (In real implementation, would use proper event scheduling)
        
        return optimized_contacts


def create_major_cities_ground_stations() -> Dict[str, GroundStation]:
    """Create comprehensive ground station database for major global cities."""
    
    # Major global cities with strategic DTN coverage
    cities_data = {
        # North America
        'gs_new_york': {'name': 'New York', 'lat': 40.7128, 'lon': -74.0060, 'alt': 0.010},
        'gs_los_angeles': {'name': 'Los Angeles', 'lat': 34.0522, 'lon': -118.2437, 'alt': 0.100},
        'gs_chicago': {'name': 'Chicago', 'lat': 41.8781, 'lon': -87.6298, 'alt': 0.180},
        'gs_toronto': {'name': 'Toronto', 'lat': 43.6532, 'lon': -79.3832, 'alt': 0.076},
        'gs_mexico_city': {'name': 'Mexico City', 'lat': 19.4326, 'lon': -99.1332, 'alt': 2.240},
        
        # South America
        'gs_sao_paulo': {'name': 'São Paulo', 'lat': -23.5505, 'lon': -46.6333, 'alt': 0.760},
        'gs_buenos_aires': {'name': 'Buenos Aires', 'lat': -34.6037, 'lon': -58.3816, 'alt': 0.025},
        'gs_bogota': {'name': 'Bogotá', 'lat': 4.7110, 'lon': -74.0721, 'alt': 2.625},
        
        # Europe
        'gs_london': {'name': 'London', 'lat': 51.5074, 'lon': -0.1278, 'alt': 0.035},
        'gs_paris': {'name': 'Paris', 'lat': 48.8566, 'lon': 2.3522, 'alt': 0.035},
        'gs_berlin': {'name': 'Berlin', 'lat': 52.5200, 'lon': 13.4050, 'alt': 0.034},
        'gs_rome': {'name': 'Rome', 'lat': 41.9028, 'lon': 12.4964, 'alt': 0.021},
        'gs_madrid': {'name': 'Madrid', 'lat': 40.4168, 'lon': -3.7038, 'alt': 0.650},
        'gs_moscow': {'name': 'Moscow', 'lat': 55.7558, 'lon': 37.6173, 'alt': 0.156},
        
        # Asia-Pacific
        'gs_tokyo': {'name': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503, 'alt': 0.040},
        'gs_beijing': {'name': 'Beijing', 'lat': 39.9042, 'lon': 116.4074, 'alt': 0.043},
        'gs_shanghai': {'name': 'Shanghai', 'lat': 31.2304, 'lon': 121.4737, 'alt': 0.004},
        'gs_mumbai': {'name': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777, 'alt': 0.014},
        'gs_delhi': {'name': 'Delhi', 'lat': 28.7041, 'lon': 77.1025, 'alt': 0.216},
        'gs_singapore': {'name': 'Singapore', 'lat': 1.3521, 'lon': 103.8198, 'alt': 0.015},
        'gs_seoul': {'name': 'Seoul', 'lat': 37.5665, 'lon': 126.9780, 'alt': 0.038},
        'gs_sydney': {'name': 'Sydney', 'lat': -33.8688, 'lon': 151.2093, 'alt': 0.058},
        'gs_melbourne': {'name': 'Melbourne', 'lat': -37.8136, 'lon': 144.9631, 'alt': 0.031},
        
        # Middle East & Africa
        'gs_dubai': {'name': 'Dubai', 'lat': 25.2048, 'lon': 55.2708, 'alt': 0.005},
        'gs_cairo': {'name': 'Cairo', 'lat': 30.0444, 'lon': 31.2357, 'alt': 0.074},
        'gs_johannesburg': {'name': 'Johannesburg', 'lat': -26.2041, 'lon': 28.0473, 'alt': 1.753},
        'gs_nairobi': {'name': 'Nairobi', 'lat': -1.2921, 'lon': 36.8219, 'alt': 1.795},
        
        # Polar and Remote Regions (Strategic for satellite coverage)
        'gs_reykjavik': {'name': 'Reykjavik', 'lat': 64.1466, 'lon': -21.9426, 'alt': 0.028},
        'gs_anchorage': {'name': 'Anchorage', 'lat': 61.2181, 'lon': -149.9003, 'alt': 0.040},
        'gs_stockholm': {'name': 'Stockholm', 'lat': 59.3293, 'lon': 18.0686, 'alt': 0.028}
    }
    
    stations = {}
    for station_id, data in cities_data.items():
        stations[station_id] = GroundStation(
            station_id=station_id,
            name=data['name'],
            position=GeodeticPosition(data['lat'], data['lon'], data['alt']),
            elevation_mask=10.0,  # Standard 10° minimum elevation
            max_range=2000.0,     # 2000 km maximum range
            antenna_gain=45.0,    # High-gain antenna
            power=1000.0          # 1kW transmitter
        )
    
    return stations


def create_default_ground_stations() -> Dict[str, GroundStation]:
    """Create default ground stations (backwards compatibility)."""
    all_stations = create_major_cities_ground_stations()
    # Return subset for basic testing
    return {
        'gs_los_angeles': all_stations['gs_los_angeles'],
        'gs_tokyo': all_stations['gs_tokyo'],
        'gs_london': all_stations['gs_london'],
        'gs_sydney': all_stations['gs_sydney']
    }