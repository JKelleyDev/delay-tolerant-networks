# P2-002: Implement Contact Window Prediction System

**Epic:** Satellite Mobility & Data Collection  
**Priority:** High  
**Story Points:** 13  
**Assignee:** Pair 2  
**Labels:** `satellite`, `contact-prediction`, `line-of-sight`, `visibility`

## Overview

Implement contact window prediction between satellites and ground stations, including line-of-sight calculations, elevation/azimuth angles, and contact quality metrics. This enables DTN routing algorithms to make informed decisions about when communication links will be available.

## User Story

As a DTN routing algorithm, I need to know when satellites will be visible from ground stations so that I can schedule message transmission during contact windows and implement store-and-forward strategies during communication gaps.

## Technical Requirements

### Core Functions to Implement

#### 1. Ground Station ECEF Conversion (`GroundStation.to_ecef_position`)
```python
def to_ecef_position(self) -> Position3D:
    # Convert latitude/longitude/altitude to ECEF coordinates
    # Use WGS84 ellipsoid parameters for accuracy
```

#### 2. Elevation and Azimuth Calculation (`calculate_elevation_azimuth`)
```python
def calculate_elevation_azimuth(self, satellite_position: Position3D, 
                               ground_station: GroundStation, timestamp: float) -> Tuple[float, float]:
    # Steps:
    # 1. Convert satellite ECI to ECEF
    # 2. Calculate range vector from station to satellite
    # 3. Transform to topocentric (SEZ) coordinates
    # 4. Calculate elevation = arcsin(z_component / range)
    # 5. Calculate azimuth = arctan2(east, north)
```

#### 3. Range Calculation (`calculate_range`)
```python
def calculate_range(self, satellite_position: Position3D, 
                   ground_station: GroundStation, timestamp: float) -> float:
    # Calculate Euclidean distance between satellite and ground station
    # Account for coordinate system transformations
```

#### 4. Visibility Check (`is_visible`)
```python
def is_visible(self, satellite_position: Position3D, 
               ground_station: GroundStation, timestamp: float) -> bool:
    # Return True if elevation > min_elevation_deg
    # Consider Earth obstruction and atmospheric effects
```

#### 5. Contact Window Prediction (`predict_contact_windows`)
```python
def predict_contact_windows(self, satellite_elements: OrbitalElements, 
                           satellite_id: str, ground_station_name: str,
                           start_time: float, duration_hours: float) -> List[ContactWindow]:
    # Algorithm:
    # 1. Loop through time with 60-second steps
    # 2. Propagate satellite orbit at each step
    # 3. Check visibility using is_visible()
    # 4. Track contact start/end times
    # 5. Calculate max elevation and quality metrics
```

#### 6. Contact Quality Assessment (`calculate_contact_quality`)
```python
def calculate_contact_quality(self, satellite_position: Position3D, 
                             satellite_velocity: Velocity3D,
                             ground_station: GroundStation, timestamp: float) -> ContactQuality:
    # Metrics: elevation, azimuth, range, data_rate, signal_strength, doppler_shift
```

### Data Structures

#### ContactWindow
```python
class ContactWindow(NamedTuple):
    satellite_id: str
    ground_station: str
    start_time: float      # Unix timestamp
    end_time: float        # Unix timestamp  
    duration_seconds: float
    max_elevation_deg: float
    max_data_rate_mbps: float
    average_range_km: float
```

#### ContactQuality
```python
@dataclass
class ContactQuality:
    elevation_deg: float
    azimuth_deg: float
    range_km: float
    data_rate_mbps: float
    signal_strength_db: float
    doppler_shift_hz: float
```

## Acceptance Criteria

### Functional Requirements
- [ ] Elevation angle calculations accurate within 0.1 degrees
- [ ] Azimuth calculations properly handle all quadrants (0-360°)
- [ ] Range calculations accurate within 1 km for LEO satellites
- [ ] Visibility checks respect minimum elevation constraints
- [ ] Contact windows correctly identify start/end times
- [ ] Contact quality metrics include all required parameters

### Mathematical Accuracy
- [ ] Elevation angle: `elevation = arcsin(z_topocentric / range)`
- [ ] Azimuth angle: `azimuth = arctan2(east, north)` 
- [ ] Range calculation uses proper coordinate transformations
- [ ] Minimum elevation: 5° (basic), 10° (high quality)

### Performance Requirements
- [ ] Single visibility check: < 1ms
- [ ] 24-hour contact prediction: < 5 seconds per satellite-station pair
- [ ] Real-time contact checking for 100 satellites: < 100ms
- [ ] Memory usage: < 10MB for 24-hour contact plan

### Validation Requirements
- [ ] ISS passes over known ground stations match published schedules
- [ ] Contact durations for LEO: 2-15 minutes per pass
- [ ] Contact frequency for LEO: 4-8 passes per day per satellite
- [ ] MEO contact durations: 1-8 hours per pass

## Implementation Notes

### Ground Station Presets
```python
PRESET_GROUND_STATIONS = {
    "svalbard": GroundStation(lat=78.92, lon=11.93, alt=78m, min_elev=5°),
    "alaska": GroundStation(lat=64.86, lon=-147.85, alt=200m, min_elev=10°),
    "australia": GroundStation(lat=-23.70, lon=133.88, alt=545m, min_elev=10°),
    "chile": GroundStation(lat=-33.45, lon=-70.67, alt=520m, min_elev=10°)
}
```

### Link Budget Calculations
```python
# Free Space Path Loss: FSPL(dB) = 20log₁₀(d) + 20log₁₀(f) + 92.45
# Data rate estimation based on range and elevation
# Higher elevation = better data rate (less atmospheric attenuation)
```

### Time Step Optimization
- **Coarse search:** 60-second steps for initial contact detection
- **Fine search:** 1-second steps around contact boundaries
- **Adaptive stepping:** Larger steps during non-contact periods

## Test Cases

### Unit Tests
- [ ] Test elevation calculation with known satellite positions
- [ ] Test azimuth calculation for all quadrants
- [ ] Test range calculation with various satellite altitudes
- [ ] Test visibility with satellites above/below horizon
- [ ] Test contact window detection with simulated orbits

### Integration Tests  
- [ ] Compare ISS contact predictions with real tracking data
- [ ] Validate contact durations against orbital mechanics theory
- [ ] Test with multiple constellation types (LEO, MEO, GEO)
- [ ] Cross-validate with online satellite tracking tools

### Edge Cases
- [ ] Polar ground stations with high-inclination satellites
- [ ] GEO satellites at horizon limits (±70° latitude)
- [ ] Satellites passing directly overhead (90° elevation)
- [ ] Multiple satellites visible simultaneously

## Definition of Done

- [ ] All 6 core functions implemented with proper error handling
- [ ] Contact window prediction working for all orbit types
- [ ] Contact quality metrics calculation complete
- [ ] Real-time contact checking optimized for performance
- [ ] Comprehensive test suite with >85% coverage
- [ ] Validation against known satellite tracking data
- [ ] Integration with orbital mechanics module verified
- [ ] Performance benchmarks meet requirements
- [ ] Documentation includes usage examples and API reference

## Dependencies

**Depends on:** P2-001 (Orbital Mechanics Core)  
**Blocks:** P2-003 (Mobility Integration), P2-004 (Constellation Management)

## Integration Points

### With Orbital Mechanics Module
```python
# Use orbital propagation for satellite positions
state = orbital_mechanics.propagate_orbit(elements, timestamp)
visible = contact_predictor.is_visible(state.position, ground_station, timestamp)
```

### With DTN Routing (Pair 1)
```python
# Provide contact predictions for routing decisions
next_contact = contact_predictor.get_next_contact("SAT_001", "GS_001", current_time)
if next_contact:
    route_bundle_for_transmission(bundle, next_contact)
```

### With GUI (Pair 3)
```python
# Real-time contact visualization
current_contacts = contact_predictor.get_current_contacts(constellation, time.time())
gui.update_contact_links(current_contacts)
```

## Resources

- **Satellite Tracking Theory:** David Vallado's orbital mechanics textbook
- **Validation Data:** N2YO.com, CelesTrak satellite tracking
- **Coordinate Systems:** IERS conventions for Earth orientation
- **Test Satellites:** ISS, GPS constellation, Iridium satellites

## Time Estimate

**Total:** 4-5 days
- Day 1: Ground station coordinate conversion and basic visibility
- Day 2: Elevation/azimuth calculations and range determination  
- Day 3: Contact window prediction algorithm
- Day 4: Contact quality metrics and performance optimization
- Day 5: Testing, validation, and integration