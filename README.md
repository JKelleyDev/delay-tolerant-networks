# Delay Tolerant Networks (DTN) Simulator

**Project Groups 3&7 - Advanced DTN Implementation with Satellite Communications**

A comprehensive DTN simulator implementing satellite communication networks with proper OSI model abstraction, comprehensive routing algorithms, and real-time 3D visualization. Built for academic research and network performance analysis.

## 🎯 Project Overview

### Core Mission
Design and implement a production-quality DTN simulator that demonstrates mastery of:
- **Complete OSI Model Implementation** - All 7 layers from Physical through Application with clean abstraction
- **Advanced DTN Protocols** - Multiple routing algorithms with performance comparison across network layers
- **Satellite Network Modeling** - Realistic orbital mechanics and contact prediction for space communications
- **Professional Software Engineering** - Enterprise-grade architecture and development practices

### Architecture Decision: **Satellite Communications** 🛰️
We chose satellite communication over terrestrial (BLE/Wi-Fi Direct) to showcase:
- Complex mobility models with orbital mechanics
- Long-delay tolerance and store-and-forward optimization  
- Advanced contact prediction algorithms
- Real-world space communication challenges

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/JKelleyDev/delay-tolerant-networks.git
cd delay-tolerant-networks

# Install backend dependencies
cd backend && pip install -r requirements.txt && cd ..

# Install frontend dependencies  
cd frontend && npm install && cd ..

# Start development environment (both frontend + backend)
./scripts/start-dev.sh

# Or run individually:
# Backend API: cd backend && python -m dtn.api.server
# Frontend:    cd frontend && npm run dev
```

## 🏗️ Project Architecture

### Three-Pair Development System

#### **Pair 1: Core Networking & Protocols** 
- DTN Bundle layer implementation
- Routing algorithms (Epidemic, PRoPHET, Spray-and-Wait)
- ARQ and buffer management
- PHY abstraction layer

#### **Pair 2: Satellite Mobility & Data Collection**
- Orbital mechanics calculations
- Contact window prediction  
- Mobility model integration
- Experiment data collection framework

#### **Pair 3: GUI & Visualization**
- 3D satellite visualization with Earth globe
- Real-time contact window display
- Performance metrics dashboard
- Interactive controls and configuration

### Complete OSI Model Implementation

```
┌─────────────────┐
│   Application   │ ← Experiment Framework & Data Collection
├─────────────────┤
│  Presentation   │ ← Data Encoding, Compression, Encryption
├─────────────────┤
│    Session      │ ← Session Management, Connection Control
├─────────────────┤
│   Transport     │ ← DTN Bundle Layer (IDs, TTL, Fragmentation)  
├─────────────────┤
│    Network      │ ← Routing (Epidemic, PRoPHET, Spray-and-Wait)
├─────────────────┤
│   Data Link     │ ← ARQ, Buffer Management, Contact Windows
├─────────────────┤
│   Physical      │ ← Satellite Communication Model
└─────────────────┘
```

#### **Layer Implementation Details:**

**Application Layer (7):** Experiment configuration, data collection, performance analysis, user interfaces

**Presentation Layer (6):** Bundle payload encoding/decoding, data compression for bandwidth optimization, optional encryption for secure communications

**Session Layer (5):** Contact session establishment, connection state management, session recovery after network partitions

**Transport Layer (4):** DTN Bundle protocol with reliable delivery, fragmentation/reassembly, flow control

**Network Layer (3):** DTN routing algorithms, store-and-forward decisions, path optimization

**Data Link Layer (2):** Link-level ARQ, buffer management, contact window utilization, error detection/correction

**Physical Layer (1):** Satellite communication channels, orbital mechanics, RF signal propagation, antenna modeling

## 📁 Project Structure

```
delay-tolerant-networks/
├── src/                          # Source code
│   ├── bundle.py                 # DTN Bundle implementation (Pair 1)
│   ├── orbital_mechanics.py      # Satellite orbital calculations (Pair 2)  
│   ├── contact_prediction.py     # Contact window algorithms (Pair 2)
│   ├── satellite_mobility.py     # Mobility model integration (Pair 2)
│   ├── constellation_config.py   # Satellite constellation management (Pair 2)
│   ├── experiment_data.py        # Data collection framework (Pair 2)
│   └── main.py                   # Main simulation entry point
├── tests/                        # Comprehensive test suite
│   ├── test_bundle.py           # Bundle layer tests (93% coverage)
│   └── test_*.py                # Module-specific test suites
├── docs/                         # Technical documentation
│   ├── satellite_communication_architecture.md  # Complete satellite architecture
│   ├── pair2_implementation_guide.md           # Implementation roadmap
│   ├── bundle_format_spec.md                   # DTN bundle specification
│   └── epics/iteration_1/                      # Sprint planning and tickets
├── .github/workflows/            # CI/CD pipeline
│   └── ci.yml                   # Automated quality checks
├── Makefile                     # Development automation
├── requirements.txt             # Production dependencies
└── requirements-dev.txt         # Development dependencies
```

## 🛰️ Satellite Implementation Features

### Constellation Support
- **LEO:** Low Earth Orbit (Iridium, Starlink-like configurations)
- **MEO:** Medium Earth Orbit (GPS-like navigation constellations)
- **GEO:** Geostationary (3-satellite minimal coverage)
- **HEO:** Highly Elliptical Orbit (Molniya-type for polar coverage)
- **Interplanetary:** Earth-Mars communication scenarios

### Advanced Orbital Mechanics
- Accurate position propagation using Keplerian elements
- Coordinate system transformations (ECI, ECEF, geodetic)
- Ground track calculations and subsatellite points
- Contact window prediction with elevation constraints
- Real-time satellite tracking and visibility determination

### DTN-Optimized Features
- Long-delay tolerance (minutes to hours)
- Store-and-forward optimization for intermittent contacts
- Priority-based message handling (LOW, NORMAL, HIGH, CRITICAL)
- Contact-aware routing with orbital predictions
- Comprehensive experiment data collection

## 🧪 Experiments & Analysis

### Required Experiments (Meeting Academic Standards)

#### **E1: Protocol Comparison**
- **Metrics:** Delivery ratio, delay distribution, overhead ratio
- **Variables:** Node counts (10, 25, 50, 100 satellites)
- **Algorithms:** Epidemic vs PRoPHET vs Spray-and-Wait

#### **E2: Buffer Size Impact**  
- **Buffer Sizes:** 5MB, 20MB, 80MB per satellite
- **Analysis:** Storage efficiency, message drops, performance curves
- **Constellation:** Starlink-like LEO (1584 satellites)

#### **E3: TTL Impact Analysis**
- **TTL Values:** 30, 120, 480 minutes  
- **Focus:** Message expiration patterns, orbital period alignment
- **Scenarios:** Various constellation types and contact patterns

### Data Collection Framework
- **Mobility Logging:** Real-time satellite positions and velocities
- **Contact Events:** Link establishment/termination with quality metrics
- **Network States:** Buffer occupancy, routing tables, message flows
- **Performance Metrics:** Automated calculation of delivery ratios and delays

## 🎮 GUI & Visualization

### 3D Earth Visualization
- **Globe Rendering:** Textured Earth with geographic features
- **Satellite Tracking:** Real-time orbital motion with accurate positioning
- **Ground Stations:** Global coverage with antenna coverage areas
- **Contact Links:** Animated communication beams during active contacts

### Real-Time Dashboards
- **Contact Timeline:** Gantt chart showing scheduled communication windows
- **Buffer Status:** Per-satellite storage utilization bars
- **Performance Metrics:** Live delivery ratios, delay CDFs, overhead tracking
- **Network Topology:** Dynamic connectivity graph with routing paths

### Interactive Controls
- **Time Acceleration:** 1x to 10000x simulation speed
- **Constellation Selection:** Preset configurations with custom editing
- **Experiment Configuration:** Parameter adjustment and scenario setup
- **Data Export:** CSV/JSON export for external analysis tools

## 🛠️ Development Commands (Makefile)

### Essential Commands

| Command | Description | When to use |
|---------|-------------|-------------|
| `make help` | Show all available commands | When you need guidance |
| `make install` | Install dependencies | First setup or new dependencies |
| `make test` | Run unit tests | Quick testing during development |
| `make all` | **Run everything** (format, lint, typecheck, test) | **Before committing** |

### Quality Assurance

| Command | Description | Coverage Target |
|---------|-------------|-----------------|
| `make format` | Format code with black | Auto-formatting |
| `make lint` | Check code style with flake8 | Zero violations |
| `make typecheck` | Type checking with mypy | Complete type safety |
| `make coverage` | Generate test coverage report | ≥85% per module |

## 🧪 Testing Strategy

### Test-Driven Development (TDD)
- **Write tests first** before implementing functionality
- **Comprehensive coverage** targeting >85% per module
- **Integration testing** across pair boundaries
- **Performance benchmarking** for real-time requirements

### Current Test Status
- **Bundle Module:** 93% coverage, 10 comprehensive tests
- **Satellite Modules:** Boilerplate with TODO-driven test requirements
- **CI Pipeline:** Automated testing on Python 3.10, 3.11, 3.12

### Validation Strategy
- **Mathematical Accuracy:** Orbital calculations validated against TLE data
- **Real-World Comparison:** Contact predictions vs published satellite schedules  
- **Performance Benchmarks:** Real-time operation requirements
- **Cross-Platform Testing:** Ensure compatibility across development environments

## 🏆 Sprint Planning Overview

### **Sprint 1 (Weeks 1-2): Foundation & Architecture**
**Goal:** Establish architecture, technology decisions, and development foundations

#### **Pair 1 - Core Networking:**
- DTN Bundle layer foundation (IDs, TTL, basic message structure)
- Bundle data structures with satellite-specific features
- PHY abstraction layer design and initial implementation
- Basic routing algorithm framework

#### **Pair 2 - Mobility & Data:**
- Satellite vs terrestrial architecture decision
- Orbital mechanics framework and contact prediction design
- Contact plan CSV format specification
- Experiment data collection framework design

#### **Pair 3 - GUI & Visualization:**
- 3D visualization framework selection and setup
- Earth globe vs flat terrain rendering decision
- Project UI shell and basic controls
- Camera system and coordinate transformations

### **Sprint 2 (Weeks 3-4): Core Implementation**
**Goal:** Implement core functionality across all layers

#### **Pair 1:**
- Complete routing algorithms (Epidemic, PRoPHET, Spray-and-Wait)
- ARQ implementation (stop-and-wait or sliding window)
- Basic buffer management and drop policies
- PHY layer integration with satellite model

#### **Pair 2:**
- Orbital mechanics calculations (position, velocity, propagation)
- Contact window prediction algorithms
- Real-time satellite mobility integration
- CSV contact plan import/export functionality

#### **Pair 3:**
- 3D Earth visualization with satellite tracking
- Real-time position updates and orbital motion
- Contact window timeline visualization
- Basic performance metrics display

### **Sprint 3 (Weeks 5-6): Advanced Features**
**Goal:** Advanced DTN features and optimization

#### **Pair 1:**
- Fragmentation and reassembly for large messages
- Custody transfer mechanisms
- Advanced buffer policies and prioritization
- Duplicate suppression and restoration

#### **Pair 2:**
- Advanced constellation management (LEO/MEO/GEO/HEO)
- Contact plan change events (mid-simulation rescheduling)
- Performance optimization for large constellations
- Comprehensive experiment data collection

#### **Pair 3:**
- Advanced visualization features (animated message paths)
- Buffer fill bars and network topology display
- Interactive constellation editing
- Performance dashboards and real-time metrics

### **Sprint 4 (Weeks 7-8): Integration & Experiments**
**Goal:** System integration and initial experiments

#### **All Pairs Integration:**
- Complete system integration testing
- Performance profiling and optimization
- Execute experiments E1 and E2
- Mid-simulation contact plan changes implementation

### **Sprint 5 (Weeks 9-10): Final Experiments & Presentation**
**Goal:** Final polish and comprehensive analysis

#### **All Pairs:**
- Complete experiment E3 (TTL impact analysis)
- Final bug fixes and edge case handling
- Results analysis and insight generation
- Presentation preparation and demo polish

## 🎖️ Competitive Advantages

### Technical Excellence
- **Enterprise Architecture:** Clean separation of concerns across OSI layers
- **Satellite Complexity:** Advanced orbital mechanics beyond basic terrestrial DTN
- **Real-Time Performance:** Sub-millisecond orbital calculations for GUI responsiveness
- **Academic Rigor:** Comprehensive experiment design with statistical analysis

### Professional Engineering
- **Code Quality:** >85% test coverage, type safety, automated CI/CD
- **Documentation:** API references, implementation guides, architectural decisions
- **Reproducibility:** Containerized deployment, configuration management
- **Maintainability:** Modular design, clear interfaces, comprehensive logging

### Research Impact
- **Novel Scenarios:** Interplanetary communication modeling
- **Performance Insights:** Orbital mechanics impact on DTN routing effectiveness
- **Scalability Analysis:** Large constellation performance (1000+ satellites)
- **Real-World Applicability:** Configurations based on actual satellite networks

## 📊 Success Metrics (100 pts Rubric)

| Category | Points | Our Approach |
|----------|--------|--------------|
| **PHY/MAC/Network Fidelity** | 22 | Realistic satellite comm model with orbital mechanics |
| **Wireless Tech Profiles** | 5 | Satellite constellation scenarios (LEO/MEO/GEO/HEO) |
| **Topology/Contact Changes** | 5 | Dynamic orbital contact windows, mid-simulation changes |
| **Connectivity Restoration** | 5 | Store-and-forward, custody transfer, duplicate suppression |
| **Mobility Integration** | 6 | CSV contact plans + orbital mechanics mobility model |
| **GUI Completeness** | 6 | 3D Earth visualization, real-time tracking, dashboards |
| **Experimental Design** | 18 | Rigorous statistical analysis, multiple constellation types |
| **Results & Insights** | 18 | Performance comparison, orbital mechanics impact analysis |
| **Code Quality** | 10 | >85% coverage, CI/CD, professional architecture |
| **Presentation** | 5 | Live satellite tracking demo, performance visualizations |

## 📖 Documentation

### Technical References
- **[Satellite Architecture](docs/satellite_communication_architecture.md)** - Complete orbital mechanics and communication specifications
- **[Implementation Guide](docs/pair2_implementation_guide.md)** - Step-by-step development roadmap for Pair 2
- **[Bundle Specification](docs/bundle_format_spec.md)** - DTN bundle format and API reference
- **[Epic Planning](docs/epics/)** - Sprint tickets organized by iteration

### API Documentation
- **Bundle Layer:** `src/bundle.py` - DTN message handling and serialization
- **Orbital Mechanics:** `src/orbital_mechanics.py` - Satellite position calculations
- **Contact Prediction:** `src/contact_prediction.py` - Communication window algorithms
- **Mobility Integration:** `src/satellite_mobility.py` - Real-time position updates
- **Experiment Framework:** `src/experiment_data.py` - Data collection and analysis

## 🤝 Contributing

### Development Workflow
```bash
# 1. Create feature branch
git checkout -b feature/your-feature

# 2. Implement with TDD approach
# Write tests first, then implement functionality

# 3. Run quality checks
make all

# 4. Commit and push
git add .
git commit -m "Descriptive commit message"
git push origin feature/your-feature

# 5. Create pull request
```

### Code Review Requirements
- ✅ All CI checks passing (format, lint, typecheck, test)
- ✅ Test coverage maintained ≥85%
- ✅ Documentation updated for new features
- ✅ Integration points validated with other pairs
- ✅ Performance benchmarks meet requirements

---

**Built with professional engineering practices to demonstrate DTN expertise and satellite communication mastery** 🛰️

*Ready to outperform the competition with advanced satellite modeling and enterprise-grade architecture.*