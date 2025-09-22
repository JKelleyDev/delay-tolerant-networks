# P2-004: Implement Constellation Configuration Management

**Epic:** Satellite Mobility & Data Collection  
**Priority:** Medium  
**Story Points:** 8  
**Assignee:** Pair 2  
**Labels:** `satellite`, `constellation`, `configuration`, `presets`, `json-config`

## Overview

Implement constellation configuration management system with preset configurations (LEO, MEO, GEO, HEO), custom constellation generation, and JSON import/export capabilities. This provides the foundation for users to select and configure satellite constellations for DTN simulation.

## User Story

As a DTN simulation user, I need to be able to select from preset satellite constellations (like Iridium or Starlink) or create custom constellations so that I can test DTN algorithms under different satellite network topologies and coverage scenarios.

## Technical Requirements

### Core Functions to Implement

#### 1. Preset Configuration Loading (`_load_preset_configurations`)
```python
def _load_preset_configurations(self) -> None:
    # Define parameters for all preset constellations:
    # - LEO: Iridium (66 sats), Starlink (1584 sats)
    # - MEO: GPS (24 sats)  
    # - GEO: Minimal (3 sats)
    # - HEO: Molniya (12 sats)
    # Use values from satellite_communication_architecture.md
```

#### 2. Walker Constellation Generation (`generate_walker_constellation`)
```python
def generate_walker_constellation(self, params: ConstellationParameters) -> List[OrbitalElements]:
    # Steps:
    # 1. Calculate satellites per plane = total_satellites / orbital_planes
    # 2. Calculate RAAN spacing = 360° / orbital_planes
    # 3. Calculate satellite spacing in plane = 360° / satellites_per_plane
    # 4. Generate OrbitalElements for each satellite with proper phasing
    # 5. Validate orbital parameters for collision avoidance
```

#### 3. Specialized Constellation Generators
```python
def generate_geostationary_constellation(self, num_satellites: int, 
                                       longitude_spacing_deg: float) -> List[OrbitalElements]:
    # GEO satellites at 35,786 km altitude, 0° inclination
    # Distribute evenly in longitude or use custom spacing

def generate_molniya_constellation(self, num_satellites: int = 12) -> List[OrbitalElements]:
    # HEO constellation: 63.4° inclination, 12-hour period, high eccentricity
    # Distribute across multiple orbital planes for continuous coverage
```

#### 4. Constellation Building (`build_preset_constellation`)
```python
def build_preset_constellation(self, preset_name: str) -> ConstellationConfig:
    # Use preset parameters to generate complete constellation
    # Include satellites, ground stations, communication config, metadata
    # Support: "leo_iridium", "leo_starlink", "meo_gps", "geo_minimal", "heo_molniya"
```

#### 5. Configuration Management
```python
def save_constellation(self, config: ConstellationConfig, file_path: Path) -> None:
    # Export complete configuration to JSON with proper formatting
    
def load_constellation(self, config_source: Union[str, Path, ConstellationConfig]) -> ConstellationConfig:
    # Handle preset names, JSON files, and direct ConstellationConfig objects
    
def validate_constellation(self, config: ConstellationConfig) -> Tuple[bool, List[str]]:
    # Check orbital parameters, ground station locations, communication config
    # Validate satellite spacing and collision avoidance
```

### Data Structures

#### ConstellationParameters
```python
@dataclass
class ConstellationParameters:
    total_satellites: int
    orbital_planes: int
    altitude_km: float
    inclination_deg: float
    eccentricity: float = 0.0
    arg_perigee_deg: float = 0.0
    raan_spacing_deg: Optional[float] = None
    satellite_spacing_deg: Optional[float] = None
```

#### ConstellationConfig
```python
@dataclass
class ConstellationConfig:
    name: str
    constellation_type: ConstellationType
    description: str
    satellites: List[OrbitalElements]
    ground_stations: List[GroundStation]
    communication_config: Dict[str, Any]
    metadata: Dict[str, Any]
```

### Preset Configurations

#### LEO Constellations
```python
LEO_IRIDIUM = ConstellationParameters(
    total_satellites=66, orbital_planes=6, altitude_km=780, 
    inclination_deg=86.4, eccentricity=0.0
)

LEO_STARLINK = ConstellationParameters(
    total_satellites=1584, orbital_planes=72, altitude_km=550,
    inclination_deg=53.0, eccentricity=0.0
)
```

#### MEO/GEO/HEO Configurations
```python
MEO_GPS = ConstellationParameters(
    total_satellites=24, orbital_planes=6, altitude_km=20200,
    inclination_deg=55.0, eccentricity=0.0
)

GEO_MINIMAL = ConstellationParameters(
    total_satellites=3, orbital_planes=1, altitude_km=35786,
    inclination_deg=0.0, eccentricity=0.0
)

HEO_MOLNIYA = ConstellationParameters(
    total_satellites=12, orbital_planes=3, altitude_km=26554,  # Semi-major axis
    inclination_deg=63.4, eccentricity=0.722
)
```

## Acceptance Criteria

### Functional Requirements
- [ ] All preset constellations generate correct number of satellites
- [ ] Walker constellation distribution maintains proper phasing
- [ ] GEO satellites positioned at correct longitudes
- [ ] HEO (Molniya) satellites have proper orbital parameters
- [ ] Custom constellation builder accepts user-defined parameters
- [ ] JSON configuration import/export preserves all data

### Mathematical Requirements
- [ ] RAAN spacing: 360° / number_of_planes
- [ ] Satellite spacing: 360° / satellites_per_plane
- [ ] GEO altitude: 35,786 km (±10 km tolerance)
- [ ] Molniya inclination: 63.4° (critical inclination)
- [ ] Orbital parameters within valid ranges (e.g., 0 ≤ eccentricity < 1)

### Validation Requirements
- [ ] Iridium constellation: 66 satellites in 6 planes (11 per plane)
- [ ] Starlink constellation: 1584 satellites in 72 planes (22 per plane)
- [ ] GPS constellation: 24 satellites in 6 planes (4 per plane)
- [ ] GEO minimal: 3 satellites spaced 120° apart
- [ ] No satellite collisions in generated constellations

### Configuration Requirements
- [ ] JSON export includes all constellation metadata
- [ ] JSON import preserves orbital precision
- [ ] Configuration validation catches invalid parameters
- [ ] Support for constellation modifications (add/remove satellites)

## Implementation Notes

### Walker Constellation Algorithm
```python
def generate_walker_constellation(self, params: ConstellationParameters):
    satellites = []
    sats_per_plane = params.total_satellites // params.orbital_planes
    
    for plane in range(params.orbital_planes):
        raan = plane * (360.0 / params.orbital_planes)
        
        for sat in range(sats_per_plane):
            true_anomaly = sat * (360.0 / sats_per_plane)
            
            orbital_elements = OrbitalElements(
                semi_major_axis=params.altitude_km + EARTH_RADIUS,
                eccentricity=params.eccentricity,
                inclination=params.inclination_deg,
                raan=raan,
                arg_perigee=params.arg_perigee_deg,
                true_anomaly=true_anomaly,
                epoch=time.time()
            )
            satellites.append(orbital_elements)
    
    return satellites
```

### JSON Configuration Format
```json
{
  "name": "Custom LEO Constellation",
  "constellation_type": "leo",
  "description": "Custom 100-satellite LEO constellation",
  "satellites": [
    {
      "semi_major_axis": 6928.0,
      "eccentricity": 0.0,
      "inclination": 51.6,
      "raan": 0.0,
      "arg_perigee": 0.0,
      "true_anomaly": 0.0,
      "epoch": 1695824400.0
    }
  ],
  "ground_stations": [...],
  "communication_config": {
    "frequency_ghz": 12.0,
    "bandwidth_mhz": 500,
    "tx_power_watts": 20
  },
  "metadata": {
    "created_by": "DTN Simulator",
    "creation_date": "2024-01-01T00:00:00Z",
    "version": "1.0"
  }
}
```

## Test Cases

### Unit Tests
- [ ] Test Walker constellation generation with various parameters
- [ ] Test GEO constellation positioning
- [ ] Test Molniya constellation orbital elements
- [ ] Test JSON serialization/deserialization
- [ ] Test constellation validation with invalid parameters
- [ ] Test preset constellation loading

### Integration Tests
- [ ] Test complete preset constellation building
- [ ] Test custom constellation with orbital mechanics module
- [ ] Test configuration save/load round-trip accuracy
- [ ] Test constellation modification (add/remove satellites)

### Validation Tests
- [ ] Compare generated constellations with published designs
- [ ] Verify orbital periods match theoretical values
- [ ] Check satellite spacing uniformity
- [ ] Validate ground station coverage patterns

## Definition of Done

- [ ] All preset constellations implemented and validated
- [ ] Walker constellation generation algorithm working
- [ ] Specialized constellation generators (GEO, HEO) complete
- [ ] JSON configuration import/export functional
- [ ] Constellation validation comprehensive
- [ ] Custom constellation builder operational
- [ ] Integration with GUI preset selection
- [ ] Performance meets requirements (< 1 second for 1000 satellites)
- [ ] Test suite coverage >85%
- [ ] Documentation includes configuration examples

## Dependencies

**Depends on:** P2-001 (Orbital Mechanics Core)  
**Blocks:** P2-005 (Experiment Data Collection)  
**Integrates with:** P2-002 (Contact Prediction), P2-003 (Mobility Integration)

## Integration Points

### With GUI (Pair 3)
```python
# Constellation preset selection dropdown
available_presets = constellation_manager.get_available_presets()
gui.populate_constellation_dropdown(available_presets)

# Real-time constellation modification
constellation_manager.add_satellite(new_orbital_elements, "CUSTOM_SAT_001")
gui.update_satellite_display()
```

### With Experiment Framework
```python
# Constellation configuration for experiments
config = constellation_manager.load_constellation("leo_starlink")
experiment.set_constellation(config)
data_collector.log_constellation_metadata(config.metadata)
```

## Resources

- **Walker Constellation Theory:** J.G. Walker's constellation design papers
- **Satellite Constellation Designs:** Published constellation parameters
- **JSON Schema:** For configuration file validation
- **Orbital Mechanics Validation:** STK, GMAT for cross-verification

## Time Estimate

**Total:** 3-4 days
- Day 1: Preset configuration loading and Walker constellation generation
- Day 2: Specialized constellation generators (GEO, HEO)
- Day 3: JSON configuration management and validation
- Day 4: Integration testing and performance optimization