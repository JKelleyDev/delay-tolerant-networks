# DTN Simulator - Satellite Network Communication Simulator

**A comprehensive Delay-Tolerant Network (DTN) simulator for satellite communications with realistic orbital mechanics, advanced routing algorithms, and real-time 3D visualization.**

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![React](https://img.shields.io/badge/react-v18.2+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🎯 Project Overview

This DTN simulator addresses the main points of the OSI model for satellite network communications, focusing on delay-tolerant networking protocols that can handle the intermittent connectivity and long delays characteristic of space communications.

### Key Features

- **🛰️ Realistic Orbital Mechanics**: SGP4/SDP4 propagation with accurate satellite positioning
- **🌐 Multiple Constellation Support**: LEO, MEO, GEO, HEO, and custom constellations via CSV upload
- **🔀 Advanced DTN Routing**: Epidemic, PRoPHET, Spray-and-Wait algorithms with performance comparison
- **📡 Ground Station Network**: Global coverage with configurable elevation masks and antenna patterns
- **🎮 3D Visualization**: Real-time satellite tracking with Earth globe and contact window display
- **📊 Comprehensive Analytics**: Performance metrics, delivery ratios, and network analysis
- **⚡ Real-time Simulation**: WebSocket-based live updates with time acceleration up to 10,000x

## 🏗️ Architecture

### Backend (Python + FastAPI)
```
backend/src/dtn/
├── api/                    # REST API and WebSocket endpoints
├── core/                   # Simulation engine and bundle protocol
├── orbital/                # Orbital mechanics and contact prediction
├── networking/             # DTN routing algorithms
│   └── routing/           # Epidemic, PRoPHET, Spray-and-Wait
├── analysis/              # Performance metrics and data collection
└── data/                  # Data models and storage
```

### Frontend (React + Three.js)
```
frontend/src/
├── components/            # UI components and 3D visualization
├── pages/                # Main application views
├── services/             # API communication and WebSocket handling
├── hooks/                # React hooks for data management
└── utils/                # Utilities and helpers
```

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

   Or start servers individually:
   ```bash
   # Backend only (Terminal 1)
   ./scripts/start-backend.sh
   
   # Frontend only (Terminal 2)
   ./scripts/start-frontend.sh
   ```

3. **Access the application**
   - **Frontend**: http://localhost:3000
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

## 📋 Usage Guide

### 1. Creating a Simulation

1. **Choose a Constellation**
   - Select from built-in constellations (Starlink, Kuiper, GPS, etc.)
   - Or upload a custom constellation via CSV file

2. **Configure Parameters**
   - Routing algorithm (Epidemic, PRoPHET, Spray-and-Wait)
   - Simulation duration and time step
   - Ground stations and traffic patterns

3. **Run Simulation**
   - Start/pause/stop controls
   - Real-time metrics dashboard
   - 3D visualization with satellite tracking

### 2. Uploading Custom Constellations

Create a CSV file with the following format:
```csv
satellite_id,name,altitude,inclination,raan,eccentricity,arg_perigee,mean_anomaly
sat_001,Satellite 1,550,53.0,0,0,0,0
sat_002,Satellite 2,550,53.0,0,0,0,60
```

### 3. Running Experiments

1. **Design Experiment**
   - Compare multiple routing algorithms
   - Test different constellation configurations
   - Analyze performance metrics

2. **Execute and Analyze**
   - Automated experiment execution
   - Statistical analysis and insights
   - Export results in CSV/JSON format

## 🧪 Experiment Examples

### E1: Protocol Comparison
```python
# Compare routing algorithms on Starlink constellation
experiment_config = {
    "name": "Starlink Protocol Comparison",
    "constellation_id": "starlink",
    "routing_algorithms": ["epidemic", "prophet", "spray_and_wait"],
    "duration": 24.0,  # hours
    "ground_stations": ["gs_la", "gs_tokyo"],
    "traffic_pattern": "uniform"
}
```

### E2: Los Angeles to Tokyo Communication
```python
# Test communication from LA to Tokyo ground stations
simulation_config = {
    "name": "LA to Tokyo Communication Test",
    "constellation_id": "starlink",
    "routing_algorithm": "prophet",
    "duration": 6.0,  # hours
    "ground_stations": ["gs_la", "gs_tokyo"]
}
```

## 📊 Performance Metrics

The simulator tracks comprehensive performance metrics:

- **Delivery Ratio**: Percentage of bundles successfully delivered
- **End-to-End Delay**: Average time for bundle delivery
- **Hop Count**: Average number of hops per delivered bundle
- **Network Overhead**: Ratio of transmissions to deliveries
- **Buffer Utilization**: Storage usage across network nodes
- **Contact Statistics**: Frequency and duration of communication windows

## 🛰️ Supported Constellations

### Built-in Constellations
- **Starlink (Phase 1)**: 1,584 satellites in LEO (550 km, 53° inclination)
- **Project Kuiper**: 3,236 satellites in multiple LEO shells
- **GPS**: 31 satellites in MEO (20,200 km, 55° inclination)
- **GEO Minimal**: 3 satellites in geostationary orbit
- **Molniya**: 12 satellites in highly elliptical orbit

### Custom Constellation Support
Upload CSV files with orbital elements to test custom configurations:
- Research constellations
- Proposed mega-constellations
- Mission-specific networks
- Interplanetary communication networks

## 🔬 DTN Routing Algorithms

### 1. Epidemic Routing
- **Strategy**: Flood-based replication to all encountered nodes
- **Pros**: High delivery ratio, robust against failures
- **Cons**: High overhead, resource intensive

### 2. PRoPHET Routing
- **Strategy**: Probabilistic routing based on encounter history
- **Pros**: Balanced performance, adaptive to patterns
- **Cons**: Complex state maintenance

### 3. Spray and Wait
- **Strategy**: Limited replication followed by direct delivery
- **Pros**: Controlled overhead, good delay/overhead tradeoff
- **Cons**: Limited coverage in sparse networks

## 📡 OSI Model Implementation

| Layer | Implementation | DTN Features |
|-------|---------------|--------------|
| **Physical (1)** | Satellite RF links, orbital mechanics | Link budgets, eclipse modeling |
| **Data Link (2)** | Contact windows, ARQ protocols | Buffer management, flow control |
| **Network (3)** | DTN routing algorithms | Store-and-forward, path optimization |
| **Transport (4)** | Bundle Protocol (RFC 9171) | Reliable delivery, fragmentation |
| **Session (5)** | Contact session management | Connection state, recovery |
| **Presentation (6)** | Data encoding/compression | Payload optimization |
| **Application (7)** | Simulation control, experiments | Traffic generation, analysis |

## 🔧 API Endpoints

### Simulation Management
- `POST /api/v2/simulation/create` - Create new simulation
- `GET /api/v2/simulation/list` - List all simulations
- `POST /api/v2/simulation/{id}/start` - Start simulation
- `GET /api/v2/simulation/{id}/metrics` - Get performance metrics

### Constellation Management
- `GET /api/v2/constellation/library` - Get built-in constellations
- `POST /api/v2/constellation/upload` - Upload custom constellation
- `GET /api/v2/constellation/{id}/satellites` - Get satellite positions

### Real-time Data (WebSocket)
- `ws://localhost:8000/api/v2/realtime/simulation/{id}` - Live simulation updates
- `ws://localhost:8000/api/v2/realtime/metrics/{id}` - Live performance metrics
- `ws://localhost:8000/api/v2/realtime/visualization/{id}` - 3D visualization data

## 🧪 Testing and Validation

### Unit Tests
```bash
cd backend
python -m pytest tests/ -v --cov=src/dtn
```

### Integration Tests
```bash
# Test full API stack
python -m pytest tests/integration/ -v
```

### Performance Benchmarks
```bash
# Run performance test suite
python -m pytest tests/performance/ --benchmark-only
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint configuration for JavaScript/React
- Write tests for new features
- Update documentation for API changes

## 📈 Roadmap

### Completed ✅
- [x] Core DTN simulation engine
- [x] Realistic orbital mechanics (SGP4/SDP4)
- [x] Three routing algorithms (Epidemic, PRoPHET, Spray-and-Wait)
- [x] FastAPI backend with comprehensive endpoints
- [x] React frontend with 3D visualization setup
- [x] Contact prediction and window management
- [x] Performance metrics and analysis framework

### In Progress 🚧
- [ ] Complete 3D Earth visualization with Three.js
- [ ] Real-time satellite position updates
- [ ] WebSocket integration for live data streaming
- [ ] Advanced performance dashboards

### Planned 🎯
- [ ] Contact Graph Routing (CGR) algorithm
- [ ] Machine learning-based adaptive routing
- [ ] Interplanetary communication scenarios
- [ ] Advanced RF link modeling
- [ ] Integration with real TLE data sources
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Performance optimization with Cython

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **NASA**: For orbital mechanics standards and DTN protocol specifications
- **IETF**: For Bundle Protocol (RFC 9171) and DTN architecture
- **Skyfield**: For accurate astronomical calculations
- **Three.js**: For 3D visualization capabilities
- **FastAPI**: For modern Python web framework
- **React**: For responsive user interface development

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/YourUsername/delay-tolerant-networks/issues)
- **Documentation**: [Project Wiki](https://github.com/YourUsername/delay-tolerant-networks/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/YourUsername/delay-tolerant-networks/discussions)

---

**Built with 💙 for advancing delay-tolerant networking research and satellite communication understanding.**