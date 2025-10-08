# P2-001: Core Orbital Mechanics Module

**Epic Owner:** Pair 2  
**Priority:** Critical  
**Total Story Points:** 8  
**Timeline:** 1 week  
**Status:** Ready for Development

## Epic Overview

Implement core orbital mechanics functionality for the DTN simulator, including:

- Orbital period and velocity calculations  
- Keplerian to Cartesian conversion  
- Orbit propagation  
- ECI ↔ ECEF coordinate transformations  
- Ground track calculation  

This module forms the foundation for accurate satellite mobility, contact prediction, and constellation simulation.

## Business Value

This module provides the basis for:

- **Accurate satellite position calculations** supporting mobility and routing  
- **Contact window prediction** via reliable orbital mechanics  
- **Integration with GUI** for real-time visualization  
- **Validation against known satellite data** (ISS, LEO, GEO)  
- **Framework for research and experiment data collection**

## Epic Goals

1. **Foundation:** Accurate orbital mechanics calculations  
2. **Validation:** Comparison against known satellite parameters and TLE data  
3. **Performance:** Fast propagation and coordinate transformation for real-time simulation  
4. **Integration:** Provides interfaces for contact prediction, GUI, and mobility modules  
5. **Documentation:** Include formulas, references, and example workflows  

## Tickets in Epic

### Critical Path
- **P2-001a: Implement Orbital Period & Velocity Calculations**  
  - Semi-major axis → orbital period  
  - Vis-viva equation → orbital velocity  

- **P2-001b: Implement Keplerian to Cartesian Conversion**  
  - ECI coordinates computation from orbital elements  
  - Circular and elliptical orbits supported  

- **P2-001c: Implement Orbit Propagation**  
  - Propagation over time  
  - Energy conservation check  

- **P2-001d: Implement ECI ↔ ECEF & Geodetic Conversion**  
  - Earth rotation accounted for in ECEF  
  - Latitude, longitude, altitude computation  

- **P2-001e: Implement Ground Track Calculation**  
  - Subsatellite point computation  
  - Validation against TLE-derived positions  

## Dependencies

### External Dependencies
- **Skyfield:** TLE parsing and reference validation  
- **NumPy/SciPy:** Mathematical operations  

### Internal Dependencies
\`\`\`mermaid
graph TD
    P2001a --> P2001b;
    P2001b --> P2001c;
    P2001c --> P2001d;
    P2001d --> P2001e;
\`\`\`

## Technical Architecture

### Module Structure
```text
src/
├── orbital_mechanics.py      # Core calculations (P2-001)
tests/
├── test_orbital_mechanics.py  # Unit tests for all functionality
```

### Core Functions

| Function | Description | Accuracy/Validation |
|----------|-------------|------------------|
| `calculate_orbital_period(a)` | Computes orbital period from semi-major axis | ±1% |
| `calculate_orbital_velocity(r, a)` | Computes velocity via Vis-viva equation | ±0.1 km/s |
| `kepler_to_cartesian(elements)` | Converts orbital elements → ECI coordinates | Validated |
| `propagate_orbit(elements, t)` | Propagates orbit over time | Energy conservation |
| `eci_to_ecef(pos, t)` | Converts ECI → ECEF | Earth rotation accounted |
| `ecef_to_geodetic(pos)` | ECEF → lat/lon/alt | ±1 m |
| `calculate_ground_track(state)` | Returns lat/lon subsatellite point | Compared to Skyfield TLE |

### Diagrams

#### Orbital Elements (ASCII)
```text
                ↑ z-axis (ECI)
                |
                |
                |          * Satellite position
                |
----------------+-----------------> x-axis (ECI)
               /
              / y-axis (ECI)

Orbital Elements:
- a: Semi-major axis
- e: Eccentricity
- i: Inclination
- Ω: RAAN
- ω: Argument of perigee
- ν: True anomaly
```

#### Ground Track (ASCII)
```text
   90°N
    ^
    *
    |
0°W +--------------------> 0°E
    *
    |
   90°S
```
## Success Criteria

### Functional Requirements
- [x] Orbital period calculations ±1% of known values  
- [x] Orbital velocity matches Vis-viva equation  
- [x] Keplerian → Cartesian conversion produces valid ECI coordinates  
- [x] Orbit propagation maintains energy conservation  
- [x] ECI ↔ ECEF conversion correct for Earth rotation  
- [x] ECEF → geodetic accurate ±1 m  
- [x] Ground track lat/lon ranges valid  

### Validation Requirements
- [x] ISS orbital period: ~5580 s ±60 s  
- [x] LEO velocity (550 km): ~7.6 km/s ±0.1  
- [x] GEO orbital period: 86400 s ±300 s  
- [ ] Ground track within 0.1° of TLE (simplified: delta relaxed)  

### Performance Requirements
- [x] Single orbit propagation <10 ms  
- [x] Coordinate transformation <1 ms  
- [x] Batch processing 1000 satellites <1 s  

### Quality Requirements
- [x] All functions documented with formulas  
- [x] Type hints included  
- [x] Unit tests >90% coverage  
- [x] Linting and type checks pass  

## Risk Assessment

### High Risk
- **Orbital mechanics complexity**  
  - Mitigation: Reference texts, TLE validation  

### Medium Risk
- **Performance for large satellite sets**  
  - Mitigation: Efficient propagation, caching  

### Low Risk
- **Integration complexity**  
  - Mitigation: Clear API and unit tests  

## Timeline

### Week 1
- Days 1-3: Implement orbital period, velocity, and Kepler → Cartesian  
- Days 3-5: Orbit propagation and energy conservation  
- Days 5-7: ECI ↔ ECEF, geodetic conversion, and ground track calculations  

## Deliverables

### Code
- [x] `orbital_mechanics.py` fully implemented  
- [x] Unit tests in `test_orbital_mechanics.py`  

### Documentation
- [x] Formulas and ASCII diagrams included  
- [x] Usage examples in tests  

### Data
- [x] TLE-based validation datasets  

## Acceptance Criteria
- [x] All functions implemented and tested  
- [x] Performance benchmarks met  
- [x] Documentation complete  
- [x] Integration with DTN mobility framework feasible  

## Resources

### References
- **Vallado, "Fundamentals of Astrodynamics"**  
- **Curtis, "Orbital Mechanics for Engineering Students"**  
- **NASA GMAT, CelesTrak TLE data**  

### Development Tools
- Python, NumPy, SciPy, Skyfield, unittest, coverage
"""

