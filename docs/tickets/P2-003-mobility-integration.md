# P2-003: Implement Satellite Mobility Model Integration

**Epic:** Satellite Mobility & Data Collection  
**Priority:** High  
**Story Points:** 10  
**Assignee:** Pair 2  
**Labels:** `satellite`, `mobility`, `csv-export`, `data-collection`, `integration`

## Overview

Integrate satellite orbital motion with the DTN mobility framework, providing position updates, contact management, and CSV data export/import for satellite networks. This connects the orbital mechanics with the broader DTN simulation system.

## User Story

As a DTN simulation system, I need satellite mobility data integrated with the standard mobility interface so that the GUI can display real-time satellite positions, routing algorithms can access current node locations, and experiment data can be collected and exported for analysis.

## Technical Requirements

### Core Functions to Implement

#### 1. Mobility State Management (`get_mobility_state`)
```python
def get_mobility_state(self, node_id: str, timestamp: float) -> Optional[MobilityState]:
    # For satellites: propagate orbit and convert to lat/lon/alt
    # For ground stations: return fixed position with zero velocity
    # Calculate velocity magnitude and heading from orbital velocity
    # Return MobilityState with all required fields
```

#### 2. Position Lookup (`get_node_position`)
```python
def get_node_position(self, node_id: str, timestamp: float) -> Optional[Position3D]:
    # For satellites: propagate orbit to timestamp
    # For ground stations: return fixed ECEF position
    # Handle node not found cases gracefully
```

#### 3. Batch Position Updates (`update_positions`)
```python
def update_positions(self, timestamp: float) -> Dict[str, MobilityState]:
    # Efficiently update all satellite and ground station positions
    # Log mobility states for experiment data collection
    # Return dictionary mapping node_id to MobilityState
    # Optimize for real-time GUI updates (1-10 Hz)
```

#### 4. Contact Plan Generation (`generate_contact_plan`)
```python
def generate_contact_plan(self, start_time: float, duration_hours: float, 
                         time_step_seconds: float = 60) -> List[ContactPlanEntry]:
    # Steps:
    # 1. For each satellite-ground station pair
    # 2. Predict contact windows using contact_predictor
    # 3. Convert ContactWindows to ContactPlanEntry objects
    # 4. Merge and sort all contact entries by time
    # 5. Add inter-satellite links if configured
```

#### 5. CSV Contact Plan Management
```python
def load_contact_plan_csv(self, csv_file: Path) -> List[ContactPlanEntry]:
    # Parse CSV: start_time,end_time,source_node,dest_node,data_rate_kbps,range_km,delay_ms
    # Handle Unix timestamps and ISO 8601 formats
    # Validate data and handle parsing errors
    
def save_contact_plan_csv(self, csv_file: Path, contact_plan: List[ContactPlanEntry]) -> None:
    # Export contact plan with proper headers
    # Include both Unix timestamps and human-readable times
    # Format for external network analysis tools
```

### Data Structures

#### MobilityState
```python
@dataclass
class MobilityState:
    node_id: str
    timestamp: float
    latitude_deg: float
    longitude_deg: float
    altitude_km: float
    velocity_kmh: float
    heading_deg: float      # 0-360, 0=North
    is_satellite: bool = True
```

#### ContactPlanEntry
```python
@dataclass
class ContactPlanEntry:
    start_time: float
    end_time: float
    source_node: str
    dest_node: str
    data_rate_kbps: float
    range_km: float
    delay_ms: float         # Propagation delay
```

### CSV Format Specification
```csv
start_time,end_time,source_node,dest_node,data_rate_kbps,range_km,delay_ms
1695824400.0,1695824700.0,SAT_001,GS_SVALBARD,50000,1500,5.0
1695824800.0,1695825100.0,SAT_002,GS_ALASKA,75000,1200,4.0
```

## Acceptance Criteria

### Functional Requirements
- [ ] Mobility states calculated correctly for satellites and ground stations
- [ ] Position updates work for individual nodes and batch operations
- [ ] Contact plan generation produces complete schedules
- [ ] CSV import handles multiple timestamp formats (Unix, ISO 8601)
- [ ] CSV export includes all required columns with proper formatting
- [ ] Real-time position updates support GUI animation requirements

### Integration Requirements
- [ ] DTN routing algorithms can access current node positions
- [ ] GUI receives position updates at 1-10 Hz without performance issues
- [ ] Experiment framework can collect mobility logs
- [ ] Contact plans compatible with external network analysis tools

### Performance Requirements
- [ ] Single mobility state calculation: < 1ms
- [ ] Batch position update (100 nodes): < 10ms
- [ ] Contact plan generation (24 hours): < 30 seconds
- [ ] CSV import/export: < 5 seconds for 10,000 entries
- [ ] Memory usage: < 50MB for full mobility logs

### Data Quality Requirements
- [ ] Satellite velocity calculations accurate within 1%
- [ ] Heading calculations correct for orbital motion
- [ ] Ground station positions remain fixed (zero velocity)
- [ ] Contact plan entries chronologically ordered
- [ ] No duplicate or overlapping contact windows

## Implementation Notes

### Velocity and Heading Calculations
```python
# For satellites in orbital motion:
# velocity_kmh = orbital_velocity_km_s * 3600
# heading_deg = arctan2(velocity_east, velocity_north) * 180/π
# heading_deg = (heading_deg + 360) % 360  # Normalize to 0-360°
```

### Contact Plan Entry Conversion
```python
@classmethod
def from_contact_window(cls, contact: ContactWindow, satellite_id: str) -> ContactPlanEntry:
    # Calculate delay_ms from range: delay = (range_km / 299792.458)
    # Convert data rates and format appropriately
    # Handle satellite-to-ground vs ground-to-satellite directionality
```

### Real-time Update Optimization
- **Lazy Evaluation:** Only calculate positions when requested
- **Caching:** Store recent calculations with timestamp validation
- **Batch Processing:** Update multiple satellites simultaneously
- **Differential Updates:** Only recalculate changed positions

## Test Cases

### Unit Tests
- [ ] Test mobility state calculation for LEO satellite
- [ ] Test position lookup for ground station
- [ ] Test batch position updates with mixed node types
- [ ] Test contact plan generation with single satellite
- [ ] Test CSV import with various timestamp formats
- [ ] Test CSV export format compliance

### Integration Tests
- [ ] Test with orbital mechanics module for position accuracy
- [ ] Test with contact prediction for complete contact plans
- [ ] Test real-time updates with simulated GUI polling
- [ ] Test experiment data collection over extended periods

### Performance Tests
- [ ] Benchmark batch position updates with large constellations
- [ ] Test CSV processing with large datasets
- [ ] Measure memory usage during long-running simulations
- [ ] Validate real-time update rates under load

### Validation Tests
- [ ] Compare satellite velocities with orbital mechanics theory
- [ ] Verify contact plan chronological ordering
- [ ] Cross-check CSV import/export round-trip accuracy
- [ ] Validate heading calculations for different orbital inclinations

## Definition of Done

- [ ] All core mobility functions implemented and tested
- [ ] CSV contact plan import/export working with validation
- [ ] Real-time position updates optimized for GUI requirements
- [ ] Integration with orbital mechanics and contact prediction verified
- [ ] Experiment data collection framework operational
- [ ] Performance benchmarks meet requirements
- [ ] Comprehensive test suite with >80% coverage
- [ ] Documentation includes API reference and usage examples
- [ ] Code reviewed and approved by team

## Dependencies

**Depends on:** P2-001 (Orbital Mechanics), P2-002 (Contact Prediction)  
**Blocks:** P2-005 (Experiment Data Collection)

## Integration Points

### With GUI (Pair 3)
```python
# Real-time position updates for 3D visualization
positions = mobility_model.update_positions(current_time)
gui.update_satellite_positions(positions)

# Contact timeline for GUI display
contacts = contact_manager.get_active_contacts(current_time)
gui.update_contact_links(contacts)
```

### With DTN Routing (Pair 1)
```python
# Current node positions for routing algorithms
position = mobility_model.get_node_position("SAT_001", current_time)
next_hop = routing_algorithm.find_next_hop(bundle, position)

# Contact predictions for store-and-forward
contact_plan = contact_manager.get_next_contacts("SAT_001", current_time)
routing_algorithm.schedule_transmission(bundle, contact_plan)
```

### With Experiment Framework
```python
# Mobility data collection
mobility_log = mobility_model.get_mobility_log(start_time, end_time)
experiment_data = data_collector.export_experiment_data(output_dir)
```

## Resources

- **DTN Mobility Models:** RFC 4838 - DTN Architecture
- **CSV Standards:** RFC 4180 - Common Format and MIME Type for CSV
- **Timestamp Formats:** ISO 8601 for human-readable times
- **Network Analysis Tools:** Compatible with OMNET++, NS-3 contact plans

## Time Estimate

**Total:** 3-4 days
- Day 1: Mobility state calculation and position management
- Day 2: Contact plan generation and CSV handling
- Day 3: Real-time updates optimization and batch processing
- Day 4: Integration testing and performance optimization