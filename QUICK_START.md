# Quick Start Guide - DTN Simulator

## 🚀 Getting Started in 3 Steps

### 1. Start the Development Environment
```bash
# From the project root directory
./scripts/start-dev.sh
```

This will start both the backend API server and frontend development server.

### 2. Access the Application
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 3. Test the Simulator

#### Create Your First Simulation
1. Navigate to the **Simulation** tab
2. Select a constellation (e.g., "Starlink")
3. Choose a routing algorithm (e.g., "Epidemic Routing")
4. Set duration (e.g., 6 hours)
5. Click "Create Simulation"
6. Use the play button to start the simulation

#### Upload a Custom Constellation
1. Navigate to the **Constellations** tab
2. Click "Upload Constellation"
3. Use the sample CSV file provided or create your own
4. Download sample: http://localhost:3000/sample_constellation.csv

#### Run an Experiment
1. Navigate to the **Experiments** tab
2. Click "New Experiment"
3. Select multiple routing algorithms to compare
4. Configure parameters and start the experiment

## 🔧 Manual Server Control

If you prefer to start servers individually:

### Backend Only
```bash
./scripts/start-backend.sh
```

### Frontend Only
```bash
./scripts/start-frontend.sh
```

## 📊 Key Features to Test

### 1. Constellation Management
- **Built-in Constellations**: Starlink, Kuiper, GPS, GEO, Molniya
- **Custom Upload**: CSV format with orbital elements
- **Visualization**: Satellite count and orbital parameters

### 2. DTN Routing Algorithms
- **Epidemic**: Flood-based replication for maximum delivery
- **PRoPHET**: Probabilistic routing using encounter history  
- **Spray-and-Wait**: Controlled replication with direct delivery

### 3. Ground Station Network
- **Los Angeles** (34.0522°N, 118.2437°W)
- **Tokyo** (35.6762°N, 139.6503°E)
- Configurable elevation masks and coverage areas

### 4. Performance Metrics
- Delivery ratio and end-to-end delay
- Hop count distribution
- Network overhead analysis
- Buffer utilization tracking

## 🧪 Sample Test Scenarios

### Scenario 1: LA to Tokyo Communication
```
Constellation: Starlink (1,584 satellites)
Routing: PRoPHET
Duration: 6 hours
Traffic: Uniform pattern between LA and Tokyo
```

### Scenario 2: Algorithm Comparison
```
Constellation: Kuiper (3,236 satellites)
Compare: Epidemic vs PRoPHET vs Spray-and-Wait
Duration: 24 hours
Metrics: Delivery ratio, delay, overhead
```

### Scenario 3: Custom Constellation Test
```
Upload: Custom small constellation (10 satellites)
Routing: Epidemic
Duration: 12 hours
Analysis: Coverage and connectivity patterns
```

## 🐛 Troubleshooting

### Backend Issues
- **Port 8000 in use**: Change port in `backend/src/main.py`
- **Import errors**: Install dependencies with `pip install fastapi uvicorn`
- **API not responding**: Check `http://localhost:8000/health`

### Frontend Issues
- **Port 3000 in use**: Change port in `frontend/vite.config.js`
- **Blank page**: Check browser console for errors
- **API errors**: Ensure backend is running on port 8000

### Common Issues
- **CORS errors**: Backend CORS is configured for localhost:3000
- **WebSocket errors**: Check network connectivity
- **File upload fails**: Ensure CSV format matches requirements

## 📈 Next Steps

Once you have the basic simulator running:

1. **Explore the API**: Visit http://localhost:8000/docs for full API documentation
2. **Customize Constellations**: Create CSV files with your own satellite configurations
3. **Analyze Results**: Use the experiment framework to compare routing performance
4. **Extend Functionality**: Add new routing algorithms or modify existing ones

## 💡 Tips for Best Results

- Start with small constellations (10-50 satellites) for faster testing
- Use shorter simulation durations (1-6 hours) during development
- Check the health endpoint regularly to monitor system status
- Use the browser developer tools to inspect WebSocket traffic
- Monitor console logs for debugging information

## 🎯 Project Goals Achieved

✅ **Complete DTN Simulator** with realistic satellite communications
✅ **FastAPI Backend** with comprehensive REST API and WebSocket support  
✅ **React Frontend** with modern UI and 3D visualization framework
✅ **Multiple Routing Algorithms** (Epidemic, PRoPHET, Spray-and-Wait)
✅ **Orbital Mechanics** with accurate satellite positioning
✅ **Constellation Support** including CSV upload for custom configurations
✅ **Ground Station Network** with LA to Tokyo communication example
✅ **Performance Analysis** with comprehensive metrics and experiment framework
✅ **Professional Architecture** meeting all OSI model requirements

The simulator is ready for testing, demonstration, and research use! 🚀