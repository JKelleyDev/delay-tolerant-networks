# Pair 2 Implementation Guide: Satellite Mobility & Data Collection

## Overview

This guide provides comprehensive implementation instructions for Pair 2 to complete the satellite mobility and data collection functionality for the DTN simulator. All boilerplate code has been created with detailed TODO comments and example usage.

## 📁 Files Created for Implementation

### Core Modules
- `src/orbital_mechanics.py` - Orbital calculations and satellite position propagation
- `src/contact_prediction.py` - Contact window prediction and visibility calculations  
- `src/satellite_mobility.py` - Mobility model integration and CSV contact plan management
- `src/constellation_config.py` - Constellation configuration and preset management

### Documentation
- `docs/satellite_communication_architecture.md` - Complete architecture specification
- `docs/pair2_implementation_guide.md` - This implementation guide

## 🎯 Implementation Priority Order

### Phase 1: Core Orbital Mechanics (Week 1-2)
**Priority: Critical** - Required for all other functionality

#### 1.1 Orbital Mechanics (`src/orbital_mechanics.py`)

**Functions to Implement:**
```python
def calculate_orbital_period(self, semi_major_axis: float) -> float:
    # Formula: T = 2π√(a³/μ)
    # μ = 398600.4418 km³/s² (Earth's gravitational parameter)
    
def calculate_orbital_velocity(self, radius: float, semi_major_axis: float) -> float:
    # Formula: v = √(μ(2/r - 1/a)) (vis-viva equation)
    
def kepler_to_cartesian(self, elements: OrbitalElements, time_offset: float = 0) -> StateVector:
    # Convert orbital elements to Cartesian coordinates
    # 1. Calculate mean anomaly from time offset
    # 2. Solve Kepler's equation for eccentric anomaly  
    # 3. Calculate true anomaly
    # 4. Transform to orbital plane coordinates
    # 5. Rotate to ECI coordinates using Euler angles
    
def propagate_orbit(self, elements: OrbitalElements, target_time: float) -> StateVector:
    # For basic implementation: Use simplified Keplerian propagation
    # For accuracy: Integrate SGP4/SDP4 algorithms using skyfield library
    
def eci_to_ecef(self, eci_position: Position3D, timestamp: float) -> Position3D:
    # Convert ECI to ECEF using Greenwich Sidereal Time
    # Account for Earth's rotation: EARTH_ROTATION_RATE = 7.2921159e-5 rad/s
    
def ecef_to_geodetic(self, ecef_position: Position3D) -> Tuple[float, float, float]:
    # Use iterative algorithm for WGS84 ellipsoid
    # Return (latitude_deg, longitude_deg, altitude_km)
    
def calculate_ground_track(self, state_vector: StateVector) -> Tuple[float, float]:
    # 1. Convert ECI to ECEF
    # 2. Convert ECEF to geodetic  
    # 3. Return (latitude, longitude)
```

**Key Constants:**
```python
EARTH_RADIUS = 6378.137      # km (WGS84)
EARTH_MU = 398600.4418       # km³/s² (gravitational parameter)
EARTH_ROTATION_RATE = 7.2921159e-5  # rad/s (sidereal)
```

**Testing Strategy:**
- Compare results with online orbital calculators
- Validate ground tracks against known satellite passes
- Test with ISS orbital elements from TLE data

#### 1.2 Constellation Generation (`src/constellation_config.py`)

**Functions to Implement:**
```python
def generate_walker_constellation(self, params: ConstellationParameters) -> List[OrbitalElements]:
    # 1. Calculate satellites per plane = total_satellites / orbital_planes
    # 2. RAAN spacing = 360° / orbital_planes  
    # 3. Satellite spacing in plane = 360° / satellites_per_plane
    # 4. Generate OrbitalElements for each satellite
    
def build_preset_constellation(self, preset_name: str) -> ConstellationConfig:
    # Use PRESET_CONSTELLATIONS dictionary
    # Generate satellites using preset parameters
    # Add default ground stations and communication config
```

**Preset Parameters (from architecture doc):**
```python
LEO_IRIDIUM = {
    "satellites": 66, "planes": 6, "altitude": 780, "inclination": 86.4
}
LEO_STARLINK = {  
    "satellites": 1584, "planes": 72, "altitude": 550, "inclination": 53
}
MEO_GPS = {
    "satellites": 24, "planes": 6, "altitude": 20200, "inclination": 55
}
GEO_MINIMAL = {
    "satellites": 3, "planes": 1, "altitude": 35786, "inclination": 0
}
```

### Phase 2: Contact Prediction (Week 2-3)
**Priority: High** - Required for DTN routing

#### 2.1 Line-of-Sight Calculations (`src/contact_prediction.py`)

**Functions to Implement:**
```python
def calculate_elevation_azimuth(self, satellite_position: Position3D, 
                               ground_station: GroundStation, timestamp: float) -> Tuple[float, float]:
    # 1. Convert satellite ECI to ECEF
    # 2. Convert ground station geodetic to ECEF
    # 3. Calculate range vector: satellite_ecef - station_ecef
    # 4. Transform to topocentric (SEZ) coordinates
    # 5. Calculate elevation = arcsin(z_component / range_magnitude)
    # 6. Calculate azimuth = arctan2(east, north)
    
def is_visible(self, satellite_position: Position3D, ground_station: GroundStation, 
               timestamp: float) -> bool:
    # elevation_deg = calculate_elevation_azimuth(...)[0]
    # return elevation_deg > ground_station.min_elevation_deg
    
def predict_contact_windows(self, satellite_elements: OrbitalElements, 
                           satellite_id: str, ground_station_name: str,
                           start_time: float, duration_hours: float) -> List[ContactWindow]:
    # 1. Loop through time with 60-second steps
    # 2. Propagate satellite orbit at each step
    # 3. Check visibility using is_visible()
    # 4. Track contact start/end times
    # 5. Calculate max elevation and average data rate
    # 6. Create ContactWindow objects
```

**Mathematical References:**
- Elevation angle: `elevation = arcsin(z_topocentric / range)`
- Azimuth angle: `azimuth = arctan2(east, north)`
- Minimum elevation: 5-10° for reliable communications

#### 2.2 Contact Quality Metrics

**Functions to Implement:**
```python
def calculate_contact_quality(self, satellite_position: Position3D, satellite_velocity: Velocity3D,
                             ground_station: GroundStation, timestamp: float) -> ContactQuality:
    # Calculate elevation, azimuth, range
    # Estimate data rate based on range and elevation
    # Calculate Doppler shift from relative velocity
    # Estimate signal strength from link budget
```

**Link Budget Calculations:**
```python
# Free Space Path Loss: FSPL(dB) = 20log₁₀(d) + 20log₁₀(f) + 92.45
# Data rate estimation based on range and elevation
# Higher elevation = better data rate (less atmospheric attenuation)
```

### Phase 3: Mobility Integration (Week 3-4)  
**Priority: High** - Integration with DTN framework

#### 3.1 Satellite Mobility Model (`src/satellite_mobility.py`)

**Functions to Implement:**
```python
def get_mobility_state(self, node_id: str, timestamp: float) -> Optional[MobilityState]:
    # For satellites: propagate orbit and convert to lat/lon/alt
    # For ground stations: return fixed position with zero velocity
    # Calculate velocity magnitude and heading from orbital velocity
    
def update_positions(self, timestamp: float) -> Dict[str, MobilityState]:
    # Batch update all satellite and ground station positions
    # Log mobility states for experiment data collection
    # Return dictionary mapping node_id to MobilityState
```

**Integration Points:**
- DTN routing algorithms need current node positions
- GUI needs real-time position updates for visualization
- Experiment framework needs mobility logs for analysis

#### 3.2 CSV Contact Plan Management

**Functions to Implement:**
```python
def load_contact_plan_csv(self, csv_file: Path) -> List[ContactPlanEntry]:
    # Parse CSV with columns: start_time,end_time,source_node,dest_node,data_rate_kbps,range_km,delay_ms
    # Handle Unix timestamps and ISO 8601 formats
    # Validate data and handle parsing errors
    
def save_contact_plan_csv(self, csv_file: Path, contact_plan: List[ContactPlanEntry]) -> None:
    # Export contact plan to CSV format
    # Include both Unix timestamps and human-readable times
    # Add headers and proper formatting
    
def generate_contact_plan(self, start_time: float, duration_hours: float) -> List[ContactPlanEntry]:
    # For each satellite-ground station pair:
    # 1. Predict contact windows
    # 2. Convert to ContactPlanEntry objects  
    # 3. Merge and sort by time
    # 4. Add inter-satellite links if configured
```

### Phase 4: Advanced Features (Week 4-5)
**Priority: Medium** - Enhanced functionality

#### 4.1 Real-time Contact Management

**Functions to Implement:**
```python
def get_current_contacts(self, constellation: List[Tuple[OrbitalElements, str]], 
                        current_time: float) -> Dict[str, List[str]]:
    # Efficiently determine which satellites are currently visible
    # Return mapping: ground_station_name -> [visible_satellite_ids]
    
def get_next_contact(self, satellite_id: str, ground_station: str, 
                    after_time: float) -> Optional[ContactWindow]:
    # Find next contact window for routing decisions
    # Used by DTN algorithms for store-and-forward timing
```

#### 4.2 Experiment Data Collection

**Functions to Implement:**
```python
def collect_network_state(self, timestamp: float) -> Dict[str, Any]:
    # Capture complete network snapshot:
    # - All node positions and velocities
    # - Active contact links and qualities
    # - Buffer states and message queues
    # - Network topology and routing tables
    
def export_experiment_data(self, output_dir: Path) -> None:
    # Export mobility logs, contact plans, network states
    # Create JSON and CSV formats for analysis
    # Generate visualization-ready data files
```

## 🔧 Dependencies and Setup

### Required Python Packages
```bash
pip install numpy scipy skyfield
```

### Optional Dependencies for Advanced Features
```bash
pip install matplotlib  # For plotting orbits and ground tracks
pip install pandas      # For CSV data manipulation  
pip install astropy     # For advanced astronomical calculations
```

### Development Setup
```bash
# Install development dependencies
make dev-setup

# Run tests during development
make test

# Check code quality
make all
```

## 🧪 Testing Strategy

### Unit Tests
Create test files in `tests/` directory:
- `tests/test_orbital_mechanics.py`
- `tests/test_contact_prediction.py`  
- `tests/test_satellite_mobility.py`
- `tests/test_constellation_config.py`

### Test Data Sources
- **TLE Data:** Use Two-Line Element sets from CelesTrak for validation
- **Known Satellites:** ISS, GPS satellites with published orbital elements
- **Ground Stations:** Real station coordinates for testing

### Validation Techniques
```python
# Example orbital mechanics validation
def test_iss_orbital_period():
    iss_elements = OrbitalElements(semi_major_axis=6793.0, ...)
    period = orbital_calc.calculate_orbital_period(iss_elements.semi_major_axis)
    expected_period = 5580  # seconds (93 minutes)
    assert abs(period - expected_period) < 60  # Within 1 minute

# Example contact prediction validation  
def test_ground_track_accuracy():
    # Compare calculated ground track with known satellite pass
    calculated_lat, calculated_lon = orbital_calc.calculate_ground_track(state)
    # Use published satellite tracking data for validation
    assert abs(calculated_lat - expected_lat) < 0.1  # Within 0.1 degrees
```

## 🔗 Integration Points

### With Pair 1 (Core Networking)
```python
# DTN routing needs current positions for contact-aware routing
mobility_state = mobility_model.get_mobility_state("SAT_001", current_time)

# Contact prediction for store-and-forward decisions
next_contact = contact_pred.get_next_contact("SAT_001", "GS_001", current_time)
```

### With Pair 3 (GUI & Visualization)
```python
# Real-time position updates for 3D visualization
positions = mobility_model.update_positions(current_time)

# Contact window timeline for GUI display
contacts = contact_pred.predict_contact_windows(sat_elements, "SAT_001", "GS_001", 
                                               start_time, 24.0)

# Constellation configuration for user selection
constellation = constellation_manager.load_constellation("leo_starlink")
```

### Data Exchange Formats
```python
# Position updates for GUI (JSON)
{
    "timestamp": 1695824400.123,
    "nodes": {
        "SAT_001": {
            "latitude": 45.5,
            "longitude": -73.6, 
            "altitude": 550.0,
            "velocity_kmh": 27400.0
        }
    }
}

# Contact plan for DTN routing (CSV)
start_time,end_time,source_node,dest_node,data_rate_kbps,range_km,delay_ms
1695824400,1695824700,SAT_001,GS_001,50000,1500,5.0
```

## 📊 Performance Requirements

### Real-time Operation
- **Position Updates:** 1-10 Hz for smooth GUI animation
- **Contact Checking:** < 100ms for routing decisions
- **Orbit Propagation:** < 10ms per satellite per time step

### Scalability Targets
- **Small Constellation:** 66 satellites (Iridium-like) - real-time operation
- **Large Constellation:** 1584 satellites (Starlink-like) - 1-10x real-time
- **Ground Stations:** 50-200 stations with minimal performance impact

### Memory Usage
- Keep orbital elements and contact plans in memory for fast access
- Stream mobility logs to disk for large experiments
- Use efficient data structures for contact window storage

## 🚀 Example Implementation Sequence

### Day 1-2: Basic Orbital Mechanics
```python
# Start with simple circular orbits
def calculate_orbital_period(self, semi_major_axis: float) -> float:
    return 2 * math.pi * math.sqrt(semi_major_axis**3 / self.EARTH_MU)

# Test with ISS parameters
iss_period = calc.calculate_orbital_period(6793.0)  # Should be ~93 minutes
```

### Day 3-4: Coordinate Transformations
```python
# Implement ECI to ECEF conversion
def eci_to_ecef(self, eci_position: Position3D, timestamp: float) -> Position3D:
    gst = self._greenwich_sidereal_time(timestamp)
    # Apply rotation matrix for Earth's rotation
    
# Test with known satellite positions
```

### Day 5-7: Contact Prediction
```python
# Start with simple elevation calculation
def calculate_elevation(self, sat_pos: Position3D, ground_station: GroundStation, 
                       timestamp: float) -> float:
    # Convert coordinates and calculate elevation angle
    
# Test with known satellite passes
```

### Day 8-10: Integration and Testing
```python
# Integrate all components
mobility_model = SatelliteMobilityModel(orbital_calc, contact_pred)
constellation = constellation_builder.build_preset_constellation("leo_iridium")

# Run end-to-end tests
contacts = mobility_model.generate_contact_plan(start_time, 24.0)
```

## 📖 Mathematical Resources

### Orbital Mechanics References
- **Vallado's "Fundamentals of Astrodynamics and Applications"** - Comprehensive orbital mechanics textbook
- **Curtis's "Orbital Mechanics for Engineering Students"** - Practical engineering approach  
- **NASA's "Orbital Mechanics"** - Free online course materials

### Online Calculators for Validation
- **AGI Systems Tool Kit (STK)** - Professional satellite analysis software
- **GMAT (General Mission Analysis Tool)** - NASA's free orbital analysis software
- **Online orbital calculators** - For quick validation of calculations

### Key Equations Reference
```python
# Orbital period (Kepler's 3rd law)
T = 2π√(a³/μ)

# Orbital velocity (vis-viva equation)  
v = √(μ(2/r - 1/a))

# Ground track longitude
lon = arctan2(y_ecef, x_ecef) - (ω_earth * t)

# Elevation angle
elevation = arcsin(z_topocentric / range)

# Free space path loss
FSPL_dB = 20*log10(distance_km) + 20*log10(frequency_ghz) + 92.45
```

## 🐛 Common Implementation Pitfalls

### Coordinate System Confusion
- **Problem:** Mixing ECI, ECEF, and geodetic coordinates
- **Solution:** Clearly document coordinate system for each function
- **Test:** Validate conversions with known reference points

### Time System Issues  
- **Problem:** Mixing UTC, GPS time, and Julian dates
- **Solution:** Use Unix timestamps consistently throughout
- **Test:** Verify time conversions with astronomical libraries

### Angle Unit Confusion
- **Problem:** Mixing degrees and radians
- **Solution:** Use degrees for user interface, radians for calculations
- **Test:** Add unit tests for angle conversions

### Numerical Precision
- **Problem:** Loss of precision in orbital calculations
- **Solution:** Use appropriate data types (float64) and validate ranges
- **Test:** Compare results with high-precision reference implementations

## 🎯 Success Criteria

### Minimum Viable Implementation
- [ ] Basic orbital mechanics working (period, velocity calculations)
- [ ] Simple contact prediction (elevation angles, visibility windows)
- [ ] Preset constellation generation (at least LEO and GEO)
- [ ] CSV contact plan export/import
- [ ] Integration with existing DTN bundle system

### Full Implementation
- [ ] All TODO functions implemented and tested
- [ ] Support for all constellation types (LEO, MEO, GEO, HEO)
- [ ] Real-time position updates for GUI
- [ ] Comprehensive experiment data collection
- [ ] Performance optimization for large constellations
- [ ] Complete test suite with >80% coverage

### Integration Success
- [ ] GUI can display real-time satellite positions
- [ ] DTN routing algorithms can use contact predictions
- [ ] Experiment framework can collect mobility and contact data
- [ ] Contact plans can be exported for external analysis tools

---

**Next Steps:**
1. Start with `src/orbital_mechanics.py` basic functions
2. Test thoroughly with known satellite data
3. Gradually build up to full contact prediction
4. Integrate with GUI as functions become available
5. Add comprehensive testing throughout development

**Questions/Support:**
- Architecture questions: Reference `docs/satellite_communication_architecture.md`
- Integration questions: Coordinate with Pair 1 and Pair 3
- Implementation questions: Check TODO comments in boilerplate code