# Satellite Communication Architecture for DTN Simulator

## Overview

This document defines the satellite communication architecture for the Delay Tolerant Network (DTN) simulator. It provides comprehensive specifications for satellite constellation parameters, ground station configurations, orbital mechanics, contact window calculations, and link characteristics models.

## 1. Satellite Constellation Parameters

### 1.1 Low Earth Orbit (LEO) Configuration

**Constellation Type:** LEO
- **Altitude Range:** 160 km - 2,000 km
- **Typical Altitude:** 550 km (Starlink-like)
- **Orbital Period:** ~95 minutes
- **Orbital Velocity:** ~7.6 km/s
- **Number of Satellites:** 66-12,000 (configurable)
- **Orbital Planes:** 6-72 planes
- **Satellites per Plane:** 11-66 satellites
- **Inclination:** 53°-97° (polar to sun-synchronous)
- **Coverage:** Global with frequent revisits
- **Latency:** 1-40 ms one-way

**Preset Configurations:**
```json
{
  "leo_iridium": {
    "name": "Iridium-like LEO",
    "altitude_km": 780,
    "orbital_planes": 6,
    "satellites_per_plane": 11,
    "inclination_deg": 86.4,
    "total_satellites": 66
  },
  "leo_starlink": {
    "name": "Starlink-like LEO", 
    "altitude_km": 550,
    "orbital_planes": 72,
    "satellites_per_plane": 22,
    "inclination_deg": 53,
    "total_satellites": 1584
  }
}
```

### 1.2 Medium Earth Orbit (MEO) Configuration

**Constellation Type:** MEO
- **Altitude Range:** 2,000 km - 35,786 km
- **Typical Altitude:** 20,200 km (GPS-like)
- **Orbital Period:** ~12 hours
- **Orbital Velocity:** ~3.9 km/s
- **Number of Satellites:** 24-30 satellites
- **Orbital Planes:** 3-6 planes
- **Satellites per Plane:** 4-8 satellites
- **Inclination:** 55°-65°
- **Coverage:** Global with moderate revisit times
- **Latency:** 50-150 ms one-way

**Preset Configuration:**
```json
{
  "meo_gps": {
    "name": "GPS-like MEO",
    "altitude_km": 20200,
    "orbital_planes": 6,
    "satellites_per_plane": 4,
    "inclination_deg": 55,
    "total_satellites": 24
  }
}
```

### 1.3 Geostationary Earth Orbit (GEO) Configuration

**Constellation Type:** GEO
- **Altitude:** 35,786 km (fixed)
- **Orbital Period:** 24 hours (sidereal day)
- **Orbital Velocity:** ~3.07 km/s
- **Number of Satellites:** 3-36 satellites
- **Orbital Planes:** 1 (equatorial)
- **Longitude Spacing:** 10°-120° apart
- **Inclination:** 0° (equatorial)
- **Coverage:** Near-global (±70° latitude)
- **Latency:** 240-280 ms one-way

**Preset Configuration:**
```json
{
  "geo_minimal": {
    "name": "Minimal GEO Coverage",
    "altitude_km": 35786,
    "orbital_planes": 1,
    "satellites_total": 3,
    "longitude_spacing_deg": 120,
    "inclination_deg": 0
  }
}
```

### 1.4 Highly Elliptical Orbit (HEO) Configuration

**Constellation Type:** HEO (Molniya-type)
- **Perigee Altitude:** 500-1,000 km
- **Apogee Altitude:** 35,000-40,000 km
- **Orbital Period:** ~12 hours
- **Eccentricity:** 0.7-0.75
- **Number of Satellites:** 3-12 satellites
- **Orbital Planes:** 1-3 planes
- **Inclination:** 63.4° (critical inclination)
- **Coverage:** High latitude regions
- **Latency:** Variable (20-300 ms)

**Preset Configuration:**
```json
{
  "heo_molniya": {
    "name": "Molniya-like HEO",
    "perigee_km": 500,
    "apogee_km": 39354,
    "orbital_planes": 3,
    "satellites_per_plane": 4,
    "inclination_deg": 63.4,
    "total_satellites": 12
  }
}
```

### 1.5 Interplanetary Configuration

**Constellation Type:** Interplanetary
- **Earth-Mars Distance:** 54.6M - 401M km (variable)
- **Communication Delay:** 3-22 minutes one-way
- **Orbital Mechanics:** Heliocentric orbits
- **Relay Satellites:** Mars orbit, Earth-Moon L points
- **Deep Space Network:** Ground-based tracking stations
- **Bundle TTL:** Days to months
- **Store-and-Forward:** Critical requirement

## 2. Ground Station Configuration

### 2.1 Geographic Distribution Model

**Primary Ground Stations (Tier 1):**
- **Count:** 12-24 stations globally
- **Coverage:** Major continents and strategic locations
- **Antenna Diameter:** 30-70 meters
- **Data Rate:** 1-100 Mbps
- **Availability:** 99.9% uptime

**Secondary Ground Stations (Tier 2):**
- **Count:** 50-200 stations
- **Coverage:** Regional coverage
- **Antenna Diameter:** 5-15 meters  
- **Data Rate:** 100 kbps - 10 Mbps
- **Availability:** 99% uptime

**Mobile/Portable Stations (Tier 3):**
- **Count:** Unlimited user-deployable
- **Antenna Diameter:** 0.5-3 meters
- **Data Rate:** 1 kbps - 1 Mbps
- **Use Cases:** Emergency, remote operations

### 2.2 Preset Ground Station Locations

```json
{
  "primary_stations": [
    {"name": "Svalbard", "lat": 78.92, "lon": 11.93, "tier": 1},
    {"name": "Alaska_Fairbanks", "lat": 64.86, "lon": -147.85, "tier": 1},
    {"name": "Canada_Churchill", "lat": 58.74, "lon": -94.17, "tier": 1},
    {"name": "Australia_Alice", "lat": -23.70, "lon": 133.88, "tier": 1},
    {"name": "Chile_Santiago", "lat": -33.45, "lon": -70.67, "tier": 1},
    {"name": "South_Africa_Cape", "lat": -33.93, "lon": 18.42, "tier": 1}
  ]
}
```

## 3. Orbital Mechanics Framework

### 3.1 Core Orbital Parameters

**Keplerian Elements:**
- **Semi-major axis (a):** Defines orbit size
- **Eccentricity (e):** Defines orbit shape (0 = circular, 0-1 = elliptical)
- **Inclination (i):** Orbit plane angle to equator
- **Right Ascension of Ascending Node (Ω):** Orbit orientation
- **Argument of Perigee (ω):** Ellipse orientation in orbital plane
- **True Anomaly (ν):** Satellite position in orbit

### 3.2 Orbital Velocity Calculations

**Circular Orbits:**
```
v = √(μ/r)
where:
- μ = Earth's gravitational parameter (398,600 km³/s²)
- r = orbital radius (km)
```

**Elliptical Orbits:**
```
v = √(μ(2/r - 1/a))
where:
- a = semi-major axis
- r = current distance from Earth center
```

### 3.3 Orbital Period Calculations

**Kepler's Third Law:**
```
T = 2π√(a³/μ)
where:
- T = orbital period (seconds)
- a = semi-major axis (km)
```

### 3.4 Ground Track Calculations

**Subsatellite Point:**
```python
def calculate_ground_track(sat_position, time):
    """Calculate latitude/longitude directly below satellite"""
    # Convert ECEF to geodetic coordinates
    lat = arcsin(sat_position.z / |sat_position|)
    lon = arctan2(sat_position.y, sat_position.x) - (earth_rotation_rate * time)
    return (lat, lon)
```

## 4. Contact Window Prediction

### 4.1 Line-of-Sight Calculations

**Elevation Angle:**
```python
def calculate_elevation(sat_position, ground_station):
    """Calculate elevation angle from ground station to satellite"""
    range_vector = sat_position - ground_station.position
    local_horizontal = transform_to_topocentric(range_vector, ground_station)
    elevation = arcsin(local_horizontal.z / |range_vector|)
    return elevation
```

**Minimum Elevation:** 5° (typical), 10° (high quality)

### 4.2 Contact Window Algorithm

```python
def predict_contact_windows(satellite, ground_station, duration_hours):
    """Predict all contact windows within specified duration"""
    contacts = []
    current_time = start_time
    
    while current_time < start_time + duration_hours:
        sat_pos = propagate_orbit(satellite, current_time)
        elevation = calculate_elevation(sat_pos, ground_station)
        
        if elevation > minimum_elevation:
            # Start of contact window
            start_contact = current_time
            while elevation > minimum_elevation:
                current_time += time_step
                sat_pos = propagate_orbit(satellite, current_time)
                elevation = calculate_elevation(sat_pos, ground_station)
            
            # End of contact window
            end_contact = current_time
            contacts.append({
                'start': start_contact,
                'end': end_contact,
                'duration': end_contact - start_contact,
                'max_elevation': max_elevation_during_pass
            })
        
        current_time += time_step
    
    return contacts
```

### 4.3 Contact Window Characteristics

**LEO Contacts:**
- **Duration:** 2-15 minutes per pass
- **Frequency:** 4-8 passes per day per satellite
- **Gaps:** 45-90 minutes between passes

**MEO Contacts:**
- **Duration:** 1-8 hours per pass  
- **Frequency:** 2-3 passes per day per satellite
- **Gaps:** 2-6 hours between passes

**GEO Contacts:**
- **Duration:** Continuous (if in coverage area)
- **Frequency:** Always visible from ±70° latitude
- **Gaps:** None within coverage area

## 5. Link Characteristics Model

### 5.1 Communication Link Budget

**Free Space Path Loss:**
```
FSPL(dB) = 20log₁₀(d) + 20log₁₀(f) + 92.45
where:
- d = distance (km)
- f = frequency (GHz)
```

**Link Budget Parameters:**
- **Transmit Power:** 1-50 watts
- **Antenna Gain:** 10-60 dBi
- **Frequency Bands:** L (1-2 GHz), S (2-4 GHz), X (8-12 GHz), Ka (26-40 GHz)
- **Noise Temperature:** 50-300 K
- **Rain Margin:** 3-10 dB

### 5.2 Data Rate vs Distance Model

```python
def calculate_data_rate(distance_km, frequency_ghz, tx_power_w, antenna_gain_db):
    """Calculate maximum achievable data rate"""
    # Free space path loss
    fspl_db = 20*log10(distance_km) + 20*log10(frequency_ghz) + 92.45
    
    # Link budget calculation
    eirp_db = 10*log10(tx_power_w) + antenna_gain_db
    received_power_db = eirp_db - fspl_db + antenna_gain_db
    
    # Shannon capacity with practical margin
    snr_linear = 10**(received_power_db/10) / noise_power
    capacity_bps = bandwidth_hz * log2(1 + snr_linear) * efficiency_factor
    
    return capacity_bps
```

### 5.3 Delay Models

**Propagation Delay:**
```python
def propagation_delay(distance_km):
    """Speed of light delay"""
    return distance_km / 299792.458  # milliseconds
```

**Processing Delays:**
- **Satellite Processing:** 1-10 ms
- **Ground Station Processing:** 5-50 ms
- **Protocol Stack:** 10-100 ms
- **Queuing Delays:** Variable (0-seconds)

### 5.4 Link Availability Windows

**LEO Link Characteristics:**
- **Max Distance:** 2,000 km
- **Data Rate Range:** 1 kbps - 100 Mbps
- **Latency:** 1-40 ms + processing
- **Availability:** 15-60% (depends on constellation density)

**MEO Link Characteristics:**
- **Max Distance:** 25,000 km  
- **Data Rate Range:** 100 bps - 10 Mbps
- **Latency:** 50-150 ms + processing
- **Availability:** 70-95%

**GEO Link Characteristics:**
- **Max Distance:** 42,000 km
- **Data Rate Range:** 10 bps - 1 Mbps  
- **Latency:** 240-280 ms + processing
- **Availability:** 99% (within coverage)

## 6. GUI Integration Points

### 6.1 User-Placeable Node Interface

**Node Types:**
- **Satellites:** Drag-and-drop with orbital parameter input
- **Ground Stations:** Click-to-place with antenna specifications
- **Mobile Nodes:** Path-definable with mobility models

**Constellation Preset Interface:**
```javascript
const constellationPresets = {
  "LEO_Iridium": {
    displayName: "Iridium (66 satellites)",
    satellites: 66,
    altitude: 780,
    planes: 6,
    inclination: 86.4
  },
  "LEO_Starlink": {
    displayName: "Starlink-like (1584 satellites)", 
    satellites: 1584,
    altitude: 550,
    planes: 72,
    inclination: 53
  },
  "MEO_GPS": {
    displayName: "GPS (24 satellites)",
    satellites: 24,
    altitude: 20200,
    planes: 6,
    inclination: 55
  },
  "GEO_Minimal": {
    displayName: "GEO Minimal (3 satellites)",
    satellites: 3,
    altitude: 35786,
    planes: 1,
    inclination: 0
  }
}
```

### 6.2 Real-Time Visualization Requirements

**Orbital Propagation:**
- **Update Rate:** 1-10 Hz for smooth animation
- **Time Acceleration:** 1x to 10000x real-time
- **Coordinate Systems:** ECEF, ECI, geodetic

**Contact Visualization:**
- **Active Links:** Green lines between communicating nodes
- **Contact Windows:** Timeline view with upcoming contacts
- **Link Quality:** Color-coded by data rate/signal strength

**3D Rendering:**
- **Earth Model:** Textured sphere with geographic features
- **Satellite Models:** Simple geometric shapes with orientation
- **Ground Track Display:** Historical and predicted paths
- **Coverage Areas:** Footprint polygons on Earth surface

## 7. Implementation Roadmap

### 7.1 Phase 1: Core Orbital Mechanics (Week 1-2)

**Deliverables:**
- [ ] Orbital propagation algorithms (SGP4/SDP4)
- [ ] Coordinate system transformations 
- [ ] Ground track calculations
- [ ] Contact window prediction algorithms

**Pair 2 Integration Points:**
- CSV contact plan format specification
- Mobility model interface for satellite movement
- Position/velocity state vector format

### 7.2 Phase 2: Communication Models (Week 3-4)

**Deliverables:**
- [ ] Link budget calculations
- [ ] Data rate vs distance models
- [ ] Latency and delay models
- [ ] Communication link state management

**GUI Integration:**
- Real-time link visualization APIs
- Contact window timeline data structures
- Network topology update interfaces

### 7.3 Phase 3: DTN Integration (Week 5-6)

**Deliverables:**
- [ ] Satellite-aware bundle routing
- [ ] Store-and-forward optimization for intermittent links
- [ ] Priority-based transmission scheduling
- [ ] Long-delay tolerance enhancements

**Bundle Layer Extensions:**
- Satellite node identifier schemes
- Orbital-aware TTL calculations
- Contact-prediction-based routing decisions

### 7.4 Phase 4: Advanced Features (Week 7-8)

**Deliverables:**
- [ ] Multi-hop satellite routing
- [ ] Inter-satellite link modeling
- [ ] Constellation reconfiguration support
- [ ] Performance optimization and profiling

## 8. Technical Specifications

### 8.1 Configuration File Format

```json
{
  "simulation": {
    "start_time": "2024-01-01T00:00:00Z",
    "duration_hours": 24,
    "time_step_seconds": 1
  },
  "constellation": {
    "type": "LEO",
    "preset": "starlink_like",
    "custom_satellites": []
  },
  "ground_stations": [
    {
      "name": "Station_1",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "altitude_m": 50,
      "antenna_diameter_m": 10,
      "min_elevation_deg": 10
    }
  ],
  "communication": {
    "frequency_ghz": 12.0,
    "bandwidth_mhz": 500,
    "tx_power_watts": 20,
    "noise_temperature_k": 150
  }
}
```

### 8.2 API Interfaces

```python
class SatelliteNode:
    def __init__(self, orbital_elements, communication_specs):
        self.orbital_elements = orbital_elements
        self.communication_specs = communication_specs
    
    def propagate_position(self, time):
        """Calculate satellite position at given time"""
        pass
    
    def calculate_contacts(self, ground_stations, duration):
        """Predict contact windows with ground stations"""
        pass
    
    def get_communication_range(self):
        """Calculate current communication range"""
        pass

class GroundStation:
    def __init__(self, location, antenna_specs):
        self.location = location
        self.antenna_specs = antenna_specs
    
    def visible_satellites(self, satellite_constellation, time):
        """Get list of currently visible satellites"""
        pass
    
    def calculate_link_budget(self, satellite):
        """Calculate communication link quality"""
        pass
```

## 9. Testing and Validation

### 9.1 Orbital Mechanics Validation

**Test Cases:**
- Compare propagated orbits with Two-Line Element (TLE) data
- Validate ground track calculations against known satellite passes
- Verify contact window predictions with real satellite tracking

### 9.2 Communication Model Validation

**Test Cases:**
- Link budget calculations against RF engineering standards
- Data rate predictions vs actual satellite communication systems
- Delay models validation with ping measurements

### 9.3 Integration Testing

**Test Scenarios:**
- End-to-end bundle transmission through satellite network
- Multi-hop routing through constellation
- Store-and-forward during communication gaps
- Priority-based transmission scheduling

---

**Document Version:** 1.0  
**Last Updated:** September 22, 2025  
**Authors:** DTN Development Team  
**Status:** Draft - Architecture Foundation