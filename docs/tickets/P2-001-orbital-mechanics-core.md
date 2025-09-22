# P2-001: Implement Core Orbital Mechanics Calculations

**Epic:** Satellite Mobility & Data Collection  
**Priority:** Critical  
**Story Points:** 8  
**Assignee:** Pair 2  
**Labels:** `satellite`, `orbital-mechanics`, `core-functionality`

## Overview

Implement the fundamental orbital mechanics calculations required for satellite position propagation and coordinate system transformations. This is the foundation module that all other satellite functionality depends on.

## User Story

As a DTN simulation developer, I need accurate orbital mechanics calculations so that satellites can be positioned correctly in 3D space and their motion can be predicted over time for contact window calculations.

## Technical Requirements

### Core Functions to Implement

#### 1. Orbital Period Calculation (`calculate_orbital_period`)
```python
def calculate_orbital_period(self, semi_major_axis: float) -> float:
    # Formula: T = 2π√(a³/μ)
    # μ = 398600.4418 km³/s² (Earth's gravitational parameter)
```

#### 2. Orbital Velocity Calculation (`calculate_orbital_velocity`) 
```python
def calculate_orbital_velocity(self, radius: float, semi_major_axis: float) -> float:
    # Formula: v = √(μ(2/r - 1/a)) (vis-viva equation)
```

#### 3. Keplerian to Cartesian Conversion (`kepler_to_cartesian`)
```python
def kepler_to_cartesian(self, elements: OrbitalElements, time_offset: float = 0) -> StateVector:
    # Convert orbital elements to ECI Cartesian coordinates
    # Steps: Mean anomaly → Eccentric anomaly → True anomaly → ECI position/velocity
```

#### 4. Orbit Propagation (`propagate_orbit`)
```python
def propagate_orbit(self, elements: OrbitalElements, target_time: float) -> StateVector:
    # Propagate satellite position from epoch to target time
    # Use simplified Keplerian propagation for MVP
```

#### 5. Coordinate System Transformations
```python
def eci_to_ecef(self, eci_position: Position3D, timestamp: float) -> Position3D:
    # Convert ECI to ECEF using Greenwich Sidereal Time
    
def ecef_to_geodetic(self, ecef_position: Position3D) -> Tuple[float, float, float]:
    # Convert ECEF to latitude/longitude/altitude using WGS84 ellipsoid
    
def calculate_ground_track(self, state_vector: StateVector) -> Tuple[float, float]:
    # Calculate subsatellite point (latitude, longitude)
```

### Mathematical Constants
```python
EARTH_RADIUS = 6378.137      # km (WGS84)
EARTH_MU = 398600.4418       # km³/s² (gravitational parameter) 
EARTH_ROTATION_RATE = 7.2921159e-5  # rad/s (sidereal)
```

## Acceptance Criteria

### Functional Requirements
- [ ] All orbital period calculations accurate within 1% of known values
- [ ] Orbital velocity calculations match vis-viva equation results
- [ ] Keplerian to Cartesian conversion produces valid ECI coordinates
- [ ] Orbit propagation maintains orbital energy conservation (for circular orbits)
- [ ] ECI to ECEF conversion accounts for Earth rotation correctly
- [ ] ECEF to geodetic conversion accurate within 1 meter for test points
- [ ] Ground track calculations match expected subsatellite points

### Validation Requirements
- [ ] ISS orbital period: ~93 minutes (5580 seconds ±60 seconds)
- [ ] LEO velocity at 550km: ~7.6 km/s (±0.1 km/s)
- [ ] GEO orbital period: 24 hours (86400 seconds ±300 seconds)
- [ ] Known satellite ground tracks match TLE predictions within 0.1°

### Performance Requirements
- [ ] Single orbit propagation: < 10ms
- [ ] Coordinate transformation: < 1ms
- [ ] Batch processing 1000 satellites: < 1 second

### Code Quality Requirements
- [ ] All functions have comprehensive docstrings with formulas
- [ ] Type hints for all parameters and return values
- [ ] Unit tests with >90% coverage
- [ ] Pass all linting (flake8) and type checking (mypy)

## Implementation Notes

### Dependencies
```bash
pip install numpy scipy  # For mathematical operations
pip install skyfield     # Optional: For high-accuracy TLE propagation
```

### Test Data Sources
- **ISS TLE Data:** Use current ISS orbital elements from CelesTrak
- **GPS Satellites:** Known MEO orbital parameters
- **Reference Points:** Use established geodetic coordinates for validation

### Validation Strategy
1. **Unit Tests:** Test each function with known inputs/outputs
2. **Integration Tests:** Compare full propagation with online orbital calculators
3. **Cross-validation:** Check results against established astronomy libraries

## Definition of Done

- [ ] All 6 core functions implemented and tested
- [ ] Mathematical accuracy validated against reference data
- [ ] Performance benchmarks meet requirements  
- [ ] Documentation includes formula references and examples
- [ ] Integration tests pass with known satellite data
- [ ] Code reviewed and approved by team
- [ ] No blocking issues in CI/CD pipeline

## Dependencies

**Blocked by:** None (foundation module)  
**Blocks:** P2-002 (Contact Prediction), P2-003 (Mobility Integration)

## Resources

- **Vallado's "Fundamentals of Astrodynamics"** - Orbital mechanics reference
- **CelesTrak:** https://celestrak.org - TLE data for validation
- **NASA GMAT:** Free orbital analysis software for cross-validation
- **Architecture Doc:** `docs/satellite_communication_architecture.md`

## Time Estimate

**Total:** 3-4 days
- Day 1: Basic orbital calculations (period, velocity)
- Day 2: Keplerian to Cartesian conversion
- Day 3: Coordinate transformations (ECI/ECEF/geodetic)
- Day 4: Testing, validation, and performance optimization