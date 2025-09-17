# Delay Tolerant Networks (DTN) - Bundle Implementation

A DTN bundle data structure implementation for satellite communication networks with comprehensive testing and CI/CD pipeline.

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/JKelleyDev/delay-tolerant-networks.git
cd delay-tolerant-networks

# Install dependencies
make install

# Run all quality checks (recommended before committing)
make all

# Run tests only
make test
```

## 📁 Project Structure

```
delay-tolerant-networks/
├── src/                     # Source code
│   ├── __init__.py         # Package initialization  
│   ├── bundle.py           # Core DTN Bundle implementation
│   └── main.py             # Main entry point (empty)
├── tests/                  # Test suite
│   ├── __init__.py         # Test package init
│   └── test_bundle.py      # Bundle unit tests (10 tests)
├── docs/                   # Documentation
│   └── bundle_format_spec.md  # Bundle format specification
├── .github/workflows/      # CI/CD pipeline
│   └── ci.yml              # GitHub Actions workflow
├── Makefile               # Build automation and development commands
├── requirements.txt       # Python dependencies
├── requirements-dev.txt   # Development dependencies
└── README.md             # This file
```

## 🛠️ Development Commands (Makefile)

### Essential Commands

| Command | Description | When to use |
|---------|-------------|-------------|
| `make help` | Show all available commands | When you need guidance |
| `make install` | Install dependencies | First setup or new dependencies |
| `make test` | Run unit tests | Quick testing during development |
| `make all` | **Run everything** (format, lint, typecheck, test) | **Before committing** |

### Individual Quality Checks

| Command | Description | What it does |
|---------|-------------|--------------|
| `make format` | Format code with black | Auto-formats Python code |
| `make lint` | Check code style with flake8 | Identifies style issues |
| `make typecheck` | Type checking with mypy | Validates type annotations |
| `make coverage` | Generate test coverage report | HTML + terminal coverage |

### Development Setup

| Command | Description | When to use |
|---------|-------------|-------------|
| `make dev-setup` | Install dev dependencies + pre-commit | Initial development setup |
| `make pre-commit` | Run pre-commit hooks | Before committing changes |
| `make clean` | Clean temporary files | Cleanup build artifacts |

## 🧪 Testing

### Test Coverage
- **Current Coverage**: 93% overall, 98% on bundle module
- **Required Coverage**: ≥80% (enforced by CI)
- **Test Count**: 10 comprehensive unit tests

### Running Tests
```bash
# Run all tests
make test

# Run tests with coverage report
make coverage

# View coverage in browser
open htmlcov/index.html
```

### Test Structure
- **Unit Tests**: `tests/test_bundle.py`
- **Coverage**: Bundle creation, validation, serialization, TTL handling
- **Satellite Features**: Long-delay tolerance, priority handling

## 🏗️ DTN Bundle Implementation

### Core Features
- ✅ **Bundle Class**: Complete data structure with all required fields
- ✅ **ID Generation**: SHA256-based unique identifiers  
- ✅ **TTL Management**: Countdown mechanism for satellite delays
- ✅ **Serialization**: JSON-based network transmission format
- ✅ **Validation**: Comprehensive bundle validation
- ✅ **Satellite Support**: Priority levels, store-and-forward flags

### Usage Example
```python
from src.bundle import Bundle, BundlePriority

# Create a DTN bundle
bundle = Bundle(
    source="satellite_1",
    destination="ground_station_1", 
    payload=b"Hello, satellite network!",
    ttl_seconds=3600,  # 1 hour
    priority=BundlePriority.HIGH
)

# Serialize for transmission
data = bundle.serialize()

# Deserialize received data
received_bundle = Bundle.deserialize(data)

# Check expiration
if bundle.is_expired():
    print("Bundle expired")
```

### Bundle Format
See `docs/bundle_format_spec.md` for complete technical specification.

## 🔄 CI/CD Pipeline

### Automated Quality Checks
The CI pipeline runs on every push and pull request:

1. **Code Formatting** - Ensures consistent style with black
2. **Testing** - Runs full test suite on Python 3.10, 3.11, 3.12  
3. **Linting** - Code quality checks with flake8
4. **Coverage** - Enforces ≥80% test coverage

### Pipeline Status
- **Current Status**: ✅ All checks passing
- **Python Versions**: 3.10, 3.11, 3.12
- **Coverage Requirement**: ≥80% (currently 93%)

## 🔧 Development Workflow

### Before You Start
```bash
# Set up development environment
make dev-setup

# This installs:
# - All dependencies
# - Pre-commit hooks
# - Development tools
```

### Daily Development
```bash
# 1. Work on your feature
# ... edit code ...

# 2. Run quality checks (fixes formatting automatically)
make all

# 3. If all passes, commit and push
git add .
git commit -m "Your commit message"
git push
```

### Code Quality Standards
- **Formatting**: Black (88 character line length)
- **Linting**: Flake8 (configured in `.flake8`)
- **Type Checking**: MyPy (static type analysis)
- **Testing**: Pytest (≥80% coverage required)

## 🌟 Key Features for Satellite Networks

### Long-Delay Tolerance
- **TTL Values**: Support orbital periods (hours/days)
- **Expiration Checking**: Graceful handling of expired bundles
- **Time Management**: Creation time vs transmission time tracking

### Satellite-Specific Features
- **Priority Levels**: LOW, NORMAL, HIGH, CRITICAL for emergency communications
- **Store-and-Forward**: Optimization flags for limited contact windows
- **Bundle Size**: Efficient serialization for bandwidth-constrained links

### Network Resilience
- **Validation**: Comprehensive bundle integrity checking
- **Error Handling**: Graceful degradation on invalid data
- **Deterministic IDs**: Collision-resistant identifier generation

## 📖 Documentation

- **Bundle Format**: `docs/bundle_format_spec.md` - Complete technical specification
- **API Reference**: Docstrings in `src/bundle.py`
- **Test Examples**: `tests/test_bundle.py` - Usage examples and edge cases

## 🤝 Contributing

### Pull Request Process
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and run `make all` 
3. Ensure all CI checks pass
4. Submit pull request

### Code Review Requirements
- ✅ All CI checks passing
- ✅ Code review approval
- ✅ Test coverage maintained ≥80%
- ✅ Documentation updated if needed

## 🚨 Troubleshooting

### Common Issues

**CI failing on formatting:**
```bash
make format  # Auto-fix formatting
```

**Tests failing locally:**
```bash
make test    # Run tests
make coverage # Check coverage
```

**Import errors:**
```bash
make install  # Reinstall dependencies
```

**Coverage below 80%:**
```bash
make coverage  # See coverage report
# Add tests for uncovered code
```

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check `docs/` directory for detailed specifications

---

## 🏆 Project Status

### Current Progress: Sprint 1 (Weeks 1-2) - Foundation & Architecture

**Goal:** Establish architecture and make satellite vs terrestrial decision

#### ✅ **Completed (Pair 1 - Partial):**
- Bundle layer foundation (IDs, TTL, basic message structure) 
- Bundle data structures with satellite-specific features
- Comprehensive test suite (93% coverage)
- CI/CD pipeline with quality gates
- Professional development workflow

#### 🚧 **In Progress:**
- **Architecture Decision:** Satellite vs BLE/Wi-Fi Direct (end of week 1)
- PHY abstraction layer with chosen technology stubs
- Simple Epidemic routing as proof-of-concept
- Define networking APIs for other pairs

#### ⏳ **Remaining Sprint 1 Tasks:**

**Pair 1 - Core Networking:**
- Complete architecture decision (satellite vs terrestrial)
- PHY abstraction layer implementation
- Basic Epidemic routing implementation
- Networking API definitions for other pairs

**Pair 2 - Mobility & Data:**
- Contact plan CSV parser (works for both satellite and terrestrial)
- **If satellite:** Orbital mechanics basics and satellite contact windows
- **If terrestrial:** Random Waypoint mobility model
- Experiment framework setup and data collection interfaces
- Node state tracking and logging foundation

**Pair 3 - GUI & Visualization:**
- 3D map framework with basic node rendering
- **Satellite consideration:** Earth globe view vs flat terrain
- Project UI shell and basic controls
- Geographic/orbital coordinate system and camera controls

### Sprint Planning Overview

#### Sprint 2 (Weeks 3-4): Core Implementation
- Complete all 3 routing algorithms (Epidemic, PRoPHET, Spray-and-Wait)
- Technology-specific implementations (satellite or terrestrial)
- Basic ARQ and buffer management
- 3D visualization foundations

#### Sprint 3 (Weeks 5-6): Advanced Features
- Long delay tolerance and store-and-forward optimization
- Fragmentation and reassembly
- Custody transfer mechanisms
- Advanced buffer policies

#### Sprint 4 (Weeks 7-8): Integration & Experiments
- System integration and optimization
- Execute experiments E1 and E2
- Performance profiling and bottleneck fixes
- Complete visualization features

#### Sprint 5 (Weeks 9-10): Final Experiments & Presentation
- Final bug fixes and edge case handling
- Complete experiment E3
- Comprehensive results analysis
- Final UI polish and demo preparation

---

*Generated with Claude Code - Professional DTN implementation for satellite networks*