# DTN Simulator V2 Architecture

## Overview
Redesigned delay-tolerant network simulator for NASA-level space communication research with realistic orbital mechanics, advanced routing algorithms, and professional 3D visualization.

## Core Design Principles
1. **Accuracy**: Real orbital mechanics using industry-standard models
2. **Scalability**: Handle thousands of satellites with efficient algorithms  
3. **Modularity**: Clean separation between simulation, networking, and visualization
4. **Performance**: Optimized for long-running simulations with time acceleration
5. **Extensibility**: Easy to add new routing algorithms and constellation types

## Backend Architecture

### 1. Core Simulation Engine
```
backend/src/dtn_sim/
├── core/
│   ├── simulation.py          # Main simulation coordinator
│   ├── time_manager.py        # Simulation time and acceleration
│   ├── event_scheduler.py     # Discrete event simulation
│   └── metrics_collector.py   # Real-time metrics collection
├── orbital/
│   ├── mechanics.py           # SGP4/SDP4 orbital propagation
│   ├── contact_prediction.py  # Visibility and link analysis
│   ├── constellation.py       # Constellation management
│   └── ground_stations.py     # Ground station modeling
├── networking/
│   ├── nodes/
│   │   ├── satellite_node.py  # Satellite DTN node
│   │   ├── ground_node.py     # Ground station DTN node
│   │   └── buffer_manager.py  # Enhanced buffer management
│   ├── routing/
│   │   ├── base_router.py     # Abstract router interface
│   │   ├── epidemic.py        # Epidemic routing
│   │   ├── prophet.py         # PRoPHET routing  
│   │   ├── spray_wait.py      # Spray-and-Wait
│   │   ├── cgr.py             # Contact Graph Routing
│   │   └── adaptive.py        # Adaptive routing
│   ├── protocols/
│   │   ├── bundle_protocol.py # Bundle Protocol (RFC 5050)
│   │   ├── tcp_cl.py          # TCP Convergence Layer
│   │   └── space_packet.py    # CCSDS Space Packet Protocol
│   └── traffic/
│       ├── generator.py       # Traffic pattern generation
│       ├── models.py          # Traffic models (Poisson, burst, etc.)
│       └── priorities.py      # Bundle priority management
└── analysis/
    ├── metrics.py             # Performance metrics calculation
    ├── path_analysis.py       # Packet path reconstruction
    ├── network_analysis.py    # Network topology analysis
    └── export.py              # Results export (CSV, JSON, etc.)
```

### 2. API Server
```
backend/src/api/
├── app.py                     # FastAPI application
├── routers/
│   ├── simulation.py          # Simulation control endpoints
│   ├── constellations.py      # Constellation management
│   ├── experiments.py         # Experiment configuration/execution
│   ├── real_time.py           # Real-time data streaming
│   └── analysis.py            # Results analysis endpoints
├── models/
│   ├── simulation_config.py   # Pydantic models for configuration
│   ├── constellation_models.py# Satellite/ground station models
│   └── experiment_models.py   # Experiment configuration models
├── websockets/
│   ├── simulation_stream.py   # Real-time simulation updates
│   ├── metrics_stream.py      # Live metrics streaming
│   └── visualization_stream.py# 3D visualization data
└── middleware/
    ├── cors.py                # CORS configuration
    ├── auth.py                # Optional authentication
    └── rate_limiting.py       # API rate limiting
```

### 3. Data Layer
```
backend/src/data/
├── models/
│   ├── satellite.py           # Satellite data model
│   ├── ground_station.py      # Ground station data model
│   ├── constellation.py       # Constellation configuration
│   ├── experiment.py          # Experiment results model
│   └── metrics.py             # Metrics data model
├── storage/
│   ├── file_storage.py        # CSV/JSON file handling
│   ├── database.py            # Optional SQLite/PostgreSQL
│   └── cache.py               # Redis caching for performance
├── loaders/
│   ├── tle_loader.py          # Two-Line Element set loader
│   ├── constellation_loader.py# Constellation CSV loader
│   ├── ground_station_loader.py# Ground station loader
│   └── traffic_loader.py      # Traffic pattern loader
└── exporters/
    ├── csv_exporter.py        # CSV export functionality
    ├── json_exporter.py       # JSON export
    ├── kml_exporter.py        # Google Earth KML export
    └── matlab_exporter.py     # MATLAB format export
```

## Enhanced Features

### 1. Realistic Orbital Mechanics
- **SGP4/SDP4 Propagation**: Industry-standard satellite tracking
- **Perturbation Models**: J2, drag, solar radiation pressure
- **Coordinate Systems**: ECI, ECEF, topocentric conversions
- **Eclipse Modeling**: Shadow effects on solar-powered satellites
- **Doppler Effects**: Frequency shifts for realistic communication

### 2. Advanced DTN Protocols
- **Bundle Protocol v7**: Latest RFC 9171 implementation
- **Contact Graph Routing**: Predictive routing with scheduled contacts
- **Adaptive Algorithms**: ML-based routing optimization
- **QoS Support**: Priority-based bundle handling
- **Custody Transfer**: Reliable bundle delivery guarantees

### 3. Professional Metrics Collection
```python
class NetworkMetrics:
    # Delivery Performance
    delivery_ratio: float
    end_to_end_delay: List[float]
    hop_count_distribution: Dict[int, int]
    
    # Network Efficiency  
    network_overhead: float
    bandwidth_utilization: Dict[str, float]
    buffer_occupancy: Dict[str, TimeSeries]
    
    # Routing Analysis
    route_stability: float
    contact_prediction_accuracy: float
    algorithm_comparison: Dict[str, Metrics]
    
    # System Performance
    packet_loss_rate: float
    congestion_events: List[CongestionEvent]
    energy_consumption: Dict[str, float]
```

### 4. Real-time Simulation
- **Discrete Event Simulation**: Efficient event-driven architecture
- **Time Acceleration**: 1x to 10000x simulation speed
- **Pause/Resume**: Interactive simulation control
- **Checkpointing**: Save/restore simulation state
- **Live Monitoring**: Real-time metrics and visualization

### 5. Constellation Library
```python
# Pre-built realistic constellations
CONSTELLATION_LIBRARY = {
    "starlink": {
        "satellites": 1584,
        "shells": [
            {"altitude": 550, "inclination": 53.0, "count": 1584}
        ],
        "description": "SpaceX Starlink constellation (Phase 1)"
    },
    "kuiper": {
        "satellites": 3236,
        "shells": [
            {"altitude": 630, "inclination": 51.9, "count": 1296},
            {"altitude": 610, "inclination": 42.0, "count": 1156},
            {"altitude": 590, "inclination": 33.0, "count": 784}
        ],
        "description": "Amazon Project Kuiper constellation"
    },
    "earth_mars_optimal": {
        "satellites": 200,
        "description": "Optimized Earth-Mars communication network",
        "design": "custom_interplanetary"
    }
}
```

## Technology Stack

### Backend
- **Python 3.11+**: Core language
- **FastAPI**: Modern async web framework
- **Skyfield**: Astronomical calculations
- **NumPy/SciPy**: Scientific computing
- **Pydantic**: Data validation
- **WebSockets**: Real-time communication
- **SQLite/PostgreSQL**: Optional persistence
- **Redis**: Caching and session management

### Performance Optimizations
- **Async/Await**: Non-blocking I/O operations
- **Cython**: Critical path optimization
- **NumPy Vectorization**: Batch calculations
- **Multiprocessing**: Parallel simulation execution
- **Memory Mapping**: Efficient large dataset handling

## Deployment Architecture

### Development Environment
```
docker-compose.yml:
  - backend: Python FastAPI server
  - frontend: React development server  
  - redis: Caching layer
  - postgres: Optional database
```

### Production Environment
```
Kubernetes deployment:
  - API Gateway: Load balancing
  - Backend Pods: Horizontally scalable
  - Database: Managed PostgreSQL
  - Cache: Redis cluster
  - Monitoring: Prometheus + Grafana
```

## API Design

### RESTful Endpoints
```python
# Simulation Management
POST /api/v2/simulations                    # Create simulation
GET /api/v2/simulations/{id}                # Get simulation status
PUT /api/v2/simulations/{id}/control        # Start/stop/pause
DELETE /api/v2/simulations/{id}             # Delete simulation

# Constellation Management  
GET /api/v2/constellations                  # List available constellations
POST /api/v2/constellations                 # Upload custom constellation
GET /api/v2/constellations/{id}/satellites  # Get satellite positions
GET /api/v2/constellations/{id}/contacts    # Get contact predictions

# Experiments
POST /api/v2/experiments                     # Create experiment
GET /api/v2/experiments/{id}/results         # Get results
GET /api/v2/experiments/{id}/metrics         # Get detailed metrics
GET /api/v2/experiments/{id}/export/{format} # Export results

# Real-time Data
WS /ws/simulation/{id}                       # Simulation updates
WS /ws/metrics/{id}                          # Live metrics
WS /ws/visualization/{id}                    # 3D visualization data
```

### GraphQL API (Optional)
```graphql
type Simulation {
  id: ID!
  status: SimulationStatus!
  constellation: Constellation!
  metrics: Metrics!
  satellites: [Satellite!]!
  experiments: [Experiment!]!
}

type Query {
  simulation(id: ID!): Simulation
  constellations: [Constellation!]!
  experiments(simulationId: ID!): [Experiment!]!
}

type Mutation {
  createSimulation(config: SimulationInput!): Simulation!
  startSimulation(id: ID!): Boolean!
  uploadConstellation(file: Upload!): Constellation!
}

type Subscription {
  simulationUpdates(id: ID!): SimulationUpdate!
  metricsStream(id: ID!): Metrics!
}
```

## Security & Performance

### Security Features
- Input validation and sanitization
- Rate limiting on API endpoints  
- Optional JWT authentication
- CORS configuration
- File upload restrictions
- SQL injection prevention

### Performance Features
- Database connection pooling
- Response caching with TTL
- Async request handling
- Background task queues
- Memory usage monitoring
- CPU usage optimization

## Testing Strategy

### Unit Tests
- Orbital mechanics calculations
- Routing algorithm correctness
- Bundle protocol implementation
- Metrics calculation accuracy

### Integration Tests  
- API endpoint functionality
- Database operations
- WebSocket communications
- File upload/processing

### Performance Tests
- Large constellation handling
- Long-running simulations
- Memory usage under load
- Response time benchmarks

### Validation Tests
- Comparison with real satellite data
- Routing algorithm performance
- Network topology accuracy
- Ground truth verification

This architecture provides a solid foundation for a professional-grade DTN simulator that can handle NASA-level requirements while remaining extensible and maintainable.