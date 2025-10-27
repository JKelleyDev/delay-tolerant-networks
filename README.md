# DTN Simulator - Comprehensive User Manual & Documentation

**A comprehensive Delay-Tolerant Network (DTN) simulator for satellite communications with realistic orbital mechanics, advanced routing algorithms, and real-time 3D visualization.**

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![React](https://img.shields.io/badge/react-v18.2+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📚 Table of Contents

1. [Project Overview](#-project-overview)
2. [Quick Start](#-quick-start)
3. [Complete User Manual](#-complete-user-manual)
4. [Mathematical Formulas & Algorithms](#-mathematical-formulas--algorithms)
5. [Data Interpretation Guide](#-data-interpretation-guide)
6. [3D Visualization Features](#-3d-visualization-features)
7. [DTN Routing Protocols](#-dtn-routing-protocols)
8. [Performance Metrics](#-performance-metrics)
9. [Orbital Mechanics](#-orbital-mechanics)
10. [API Reference](#-api-reference)
11. [Troubleshooting](#-troubleshooting)

## 🎯 Project Overview

This DTN simulator provides a comprehensive environment for studying delay-tolerant networking in satellite constellations. It combines realistic orbital mechanics with advanced routing algorithms to simulate how data flows through intermittently connected space networks.

### Key Features

- **🛰️ Realistic Orbital Mechanics**: SGP4/SDP4 propagation with accurate satellite positioning
- **🌐 Multiple Constellation Support**: LEO, MEO, GEO constellations with custom upload capability
- **🔀 Advanced DTN Routing**: Epidemic, PRoPHET, Spray-and-Wait algorithms with performance comparison
- **📡 Ground Station Network**: Global coverage with configurable elevation masks
- **🎮 Military-Style 3D Visualization**: Real-time satellite tracking with dynamic footprints
- **📊 Comprehensive Analytics**: Performance metrics, delivery ratios, and network analysis
- **⚡ Real-time Simulation**: Live updates with time acceleration up to 3600x

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Git** for version control

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YourUsername/delay-tolerant-networks.git
   cd delay-tolerant-networks
   ```

2. **Start the development environment**
   ```bash
   # Start both backend and frontend servers
   ./scripts/start-dev.sh
   ```

3. **Access the application**
   - **Frontend**: http://localhost:3000
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

## 📖 Complete User Manual

### Navigation Overview

The DTN Simulator has three main sections:

1. **Constellations**: Manage satellite constellations and upload custom configurations
2. **Experiments**: Design and run comparative studies across different scenarios
3. **Simulations**: Run real-time simulations with live 3D visualization

### Section 1: Constellation Management

#### Viewing Built-in Constellations

1. **Navigate to Constellations tab**
2. **View constellation library** with pre-configured satellite networks:
   - **Starlink**: 1,584 satellites in LEO (550 km altitude, 53° inclination)
   - **Project Kuiper**: 3,236 satellites in multiple LEO shells
   - **GPS**: 31 satellites in MEO (20,200 km altitude)
   - **GEO Minimal**: 3 satellites in geostationary orbit
   - **Molniya**: 12 satellites in highly elliptical orbit

#### Uploading Custom Constellations

1. **Prepare CSV file** with the following format:
   ```csv
   satellite_id,name,altitude,inclination,raan,eccentricity,arg_perigee,mean_anomaly
   sat_001,MySat1,550,53.0,0,0,0,0
   sat_002,MySat2,550,53.0,0,0,0,60
   ```

2. **Upload process**:
   - Click "Upload Custom Constellation"
   - Enter constellation name and description
   - Select your CSV file
   - Review satellite count and orbital parameters
   - Click "Create Constellation"

3. **Validation**: The system automatically validates:
   - Orbital parameter ranges (altitude: 200-50,000 km)
   - Satellite naming conventions
   - File format compliance

#### Understanding Orbital Elements

- **Altitude**: Height above Earth's surface (km)
- **Inclination**: Orbital plane angle relative to equator (degrees)
- **RAAN**: Right Ascension of Ascending Node - orbital plane orientation (degrees)
- **Eccentricity**: Orbit shape (0 = circular, >0 = elliptical)
- **Argument of Perigee**: Orientation of ellipse within orbital plane (degrees)
- **Mean Anomaly**: Satellite position along orbit (degrees)

### Section 2: Experiment Design

#### Creating Comparative Experiments

1. **Navigate to Experiments tab**
2. **Click "New Experiment"**
3. **Configure experiment parameters**:
   - **Name**: Descriptive experiment title
   - **Constellation**: Select from available constellations
   - **Routing Algorithms**: Choose one or more to compare:
     - Epidemic Routing
     - PRoPHET Routing
     - Spray and Wait
   - **Duration**: Simulation time (1-168 hours)
   - **Ground Stations**: Select source and destination pairs

4. **Advanced Configuration**:
   - **Traffic Pattern**: Uniform, bursty, or custom
   - **Bundle Size**: Data packet size (KB)
   - **Bundle TTL**: Time-to-live for data packets
   - **Buffer Size**: Satellite storage capacity

5. **Run Experiment**: Click "Start Experiment" to begin automated testing

#### Experiment Results Analysis

**Delivery Performance**:
- **Delivery Ratio**: Percentage of bundles successfully delivered
- **End-to-End Delay**: Average time from source to destination
- **Hop Count Distribution**: Number of satellite hops per delivery

**Network Efficiency**:
- **Overhead Ratio**: Total transmissions / successful deliveries
- **Buffer Utilization**: Storage usage across network
- **Energy Consumption**: Transmission energy per bit delivered

**Statistical Analysis**:
- **Confidence Intervals**: Statistical significance of results
- **Performance Comparison**: Side-by-side algorithm comparison
- **Trend Analysis**: Performance over time

### Section 3: Real-time Simulations

#### Creating a New Simulation

1. **Navigate to Simulations tab**
2. **Configure simulation**:
   - **Name**: Simulation identifier
   - **Constellation**: Choose satellite network
   - **Routing Algorithm**: Select DTN protocol
   - **Duration**: Simulation length (1-168 hours)
   - **Ground Stations**: Select exactly 2 stations for source/destination

3. **Weather Simulation** (Optional):
   - **Enable Weather Effects**: Realistic RF attenuation
   - **Weather Seed**: For reproducible weather patterns
   - **Effects Include**:
     - Rain fade attenuation (frequency dependent)
     - Atmospheric absorption (humidity, temperature)
     - Regional weather patterns (9 global regions)
     - Real-time weather evolution

4. **Click "Create Simulation"** to initialize

#### Running Simulations

1. **Start Simulation**: Click play button (▶️) to begin
2. **Monitor Progress**: Watch real-time metrics update
3. **Control Playback**:
   - **Pause** (⏸️): Temporarily halt simulation
   - **Stop** (⏹️): End simulation and save results

#### 3D Visualization Interface

**Command Center HUD** (Upper portion):
- **System Status**: Network operational state
- **Simulation Time**: Accelerated time display (3600x speed)
- **Active Satellites**: Number of operational satellites
- **Bundle Tracking**: Active, delivered, and expired data packets

**Left Panel - Network Status**:
- **Satellites**: Total count in constellation
- **Active Links**: Current inter-satellite connections
- **Bundles Active**: Data packets currently in network
- **Delivered**: Successfully transmitted packets
- **Expired**: Packets that exceeded time-to-live
- **Throughput**: Network data rate (Mbps)

**Left Panel - RF Subsystem**:
- **Band**: Communication frequency (Ka-band)
- **SNR Avg**: Signal-to-noise ratio (dB)
- **Link Quality**: Connection reliability (%)
- **Weather**: Environmental effects status

**Left Panel - DTN Routing**:
- **Algorithm**: Current routing protocol
- **Delivery Ratio**: Success rate (%)
- **Avg Delay**: End-to-end latency (seconds)
- **Overhead**: Efficiency metric (transmissions per delivery)

**3D Visualization Elements**:
- **Earth**: Realistic satellite imagery with day/night cycle
- **Satellites**: Octahedral shapes with status colors
- **Communication Footprints**: Green circles on Earth showing coverage during transmission
- **Transmission Beams**: Lines from satellites to Earth during active communication
- **Ground Stations**: Antenna models at geographic locations
- **Bundle Indicators**: Orange spheres above satellites storing data

#### Interactive Controls

- **Mouse Orbit**: Drag to rotate camera around Earth
- **Scroll Zoom**: Zoom in/out for different perspectives
- **Satellite Selection**: Click satellites for detailed information
- **Camera Reset**: Double-click to return to default view

## 🧮 Mathematical Formulas & Algorithms

### Orbital Mechanics Calculations

#### SGP4/SDP4 Satellite Propagation

**Mean Motion** (revolutions per day):
```
n = √(μ / a³)
```
Where:
- μ = Earth's gravitational parameter (398,600.4418 km³/s²)
- a = semi-major axis (km)

**Orbital Period**:
```
T = 2π√(a³ / μ)
```

**Satellite Position** (Earth-Centered Inertial coordinates):
```
r = [x, y, z] = orbital_propagation(TLE, time)
```

#### Contact Window Prediction

**Line-of-Sight Calculation**:
```
elevation = arcsin((r_sat · r_gs) / (|r_sat| × |r_gs|))
```

**Communication Range**:
```
d_max = √(h² + 2R_earth × h)
```
Where:
- h = satellite altitude
- R_earth = Earth radius (6371 km)

**Contact Duration**:
```
contact_time = 2 × arccos(R_earth / (R_earth + h)) / orbital_velocity
```

### DTN Routing Mathematics

#### Epidemic Routing

**Delivery Probability**:
```
P_delivery = 1 - (1 - p)^n
```
Where:
- p = contact probability
- n = number of replicas

**Optimal Replica Count**:
```
L = √(N × λ × T)
```
Where:
- N = network size
- λ = contact rate
- T = bundle TTL

#### PRoPHET Routing

**Delivery Predictability Update**:
```
P(a,b) = P(a,b)_old + (1 - P(a,b)_old) × P_init
```

**Aging Equation**:
```
P(a,b) = P(a,b) × γ^k
```
Where:
- γ = aging constant (0.98)
- k = time units elapsed

**Transitive Update**:
```
P(a,c) = P(a,c) + (1 - P(a,c)) × P(a,b) × P(b,c) × β
```

#### Spray and Wait

**Optimal Spray Count**:
```
L = min(N, √(N × λ × T))
```

**Wait Phase Delivery**:
```
P_wait = P_direct × (1 - e^(-λ×t))
```

### Network Performance Metrics

#### Delivery Ratio
```
Delivery_Ratio = Bundles_Delivered / Bundles_Generated
```

#### Average Delay
```
Avg_Delay = Σ(delivery_time - creation_time) / delivered_bundles
```

#### Overhead Ratio
```
Overhead = Total_Transmissions / Successful_Deliveries
```

#### Buffer Utilization
```
Buffer_Util = Average_Buffer_Occupancy / Total_Buffer_Capacity
```

### RF Link Budget Calculations

#### Free Space Path Loss
```
FSPL(dB) = 20 × log₁₀(d) + 20 × log₁₀(f) + 92.45
```
Where:
- d = distance (km)
- f = frequency (GHz)

#### Rain Attenuation
```
A_rain = γ × R^α × L
```
Where:
- γ, α = frequency-dependent coefficients
- R = rain rate (mm/hr)
- L = path length through rain (km)

## 📊 Data Interpretation Guide

### Understanding Simulation Results

#### Delivery Performance Indicators

**High Delivery Ratio (>90%)**:
- ✅ Excellent network connectivity
- ✅ Sufficient satellite density
- ✅ Appropriate routing algorithm choice

**Moderate Delivery Ratio (70-90%)**:
- ⚠️ Acceptable performance with room for improvement
- ⚠️ May indicate sparse connectivity regions
- ⚠️ Consider constellation optimization

**Low Delivery Ratio (<70%)**:
- ❌ Poor network performance
- ❌ Insufficient satellite coverage
- ❌ Routing algorithm mismatch for scenario

#### Delay Analysis

**Low Delay (<5 minutes)**:
- Direct or single-hop delivery
- High connectivity constellation
- Optimal ground station placement

**Moderate Delay (5-60 minutes)**:
- Multi-hop routing through satellites
- Store-and-forward delay accumulation
- Expected for DTN scenarios

**High Delay (>1 hour)**:
- Long contact gaps
- Sparse network connectivity
- May indicate need for constellation densification

#### Overhead Interpretation

**Low Overhead (1.0-2.0)**:
- Efficient routing with minimal redundancy
- Good for resource-constrained scenarios
- May sacrifice delivery ratio for efficiency

**Moderate Overhead (2.0-5.0)**:
- Balanced performance approach
- Acceptable redundancy for reliability
- Typical for well-tuned DTN networks

**High Overhead (>5.0)**:
- Excessive message replication
- Resource wasteful but high reliability
- May overwhelm network capacity

### 3D Visualization Data Meaning

#### Satellite Colors and Indicators

**Satellite Status Colors**:
- **Green**: Active satellite with good connectivity
- **Yellow**: Satellite with limited contacts
- **Red**: Satellite with poor connectivity or failures
- **Orange Sphere Above**: Satellite storing data bundles

**Communication Footprints**:
- **Green Circles**: Active data transmission coverage area
- **Blue Circles**: Regular communication coverage
- **Pulsing Animation**: Real-time data transfer
- **Size**: Proportional to satellite altitude

**Transmission Beams**:
- **Green Lines**: Bundle delivery in progress
- **Blue Lines**: Regular communication links
- **Cone Pattern**: Beam spread from satellite to Earth
- **Opacity**: Signal strength indication

#### Ground Station Activity

**Antenna Colors**:
- **Green**: Primary communication stations (source/destination)
- **Orange**: Secondary or relay stations
- **Beam Patterns**: Active when communicating with satellites

### Weather Effects Interpretation

When weather simulation is enabled:

**Clear Conditions**:
- Full signal strength
- Optimal communication windows
- Baseline performance metrics

**Rain/Storm Conditions**:
- Signal attenuation (5-20 dB additional loss)
- Reduced communication quality
- Shorter effective contact windows

**Regional Variations**:
- Tropical regions: Higher rain rates
- Polar regions: Temperature effects
- Temperate zones: Variable conditions

## 🎮 3D Visualization Features

### Military-Style Command Center Interface

The 3D visualization provides a realistic command center experience with:

#### Cinematic Design Elements

**Visual Aesthetics**:
- Dark space background with realistic starfield
- Military-style HUD overlays with glowing cyan/green accents
- Tactical corner brackets and scanning line effects
- Monospace fonts for authentic command center feel

**Earth Rendering**:
- High-resolution satellite imagery textures
- Realistic day/night cycle with city lights
- Procedural cloud formations and weather patterns
- Atmospheric glow effects

#### Interactive Features

**Camera Controls**:
- **Orbit**: Drag to rotate around Earth
- **Zoom**: Scroll wheel for distance control
- **Pan**: Shift+drag for lateral movement
- **Reset**: Double-click to return to default view

**Object Selection**:
- **Click Satellites**: View detailed telemetry
- **Hover Effects**: Highlight interactive elements
- **Information Panels**: Real-time data display

#### Real-time Animation

**Satellite Movement**:
- Accurate orbital mechanics
- Realistic velocity and acceleration
- Proper constellation formation

**Communication Visualization**:
- Dynamic footprint projection during transmission
- Pulsing animations for active data transfer
- Color-coded status indicators

### Understanding 3D Data Representation

#### Spatial Relationships

**Scale Accuracy**:
- Earth: 6,371 km radius (1:1 scale)
- Satellite altitudes: Realistic positioning
- Communication ranges: Geometrically accurate

**Coordinate System**:
- Earth-Centered Inertial (ECI) reference frame
- Real-time coordinate transformations
- Geographic latitude/longitude mapping

#### Temporal Dynamics

**Time Acceleration**:
- 3600x real-time speed (1 second = 1 hour simulation)
- Visible orbital progression
- Dynamic contact window formation

**Event Synchronization**:
- Bundle creation synchronized with ground station contacts
- Transmission beams appear during actual data transfer
- Footprints activate only during communication events

## 🔀 DTN Routing Protocols

### Detailed Protocol Analysis

#### 1. Epidemic Routing

**Algorithm Overview**:
Epidemic routing spreads messages like a virus, replicating to every encountered node until delivery or TTL expiration.

**Implementation Details**:
```python
def epidemic_routing(self, bundle, contact_list):
    for contact in contact_list:
        if contact.has_capacity():
            # Replicate to all available contacts
            contact.send_copy(bundle)
    return bundle_copies_sent
```

**Performance Characteristics**:
- **Best Case**: Dense, well-connected networks
- **Worst Case**: Resource-constrained environments
- **Optimal Usage**: High-priority, delay-sensitive traffic

**Mathematical Model**:
- Delivery probability approaches 1 with sufficient resources
- Message complexity: O(n²) where n = network size
- Buffer requirements: Exponential growth possible

#### 2. PRoPHET Routing

**Algorithm Overview**:
PRoPHET (Probabilistic Routing Protocol using History of Encounters and Transitivity) uses encounter history to predict future meeting probabilities.

**Implementation Details**:
```python
def prophet_routing(self, bundle, contact_list):
    best_contact = None
    best_probability = self.delivery_predictability[bundle.destination]
    
    for contact in contact_list:
        contact_prob = contact.delivery_predictability[bundle.destination]
        if contact_prob > best_probability:
            best_contact = contact
            best_probability = contact_prob
    
    if best_contact:
        best_contact.send_bundle(bundle)
```

**Predictability Updates**:
1. **Direct Contact**: P(a,b) += (1 - P(a,b)) × P_encounter
2. **Aging**: P(a,b) = P(a,b) × γ^time_units
3. **Transitivity**: P(a,c) += (1 - P(a,c)) × P(a,b) × P(b,c) × β

**Performance Characteristics**:
- **Best Case**: Predictable mobility patterns
- **Worst Case**: Random movement patterns
- **Optimal Usage**: Networks with repeating contact patterns

#### 3. Spray and Wait

**Algorithm Overview**:
Spray and Wait combines controlled replication (spray phase) with direct delivery (wait phase).

**Implementation Details**:
```python
def spray_and_wait(self, bundle, contact_list):
    if bundle.copy_count > 1:
        # Spray phase: distribute copies
        copies_to_distribute = bundle.copy_count // 2
        for contact in contact_list[:copies_to_distribute]:
            new_bundle = bundle.create_copy()
            new_bundle.copy_count = 1
            contact.send_bundle(new_bundle)
        bundle.copy_count -= copies_to_distribute
    else:
        # Wait phase: direct delivery only
        if bundle.destination in contact_list:
            bundle.destination.send_bundle(bundle)
```

**Performance Characteristics**:
- **Best Case**: Networks with predictable contacts
- **Worst Case**: Highly sparse networks
- **Optimal Usage**: Resource-limited scenarios requiring efficiency

### Protocol Comparison Matrix

| Metric | Epidemic | PRoPHET | Spray & Wait |
|--------|----------|---------|--------------|
| **Delivery Ratio** | Highest | High | Medium-High |
| **Delay** | Lowest | Medium | Medium |
| **Overhead** | Highest | Medium | Lowest |
| **Complexity** | Low | High | Medium |
| **Scalability** | Poor | Good | Excellent |
| **Memory Usage** | High | Medium | Low |

### Routing Algorithm Selection Guide

**Choose Epidemic When**:
- Maximum delivery ratio required
- Network has abundant resources
- Delay minimization is critical
- Network size is small to medium

**Choose PRoPHET When**:
- Mobility patterns are predictable
- Balance between performance and efficiency needed
- Historical data is available
- Network has moderate resources

**Choose Spray and Wait When**:
- Resources are severely constrained
- Network is sparse with long contact gaps
- Efficiency is more important than maximum delivery ratio
- Predictable routing paths exist

## 📈 Performance Metrics

### Core Metrics Definitions

#### 1. Delivery Ratio
**Formula**: `Delivered Bundles / Generated Bundles`
**Range**: 0.0 to 1.0 (0% to 100%)
**Interpretation**:
- **>0.95**: Excellent network performance
- **0.80-0.95**: Good performance, acceptable for most applications
- **0.60-0.80**: Moderate performance, may need optimization
- **<0.60**: Poor performance, requires intervention

#### 2. End-to-End Delay
**Formula**: `Σ(Delivery Time - Creation Time) / Delivered Bundles`
**Units**: Seconds, minutes, or hours
**Factors Affecting Delay**:
- Contact window frequency
- Routing algorithm efficiency
- Buffer management policies
- Network congestion levels

#### 3. Hop Count
**Formula**: `Average number of intermediate nodes per delivered bundle`
**Range**: 1 to network diameter
**Significance**:
- **1-2 hops**: Direct or nearly direct delivery
- **3-5 hops**: Typical multi-hop routing
- **>5 hops**: Complex routing, potential inefficiency

#### 4. Overhead Ratio
**Formula**: `Total Transmissions / Successful Deliveries`
**Range**: 1.0 to infinity
**Efficiency Levels**:
- **1.0-2.0**: Highly efficient
- **2.0-5.0**: Moderately efficient
- **>5.0**: Inefficient, excessive redundancy

### Advanced Performance Analysis

#### Statistical Significance
- **Confidence Intervals**: 95% confidence bounds on all metrics
- **Sample Size**: Minimum 100 bundles for statistical validity
- **Variance Analysis**: Understanding metric stability

#### Temporal Performance
- **Warm-up Period**: Initial network learning phase
- **Steady State**: Stable performance region
- **Performance Trends**: Degradation or improvement over time

#### Comparative Analysis
- **Algorithm Comparison**: Side-by-side performance
- **Constellation Comparison**: Different network topologies
- **Parameter Sensitivity**: Impact of configuration changes

### Performance Optimization Guidelines

#### Improving Delivery Ratio
1. **Increase Satellite Density**: More satellites = better coverage
2. **Optimize Ground Station Placement**: Strategic positioning for maximum coverage
3. **Tune TTL Values**: Balance between delivery opportunity and resource usage
4. **Buffer Management**: Prevent buffer overflow and message drops

#### Reducing Delay
1. **Choose Aggressive Routing**: Epidemic for minimum delay
2. **Increase Buffer Sizes**: Reduce blocking and queuing delays
3. **Optimize Contact Prediction**: Better timing for transmissions
4. **Prioritize Traffic**: High-priority bundles get preference

#### Reducing Overhead
1. **Choose Conservative Routing**: Spray and Wait for efficiency
2. **Implement Smart Replication**: Avoid unnecessary copies
3. **Use Acknowledgments**: Stop replication upon delivery
4. **Bundle Aggregation**: Combine small messages

## 🛰️ Orbital Mechanics

### Coordinate Systems

#### Earth-Centered Inertial (ECI)
**Primary coordinate system** for satellite tracking:
- **Origin**: Earth's center of mass
- **X-axis**: Points toward vernal equinox
- **Y-axis**: 90° east of X-axis in equatorial plane
- **Z-axis**: Points toward North Pole

#### Earth-Centered Earth-Fixed (ECEF)
**Rotating coordinate system**:
- **Origin**: Earth's center of mass
- **X-axis**: Points toward 0° longitude (Greenwich)
- **Y-axis**: Points toward 90° east longitude
- **Z-axis**: Points toward North Pole

#### Geographic Coordinates
**Human-readable location system**:
- **Latitude**: -90° (South Pole) to +90° (North Pole)
- **Longitude**: -180° (West) to +180° (East)
- **Altitude**: Height above mean sea level

### Orbital Elements and Their Effects

#### Semi-Major Axis (a)
**Controls orbital altitude and period**:
- **LEO**: 200-2,000 km altitude
- **MEO**: 2,000-35,786 km altitude
- **GEO**: 35,786 km altitude (geostationary)
- **HEO**: Highly elliptical (apogee >10,000 km)

**Period Calculation**:
```
T = 2π√(a³/μ)
```

#### Inclination (i)
**Orbital plane angle relative to equator**:
- **0°**: Equatorial orbit (stays above equator)
- **90°**: Polar orbit (passes over both poles)
- **Sun-synchronous**: ~98° for Earth observation
- **Retrograde**: >90° (moves opposite to Earth's rotation)

#### Eccentricity (e)
**Orbit shape parameter**:
- **0**: Perfectly circular
- **0-0.1**: Nearly circular (most satellites)
- **0.1-0.5**: Elliptical
- **>0.7**: Highly elliptical (Molniya orbits)

#### Right Ascension of Ascending Node (RAAN)
**Orbital plane orientation**:
- **0°**: Ascending node at vernal equinox
- **Changes**: Due to Earth's oblateness (J2 perturbation)
- **Sun-synchronous**: RAAN precesses to match Earth's orbit

#### Argument of Perigee (ω)
**Ellipse orientation within orbital plane**:
- **0°**: Perigee at ascending node
- **90°**: Perigee at northernmost point
- **180°**: Perigee at descending node
- **270°**: Perigee at southernmost point

#### Mean Anomaly (M)
**Satellite position along orbit**:
- **0°**: At perigee
- **90°**: Quarter orbit from perigee
- **180°**: At apogee
- **270°**: Three-quarters orbit

### Contact Prediction Mathematics

#### Line-of-Sight Geometry
**Elevation angle calculation**:
```
elevation = arcsin((r_sat - r_gs) · r_gs_up / |r_sat - r_gs|)
```

**Azimuth calculation**:
```
azimuth = atan2(east_component, north_component)
```

#### Maximum Communication Range
**Geometric horizon**:
```
d_max = √((R_earth + h_sat)² - R_earth²)
```

**With minimum elevation constraint**:
```
d_max = √((R_earth + h_sat)² - (R_earth / sin(elevation_min))²)
```

#### Contact Window Duration
**For circular orbits**:
```
contact_duration = 2 × arccos(cos(max_zenith_angle)) / angular_velocity
```

**Where**:
```
max_zenith_angle = arccos(R_earth / (R_earth + altitude))
angular_velocity = √(μ / (R_earth + altitude)³)
```

### Perturbation Effects

#### J2 Perturbation (Earth's Oblateness)
**RAAN precession rate**:
```
dΩ/dt = -3/2 × J2 × (R_earth/a)² × n × cos(i)
```

**Argument of perigee precession**:
```
dω/dt = 3/4 × J2 × (R_earth/a)² × n × (5cos²(i) - 1)
```

#### Atmospheric Drag (LEO only)
**Orbital decay rate**:
```
da/dt = -2πρv³(CD × A/m) / n
```

Where:
- ρ = atmospheric density
- v = orbital velocity
- CD = drag coefficient
- A = cross-sectional area
- m = satellite mass

### Constellation Design Principles

#### Coverage Optimization
**Walker Delta Pattern**:
- **T/P/F notation**: T satellites, P planes, F phase difference
- **Example**: 24/6/1 = 24 satellites, 6 planes, 1 unit phase shift

**Coverage Gaps**:
- **Latitude gaps**: Due to inclination limitations
- **Temporal gaps**: When satellites are below horizon
- **Mitigation**: Inter-satellite links, more satellites

#### Revisit Time Optimization
**Single satellite revisit**:
```
revisit_time = orbital_period / ground_track_repetition
```

**Constellation revisit**:
```
revisit_time = orbital_period / (satellites_per_plane × track_repetition)
```

## 🔌 API Reference

### Authentication
Currently, the API does not require authentication for development purposes. In production deployments, implement OAuth 2.0 or API key authentication.

### Base URL
```
http://localhost:8000/api/v2
```

### Response Format
All API responses follow this standard format:
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Constellation Management

#### GET /constellation/library
**Description**: Retrieve all built-in constellations
**Response**:
```json
{
  "success": true,
  "data": {
    "constellations": {
      "starlink": {
        "name": "Starlink Phase 1",
        "satellites": 1584,
        "altitude": 550,
        "inclination": 53.0,
        "description": "SpaceX Starlink constellation"
      }
    }
  }
}
```

#### POST /constellation/upload
**Description**: Upload custom constellation via CSV
**Request Body**:
```json
{
  "name": "My Custom Constellation",
  "description": "Research constellation for DTN study",
  "csv_data": "satellite_id,name,altitude,inclination...\nsat_001,MySat1,550,53.0..."
}
```

#### GET /constellation/{constellation_id}/satellites
**Description**: Get current satellite positions
**Parameters**:
- `constellation_id`: Constellation identifier
- `time`: Optional ISO timestamp (defaults to current time)

**Response**:
```json
{
  "success": true,
  "data": {
    "satellites": {
      "sat_001": {
        "position": {"x": 1234.5, "y": 2345.6, "z": 3456.7},
        "velocity": {"x": 7.5, "y": 0.2, "z": 1.1},
        "latitude": 45.123,
        "longitude": -122.456,
        "altitude": 550.2
      }
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Simulation Management

#### POST /simulation/create
**Description**: Create new simulation
**Request Body**:
```json
{
  "name": "LA to Tokyo Communication Test",
  "constellation_id": "starlink",
  "routing_algorithm": "prophet",
  "duration": 6.0,
  "ground_stations": ["gs_los_angeles", "gs_tokyo"],
  "time_step": 1.0,
  "weather_enabled": true,
  "weather_seed": 12345
}
```

#### GET /simulation/list
**Description**: List all simulations
**Response**:
```json
{
  "success": true,
  "data": {
    "simulations": [
      {
        "id": "sim_1234567890",
        "name": "LA to Tokyo Test",
        "status": "created",
        "constellation": "starlink",
        "routing_algorithm": "prophet",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

#### POST /simulation/{simulation_id}/start
**Description**: Start simulation execution
**Response**:
```json
{
  "success": true,
  "message": "Simulation started successfully",
  "data": {
    "simulation_id": "sim_1234567890",
    "estimated_completion": "2024-01-15T11:30:00Z"
  }
}
```

#### GET /simulation/{simulation_id}/status
**Description**: Get simulation status and progress
**Response**:
```json
{
  "success": true,
  "data": {
    "status": "running",
    "progress": 65.5,
    "current_sim_time": "2024-01-15T14:30:00Z",
    "runtime_seconds": 125.3,
    "bundles_generated": 450,
    "bundles_delivered": 387,
    "delivery_ratio": 0.86,
    "current_activity": "Processing satellite contacts..."
  }
}
```

#### GET /simulation/{simulation_id}/metrics
**Description**: Get detailed performance metrics
**Response**:
```json
{
  "success": true,
  "data": {
    "delivery_ratio": 0.863,
    "average_delay": 145.2,
    "average_hops": 2.4,
    "overhead_ratio": 3.1,
    "buffer_utilization": 0.45,
    "throughput": 125.6,
    "contact_statistics": {
      "total_contacts": 2456,
      "average_duration": 320.5,
      "data_transferred": 45.6
    }
  }
}
```

### Ground Station Management

#### GET /ground_stations/library
**Description**: Get all available ground stations
**Response**:
```json
{
  "success": true,
  "data": {
    "ground_stations": {
      "gs_los_angeles": {
        "name": "Los Angeles",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "elevation_mask": 10.0,
        "antenna_gain": 45.0
      }
    }
  }
}
```

### Experiment Management

#### POST /experiment/create
**Description**: Create comparative experiment
**Request Body**:
```json
{
  "name": "Routing Algorithm Comparison",
  "constellation_id": "starlink",
  "routing_algorithms": ["epidemic", "prophet", "spray_and_wait"],
  "duration": 24.0,
  "ground_stations": ["gs_los_angeles", "gs_tokyo"],
  "iterations": 5
}
```

#### GET /experiment/{experiment_id}/results
**Description**: Get experiment results and analysis
**Response**:
```json
{
  "success": true,
  "data": {
    "experiment_id": "exp_1234567890",
    "status": "completed",
    "results": {
      "epidemic": {
        "delivery_ratio": {"mean": 0.95, "std": 0.02, "ci_95": [0.93, 0.97]},
        "average_delay": {"mean": 145.2, "std": 15.3, "ci_95": [138.1, 152.3]}
      },
      "prophet": {
        "delivery_ratio": {"mean": 0.89, "std": 0.03, "ci_95": [0.86, 0.92]},
        "average_delay": {"mean": 178.5, "std": 22.1, "ci_95": [168.2, 188.8]}
      }
    }
  }
}
```

### Real-time Data

#### GET /simulation/{simulation_id}/real-time
**Description**: Get real-time simulation state (used by 3D visualization)
**Response**:
```json
{
  "success": true,
  "data": {
    "satellites": {
      "sat_001": {
        "position": {"x": 1234.5, "y": 2345.6, "z": 3456.7},
        "status": "active",
        "bundles_stored": 3,
        "active_contacts": 2
      }
    },
    "contacts": [
      {
        "source_id": "sat_001",
        "target_id": "sat_002",
        "is_active": true,
        "data_transfer": 156.7,
        "signal_strength": 85.2
      }
    ],
    "bundles_in_network": 45,
    "bundles_delivered": 123,
    "bundles_expired": 5,
    "current_sim_time": "2024-01-15T14:30:00Z",
    "time_acceleration": 3600
  }
}
```

### Error Handling

#### Standard Error Response
```json
{
  "success": false,
  "message": "Detailed error description",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "constellation_id",
    "issue": "Constellation not found"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### HTTP Status Codes
- **200**: Success
- **201**: Created successfully
- **400**: Bad request (validation error)
- **404**: Resource not found
- **422**: Unprocessable entity
- **500**: Internal server error

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Backend Connection Issues

**Problem**: "Failed to connect to localhost:8000"
**Causes**:
- Backend server not running
- Port 8000 already in use
- Firewall blocking connection

**Solutions**:
1. **Check if backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Kill processes on port 8000**:
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

3. **Start backend server**:
   ```bash
   cd backend && python src/main.py
   ```

#### Frontend Issues

**Problem**: "Cannot connect to backend" or API errors
**Solutions**:
1. **Check browser console** for specific error messages
2. **Verify API endpoints** in browser network tab
3. **Clear browser cache** and reload application
4. **Check CORS settings** in backend configuration

**Problem**: 3D visualization not loading
**Causes**:
- WebGL not supported
- GPU drivers outdated
- Three.js library loading issues

**Solutions**:
1. **Check WebGL support**: Visit https://get.webgl.org/
2. **Update browser** to latest version
3. **Update GPU drivers**
4. **Disable hardware acceleration** as fallback

#### Simulation Issues

**Problem**: Simulations not starting or hanging
**Causes**:
- Invalid constellation data
- Missing ground stations
- Insufficient system resources

**Solutions**:
1. **Validate constellation**: Check CSV format and orbital parameters
2. **Verify ground stations**: Ensure selected stations exist
3. **Check system resources**: Monitor CPU and memory usage
4. **Reduce simulation scope**: Shorter duration or fewer satellites

**Problem**: Poor simulation performance
**Solutions**:
1. **Reduce satellite count**: Use smaller constellations for testing
2. **Increase time step**: Trade accuracy for speed
3. **Disable 3D visualization**: Focus on computation
4. **Close other applications**: Free up system resources

#### Data Upload Issues

**Problem**: CSV upload fails or produces errors
**Common Issues**:
- Incorrect file format
- Missing required columns
- Invalid orbital parameters

**Solutions**:
1. **Check CSV format**:
   ```csv
   satellite_id,name,altitude,inclination,raan,eccentricity,arg_perigee,mean_anomaly
   sat_001,Test Sat,550,53.0,0,0,0,0
   ```

2. **Validate parameters**:
   - Altitude: 200-50,000 km
   - Inclination: 0-180 degrees
   - RAAN: 0-360 degrees
   - Eccentricity: 0-0.9
   - All angles in degrees

3. **Check file encoding**: Use UTF-8 encoding

#### Performance Optimization

**Slow 3D Visualization**:
1. **Reduce satellite count** in view (limit to <50 visible)
2. **Lower graphics quality** settings
3. **Close other browser tabs**
4. **Use Chrome or Firefox** for better WebGL performance

**Long Simulation Times**:
1. **Increase time step** (trade accuracy for speed)
2. **Reduce simulation duration**
3. **Use faster routing algorithms** (Spray-and-Wait vs Epidemic)
4. **Disable detailed logging**

### Debug Mode

#### Enable Debug Logging
**Backend**:
```bash
export LOG_LEVEL=DEBUG
python src/main.py
```

**Frontend**:
```javascript
// In browser console
localStorage.setItem('debug', 'true')
```

#### Monitoring Tools

**Backend Monitoring**:
- **Health Endpoint**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Metrics Endpoint**: http://localhost:8000/metrics

**Browser Debugging**:
- **Console Logs**: F12 → Console tab
- **Network Requests**: F12 → Network tab
- **Performance**: F12 → Performance tab

### Support Resources

**Getting Help**:
1. **Check GitHub Issues**: Common problems and solutions
2. **Review Documentation**: Comprehensive usage guide
3. **Enable Debug Mode**: Detailed error information
4. **Collect Logs**: Backend and browser console outputs

**Reporting Issues**:
1. **Include system information**: OS, browser, versions
2. **Provide error messages**: Complete stack traces
3. **Describe reproduction steps**: Minimal example
4. **Attach log files**: Backend and frontend logs

---

**Built with 💙 for advancing delay-tolerant networking research and satellite communication understanding.**

*This documentation is continuously updated. For the latest version, visit the project repository.*