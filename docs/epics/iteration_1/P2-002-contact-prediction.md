# P2-002: Contact Window Prediction Module

**Epic Owner:** Pair 2  
**Priority:** High  
**Total Story Points:** 8  
**Timeline:** 1 week  
**Status:** Ready for Development

## Epic Overview

Implement a robust contact prediction and quality estimation subsystem for the DTN simulator. This includes line-of-sight visibility calculations, contact window detection, contact quality metrics (range, elevation, data rate, doppler), and light-weight scheduling helpers. The work will integrate with the existing `orbital_mechanics` module and provide APIs used by higher-level routing, scheduling, and GUI components.

Files in scope:
- `src/contact_prediction.py` — contact prediction implementation
- `src/test_contact_prediction.py` — unit, integration and edge tests

## Business Value

- Provide accurate contact windows for DTN routing and store-and-forward planning.  
- Enable scheduling and bandwidth planning between satellites and ground stations.  
- Allow trade-off studies (antenna sizes, elevation masks, frequency bands) using contact quality metrics.  
- Support GUI visualization of passes and integration with experiment data collection.

## Epic Goals

1. Accurate, reproducible contact window detection for LEO/MEO/GEO orbits.  
2. Contact quality metrics (elevation, azimuth, range, doppler, estimated data rate).  
3. Integration with `orbital_mechanics` for ECI→ECEF transforms and propagation.  
4. Reasonable performance so prediction and real-time checks can be used interactively.  
5. Complete test coverage and documentation showing usage examples.

## Tickets in Epic

### Critical Path
- **P2-002a: Implement ECEF conversion & ground-station model**
  - GroundStation dataclass, geodetic→ECEF conversion, min elevation config.

- **P2-002b: Implement elevation/azimuth/visibility math**
  - ECEF→ENU topocentric conversion, elevation via arcsin(up / range), azimuth via arctan2(east, north).

- **P2-002c: Implement contact window detection**
  - Kepler propagation loop, visibility thresholding, pass identification and aggregation.

- **P2-002d: Contact quality metrics**
  - Slant range, FSPL-based signal estimate, data rate model, doppler estimate using relative radial velocity.

- **P2-002e: Scheduler helpers and exports**
  - Light-weight ContactScheduler to store lists of `ContactWindow`, CSV export for external tools.

### Secondary
- **P2-002f: Batch prediction & real-time checks**
  - predict_all_contacts, get_current_contacts — optimized for many satellites.

- **P2-002g: Integration tests with TLE/SGP4**
  - Validate predicted passes against skyfield/SGP4-derived passes for ISS and sample LEO satellites.

## Dependencies

### External
- astropy — for robust coordinate transforms when needed  
- numpy — vector math  
- skyfield / sgp4 (optional) — for TLE/SGP4 validation

### Internal
- `src/orbital_mechanics.py` — ECI propagation and ECI↔ECEF helpers

## Technical Architecture

### Module Structure
```
src/
├── contact_prediction.py        # Contact prediction and scheduling
tests/
├── test_contact_prediction.py   # Unit & integration tests
docs/
├── epics/iteration_1/P2-002-contact-prediction.md
```

### Core functions (priority list)

| Function | Purpose | Unit / Notes |
|---|---:|---|
| `GroundStation.to_ecef_position()` | Convert geodetic to ECEF (meters) | returns `Position3D` (meters)
| `calculate_elevation_azimuth()` | Compute elevation & azimuth from GS→sat | elevation: deg, azimuth: deg [0,360)
| `calculate_range()` | Slant range (meters) between GS and sat | uses ECEF transforms
| `is_visible()` | Boolean above GS min elevation | respects `GroundStation.min_elevation_deg`
| `predict_contact_windows()` | Predict contact windows for a satellite/station | Kepler propagation loop, returns list of `ContactWindow`
| `calculate_contact_quality()` | Compute elevation, azimuth, range_km, data_rate, signal_strength_db, doppler | returns `ContactQuality`

### Data models
- `GroundStation` — geodetic lat/lon/alt, min elevation, antenna properties
- `Position3D` / `Velocity3D` — (x,y,z) with `coordinate_system` tag (ECI / ECEF). Documentation must state units (prefer km for ECI, meters for ECEF) to avoid heuristics.
- `ContactWindow` — satellite id, ground station name, start/end times, duration, max elevation, data rate, avg range
- `ContactQuality` — per-sample metrics used to evaluate window quality

## Accuracy and Acceptance Criteria

This epic maps directly to the acceptance criteria defined by the project. The implementation MUST satisfy the following:

### Functional Requirements (must pass tests)
- Elevation angle calculations accurate within 0.1 degrees (unit tests validate geometry).  
- Azimuth calculations properly handle all quadrants (0–360°).  
- Range calculations accurate within 1 km for LEO satellites (slant range).  
- Visibility checks respect `GroundStation.min_elevation_deg` (5° basic, 10° for high-quality stations).  
- Contact windows correctly identify start/end times (tests validate durations/frequency for LEO/MEO/GEO).  
- Contact quality metrics include elevation, azimuth, range_km, data_rate_mbps, signal_strength_db, doppler_shift_hz.

### Mathematical Accuracy
- Elevation: elevation = arcsin(up_topocentric / slant_range)  
- Azimuth: azimuth = arctan2(east, north)  
- Range: computed from ECEF vectors after proper coordinate transforms

### Performance Targets (guidance)
- Single visibility check: < 1 ms (prefer internal fast path without heavy astropy transforms).  
- 24-hour contact prediction: < 5 seconds per satellite-station pair (depends on timestep).  
- Real-time contact checking: 100 satellites < 100 ms (batch optimizations required).  
- Memory: < 10 MB for a 24-hour contact plan (depends on how many windows produced).

> Note: performance targets should be validated with microbenchmarks; optimizations (vectorized propagation, batch ECI→ECEF transforms or use of SGP4) may be required to meet strict numbers.

## Validation Requirements
- Compare predicted ISS passes with Skyfield/SGP4-derived pass times for at least one ground station.  
- Contact durations for LEO: typically 2–15 minutes; tests should assert pass durations fall into expected ranges.  
- Contact frequency for typical LEO: 4–8 passes/day per satellite (statistical validation).  
- MEO/GEO behavior: MEO passes longer, GEO stationary relative to longitude (low elevation near high latitudes).

## Testing Strategy
- Unit tests in `src/test_contact_prediction.py` must cover:
  - Elevation/azimuth math and quadrant handling
  - Range accuracy for sample geometries
  - Visibility logic at and around elevation thresholds
  - Contact window detection for LEO/MEO/GEO synthetic orbits
  - Contact quality output fields and reasonable ranges
- Integration tests:
  - Compare predictions with skyfield/SGP4 runs for ISS/TLE (optional, stored TLEs included in tests if desired)
- Coverage target: >85% for the module. Current tests exercise many behaviors; expand to cover scheduler and bulk-prediction functions when implemented.

## Risk Assessment

### High risk
- Unit ambiguity (km vs m) across Position3D / Velocity3D — mitigated by adding explicit unit contracts or conversion helpers.

### Medium risk
- Performance for large constellations — mitigated by batching/vectorization or native propagators (SGP4/skyfield).

### Low risk
- Link budget simplifications (data rate model is approximate) — mitigated by replacing with parametric link budget if required.

## Timeline

### Week 1
- Days 1–2: Implement core functions (to_ecef_position, elevation/azimuth, range, is_visible).  
- Days 2–4: Implement predict_contact_windows and calculate_contact_quality; write unit tests.  
- Days 4–5: Add scheduler helpers, CSV export, and integrate tests with `orbital_mechanics`.  
- Day 6: Benchmarks and performance tuning.  
- Day 7: Documentation and acceptance validation versus TLE data.

## Deliverables

### Code
- `src/contact_prediction.py` — fully implemented core functions and scheduler helpers (TODO: complete batch optimizations).  
- `src/test_contact_prediction.py` — unit and integration tests (current test suite included).  

### Documentation
- This epic document `docs/epics/iteration_1/P2-002-contact-prediction.md`  
- Inline docstrings and examples in module files

### Validation artifacts
- Small dataset / example TLEs (optional) and benchmark scripts to validate performance

## Acceptance Criteria (summary checklist)
- [x] Elevation formula implemented as arcsin(up/range)  
- [x] Azimuth formula implemented as arctan2(east, north)  
- [x] Range calculation uses ECEF transforms  
- [x] Visibility respects station min elevation  
- [x] Contact windows detect start/end times  
- [x] Contact quality includes required metrics  
- [ ] Bulk functions & scheduler implemented and tested (predict_all_contacts, get_current_contacts, scheduler) — TODO
- [ ] Performance microbenchmarks added and targets validated — TODO
- [ ] TLE/Skyfield validation test added — TODO

## Resources

### References
- Vallado, "Fundamentals of Astrodynamics"  
- Curtis, "Orbital Mechanics for Engineering Students"  
- Skyfield and sgp4 documentation  

### Tools
- Python, NumPy, astropy, Skyfield (optional), pytest, coverage
