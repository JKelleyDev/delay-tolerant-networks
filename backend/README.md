# DTN Backend

Backend simulation engine for the Delay Tolerant Networks project.

## Structure

- `src/dtn/core/` - Core DTN simulation components (bundles, physical layer)
- `src/dtn/orbital/` - Orbital mechanics and satellite mobility 
- `src/dtn/routing/` - DTN routing algorithms (Epidemic, PRoPHET, Spray-and-Wait)
- `src/dtn/experiments/` - Data collection and analysis framework
- `src/dtn/api/` - Web API server for frontend communication

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Running

```bash
# Run simulation
python src/main.py

# Run API server
python -m dtn.api.server

# Run tests
make test

# Run all quality checks
make all
```