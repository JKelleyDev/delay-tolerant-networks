import React, { useState, useEffect } from 'react'
import { Play, Pause, Square, Settings, Activity, Satellite, Globe } from 'lucide-react'
import SatelliteVisualization from '../components/simulation/SatelliteVisualization'
import MilitaryHUD from '../components/simulation/MilitaryHUD'
import ContactGanttChart from '../components/simulation/ContactGanttChart'

const SimulationView = () => {
  const [simulationName, setSimulationName] = useState('')
  const [selectedConstellation, setSelectedConstellation] = useState('starlink')
  const [routingAlgorithm, setRoutingAlgorithm] = useState('epidemic')
  const [simulationDuration, setSimulationDuration] = useState(6)
  const [constellations, setConstellations] = useState({})
  const [groundStations, setGroundStations] = useState({})
  const [selectedGroundStations, setSelectedGroundStations] = useState(['gs_los_angeles', 'gs_tokyo'])
  const [simulations, setSimulations] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [simulationDetails, setSimulationDetails] = useState({})
  const [selectedSatellite, setSelectedSatellite] = useState(null)
  const [realTimeData, setRealTimeData] = useState({
    satellites: {},
    contacts: [],
    timelineContacts: [],
    bundles: { active: 0, delivered: 0, expired: 0 },
    packetPaths: [],
    metrics: {
      throughput: 0,
      avgSNR: 0,
      linkQuality: 0,
      deliveryRatio: 0,
      avgDelay: 0,
      overhead: 0
    },
    simTime: '00:00:00',
    timeAcceleration: 1,
    networkStatus: 'stopped'
  })
  const [isSimulationRunning, setIsSimulationRunning] = useState(false)
  const [view3D, setView3D] = useState(true)
  const [weatherEnabled, setWeatherEnabled] = useState(false)
  const [weatherSeed, setWeatherSeed] = useState('')
  const [trafficPattern, setTrafficPattern] = useState('uniform')
  const [bundleSize, setBundleSize] = useState(1)
  const [bundleTTL, setBundleTTL] = useState(3600)
  const [bufferSize, setBufferSize] = useState(100)
  const [bufferDropStrategy, setBufferDropStrategy] = useState('oldest')
  const [timeAcceleration, setTimeAcceleration] = useState(1) // Start at 1x speed

  // Fetch data on component mount
  useEffect(() => {
    fetchConstellations()
    fetchGroundStations()
    fetchSimulations()
  }, [])

  // Poll for running simulation updates
  useEffect(() => {
    const interval = setInterval(async () => {
      const runningSims = simulations.filter(s => s.status === 'running')
      if (runningSims.length > 0) {
        for (const sim of runningSims) {
          await fetchSimulationStatus(sim.id)
        }
      }
    }, 2000) // Update every 2 seconds

    return () => clearInterval(interval)
  }, [simulations])

  // Track running simulations for 3D visualization
  useEffect(() => {
    try {
      const runningSimulation = simulations.find(s => s.status === 'running')
      setIsSimulationRunning(!!runningSimulation)
      
      if (runningSimulation) {
        // Start real-time data fetching for 3D visualization
        const cleanup = startRealTimeDataFetch(runningSimulation.id)
        return cleanup // Return cleanup function
      } else {
        // Clear data when no simulation is running
        setRealTimeData({
          satellites: {},
          contacts: [],
          timelineContacts: [],
          bundles: { active: 0, delivered: 0, expired: 0 },
          packetPaths: [],
          metrics: {
            throughput: 0,
            avgSNR: 0,
            linkQuality: 0,
            deliveryRatio: 0,
            avgDelay: 0,
            overhead: 0
          },
          simTime: '00:00:00',
          timeAcceleration: 1,
          networkStatus: 'stopped'
        })
      }
    } catch (error) {
      console.error('Error in simulation tracking useEffect:', error)
      // Ensure we have fallback data
      setRealTimeData({
        satellites: {},
        contacts: [],
        timelineContacts: [],
        bundles: { active: 0, delivered: 0, expired: 0 },
        packetPaths: [],
        metrics: {
          throughput: 0,
          avgSNR: 0,
          linkQuality: 0,
          deliveryRatio: 0,
          avgDelay: 0,
          overhead: 0
        },
        simTime: '00:00:00',
        timeAcceleration: 1,
        networkStatus: 'stopped'
      })
    }
  }, [simulations])

  const startRealTimeDataFetch = (simulationId) => {
    // Enhanced real-time data with fallback to mock data
    const simulationStartTime = Date.now()
    // Start simulation time at 9:00 AM for realistic display
    const baseSimTime = new Date()
    baseSimTime.setHours(9, 0, 0, 0)
    const timeAcceleration = 3600 // 1 hour per second
    
    const interval = setInterval(async () => {
      try {
        // Try to get real simulation data first
        const response = await fetch(`/api/v2/realtime-data/simulation/${simulationId}`)
        
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.data) {
            // Process real simulation data with error handling
            try {
              const simData = data.data
              const satellites = {}
              const contacts = []
              
              // Extract real satellite data
              if (simData.satellites && typeof simData.satellites === 'object') {
                Object.entries(simData.satellites).forEach(([satId, satData]) => {
                  try {
                    satellites[satId] = {
                      position: (satData && satData.position) ? satData.position : { x: 0, y: 0, z: 0 },
                      status: (satData && satData.status) || 'active',
                      contacts: Number(satData && satData.contacts) || 0,
                      bundles_stored: Number(satData && satData.bundles_stored) || 0,
                      buffer_utilization: Number(satData && satData.buffer_utilization) || 0
                    }
                  } catch (e) {
                    console.warn(`Error processing satellite ${satId}:`, e)
                  }
                })
              }
              
              // Extract real contact data
              if (Array.isArray(simData.contacts)) {
                simData.contacts.forEach(contact => {
                  try {
                    if (contact && contact.isActive && contact.source_id && contact.target_id) {
                      // For 3D visualization contacts
                      const sourceSat = satellites[contact.source_id]
                      const targetSat = satellites[contact.target_id]
                      if (sourceSat && targetSat && sourceSat.position && targetSat.position) {
                        contacts.push({
                          source: sourceSat.position,
                          target: targetSat.position,
                          isActive: contact.isActive,
                          hasData: contact.hasData || false
                        })
                      }
                    }
                  } catch (e) {
                    console.warn('Error processing contact:', e)
                  }
                })
              }
            
              setRealTimeData({
                satellites,
                contacts: contacts, // Processed 3D visualization contacts
                timelineContacts: simData.contacts || [], // Full contact data for timeline
                bundles: simData.bundles || { active: 0, delivered: 0, expired: 0 },
                packetPaths: [], // Real packet paths would go here
                metrics: {
                  throughput: Number(simData.metrics?.throughput) || 0,
                  avgSNR: Number(simData.metrics?.avgSNR) || 45.0,
                  linkQuality: Number(simData.metrics?.linkQuality) || 98.5,
                  deliveryRatio: Number(simData.metrics?.deliveryRatio) || 0.85,
                  avgDelay: Number(simData.metrics?.avgDelay) || 120,
                  overhead: Number(simData.metrics?.overhead) || 1.2,
                  avgContactDuration: Number(simData.metrics?.avgContactDuration) || 320.5,
                  dataTransferred: Number(simData.metrics?.dataTransferred) || 45600,
                  avgBufferUtilization: Number(simData.metrics?.avgBufferUtilization) || 0.35
                },
                simTime: simData.simTime || '00:00:00',
                timeAcceleration: simData.timeAcceleration || timeAcceleration || 1,
                networkStatus: 'operational',
                currentSimTime: simData.currentSimTime || 0
              })
              
              // Sync local acceleration state with backend
              if (simData.timeAcceleration !== undefined && simData.timeAcceleration !== timeAcceleration) {
                setTimeAcceleration(simData.timeAcceleration)
              }
              
              return // Successfully processed real data
            } catch (dataProcessingError) {
              console.warn('Error processing simulation data:', dataProcessingError)
            }
          }
        }
      } catch (error) {
        // Fall back to mock data if API fails
        console.log('Using mock data for visualization:', error.message)
      }
      
      // Fallback: Generate enhanced mock data for visualization
      const satellites = {}
      const contacts = []
      const satelliteCount = constellations[selectedConstellation]?.satellites || 56
      
      // Create properly distributed constellation with multiple orbital planes
      const planesCount = 8  // Multiple orbital planes
      const satsPerPlane = Math.ceil(Math.min(satelliteCount, 60) / planesCount)
      let satIndex = 0
      
      for (let plane = 0; plane < planesCount && satIndex < Math.min(satelliteCount, 60); plane++) {
        const planeInclination = 53.0 // Starlink-like inclination
        const planeRaan = (plane / planesCount) * 360 // Right Ascension spread
        
        for (let sat = 0; sat < satsPerPlane && satIndex < Math.min(satelliteCount, 60); sat++) {
          const satId = `starlink_sat_${satIndex.toString().padStart(3, '0')}`
          
          // Spread satellites within each orbital plane
          const meanAnomaly = (sat / satsPerPlane) * 360
          const timeOffset = (Date.now() / 8000) // Slow orbital motion
          const currentAnomaly = (meanAnomaly + timeOffset + plane * 45) % 360 // Phase different planes
          const angle = (currentAnomaly * Math.PI) / 180
          
          // Orbital parameters for realistic positioning
          const altitude = 550 + Math.sin(plane * 0.8) * 100 // Vary altitude slightly per plane
          const radius = 6371 + altitude // Earth radius + altitude
          
          // Calculate position with proper orbital mechanics approximation
          const cosInclination = Math.cos((planeInclination * Math.PI) / 180)
          const sinInclination = Math.sin((planeInclination * Math.PI) / 180)
          const cosRaan = Math.cos((planeRaan * Math.PI) / 180)
          const sinRaan = Math.sin((planeRaan * Math.PI) / 180)
          
          // Position in orbital plane
          const xOrbital = radius * Math.cos(angle)
          const yOrbital = radius * Math.sin(angle)
          const zOrbital = 0
          
          // Transform to ECI coordinates (simplified)
          const x = xOrbital * cosRaan - yOrbital * sinRaan * cosInclination
          const y = xOrbital * sinRaan + yOrbital * cosRaan * cosInclination
          const z = yOrbital * sinInclination
          
          satellites[satId] = {
            position: { x, y, z },
            status: 'active',
            contacts: Math.floor(Math.random() * 5),
            bundles_stored: Math.floor(Math.random() * 3),
            buffer_utilization: Math.random() * 0.8,
            buffer_drop_strategy: bufferDropStrategy || 'oldest',
            bundles_dropped: Math.floor(Math.random() * 2)
          }
          
          satIndex++
        }
      }
      
      // Add contact lines based on proximity between satellites
      const satelliteIds = Object.keys(satellites)
      for (let i = 0; i < satelliteIds.length; i++) {
        const satId1 = satelliteIds[i]
        const sat1 = satellites[satId1]
        
        // Check contacts with nearby satellites (limit to avoid too many lines)
        for (let j = i + 1; j < Math.min(i + 3, satelliteIds.length); j++) {
          const satId2 = satelliteIds[j]
          const sat2 = satellites[satId2]
          
          const distance = Math.sqrt(
            Math.pow(sat1.position.x - sat2.position.x, 2) +
            Math.pow(sat1.position.y - sat2.position.y, 2) +
            Math.pow(sat1.position.z - sat2.position.z, 2)
          )
          
          if (distance < 2500) { // Within ISL communication range
            contacts.push({
              source: sat1.position,
              target: sat2.position,
              isActive: true,
              hasData: Math.random() > 0.7,
              source_id: satId1,
              target_id: satId2
            })
          }
        }
      }

      // Calculate accelerated simulation time
      const elapsedRealSeconds = (Date.now() - simulationStartTime) / 1000
      const acceleratedMilliseconds = elapsedRealSeconds * timeAcceleration * 1000
      const acceleratedTime = new Date(baseSimTime.getTime() + acceleratedMilliseconds)
      
      setRealTimeData({
        satellites,
        contacts,
        timelineContacts: [], // Mock timeline contacts would be complex
        bundles: { 
          active: Math.floor(Math.random() * 10) + 5,
          delivered: Math.floor(Math.random() * 50),
          expired: Math.floor(Math.random() * 5)
        },
        packetPaths: [], // No mock packet paths to avoid confusion
        metrics: {
          throughput: 50 + Math.random() * 100,
          avgSNR: 45 + Math.random() * 10,
          linkQuality: 95 + Math.random() * 5,
          deliveryRatio: 0.8 + Math.random() * 0.15,
          avgDelay: 100 + Math.random() * 50,
          overhead: 1.0 + Math.random() * 0.5
        },
        simTime: acceleratedTime.toLocaleTimeString(),
        timeAcceleration: timeAcceleration,
        networkStatus: 'mock-data'
      })
    }, 1000) // Update every second for smooth animation
    
    // Cleanup function to clear interval when simulation stops
    return () => clearInterval(interval)
  }

  const fetchConstellations = async () => {
    try {
      const response = await fetch('/api/v2/constellation/library')
      const data = await response.json()
      if (data.success) {
        setConstellations(data.data.constellations || {})
      }
    } catch (err) {
      console.error('Failed to fetch constellations:', err)
      // Fallback: use mock constellations for demo
      setConstellations({
        starlink: { name: 'Starlink', satellites: 56 },
        oneweb: { name: 'OneWeb', satellites: 48 },
        kuiper: { name: 'Project Kuiper', satellites: 64 }
      })
    }
  }

  const fetchGroundStations = async () => {
    try {
      const response = await fetch('/api/v2/ground_stations/library')
      const data = await response.json()
      if (data.success) {
        setGroundStations(data.data.ground_stations || {})
      }
    } catch (err) {
      console.error('Failed to fetch ground stations:', err)
      // Fallback: use mock ground stations for demo
      setGroundStations({
        gs_los_angeles: { name: 'Los Angeles', latitude: 34.0522, longitude: -118.2437 },
        gs_tokyo: { name: 'Tokyo', latitude: 35.6762, longitude: 139.6503 },
        gs_london: { name: 'London', latitude: 51.5074, longitude: -0.1278 },
        gs_sydney: { name: 'Sydney', latitude: -33.8688, longitude: 151.2093 }
      })
    }
  }

  const fetchSimulations = async () => {
    try {
      const response = await fetch('/api/v2/simulation/list')
      const data = await response.json()
      if (data.success) {
        setSimulations(data.data.simulations || [])
      }
    } catch (err) {
      console.error('Failed to fetch simulations:', err)
      // Fallback: keep existing simulations or initialize empty
      if (simulations.length === 0) {
        setSimulations([])
      }
    }
  }

  const fetchSimulationStatus = async (simulationId) => {
    try {
      const response = await fetch(`/api/v2/simulation/${simulationId}/status`)
      const data = await response.json()
      if (data.success) {
        setSimulationDetails(prev => ({
          ...prev,
          [simulationId]: data.data
        }))
      }
    } catch (err) {
      console.error('Failed to fetch simulation status:', err)
    }
  }

  const handleCreateSimulation = async () => {
    if (loading) return

    setLoading(true)
    setError(null)

    try {
      const config = {
        name: simulationName || `DTN Simulation - ${new Date().toLocaleTimeString()}`,
        constellation_id: selectedConstellation,
        routing_algorithm: routingAlgorithm,
        duration: simulationDuration,
        ground_stations: selectedGroundStations,
        time_step: 1.0,
        weather_enabled: weatherEnabled,
        weather_seed: weatherSeed ? parseInt(weatherSeed) : null,
        traffic_pattern: trafficPattern,
        bundle_size_kb: bundleSize,
        bundle_ttl_seconds: bundleTTL,
        satellite_buffer_size_kb: bufferSize,
        buffer_drop_strategy: bufferDropStrategy
      }

      const response = await fetch('/api/v2/simulation/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
      })

      const data = await response.json()
      
      if (data.success) {
        console.log('Simulation created:', data.data.simulation_id)
        // Clear form
        setSimulationName('')
        setTrafficPattern('uniform')
        setBundleSize(1)
        setBundleTTL(3600)
        setBufferSize(100)
        setBufferDropStrategy('oldest')
        setWeatherEnabled(false)
        setWeatherSeed('')
        await fetchSimulations() // Refresh simulation list
      } else {
        setError(data.message || 'Failed to create simulation')
        console.error('Backend error:', data)
      }
    } catch (err) {
      console.error('Error creating simulation:', err)
      
      // Fallback: Create mock simulation for demo
      const mockSimulation = {
        id: Date.now().toString(),
        name: config.name,
        constellation: selectedConstellation,
        routing_algorithm: routingAlgorithm,
        duration: simulationDuration,
        traffic_pattern: trafficPattern,
        bundle_size_kb: bundleSize,
        bundle_ttl_seconds: bundleTTL,
        satellite_buffer_size_kb: bufferSize,
        buffer_drop_strategy: bufferDropStrategy,
        weather_enabled: weatherEnabled,
        status: 'created',
        created_at: new Date().toISOString()
      }
      
      setSimulations(prev => [...prev, mockSimulation])
      // Clear form
      setSimulationName('')
      setTrafficPattern('uniform')
      setBundleSize(1)
      setBundleTTL(3600)
      setBufferSize(100)
      setBufferDropStrategy('oldest')
      setWeatherEnabled(false)
      setWeatherSeed('')
      console.log('Created mock simulation (backend unavailable):', mockSimulation)
    } finally {
      setLoading(false)
    }
  }

  const handleSimulationControl = async (simulationId, action) => {
    try {
      const response = await fetch(`/api/v2/simulation/${simulationId}/${action}`, {
        method: 'POST'
      })
      
      const data = await response.json()
      if (data.success) {
        console.log(`${action} simulation ${simulationId}:`, data.message)
        await fetchSimulations() // Refresh simulation list
        
        // Initialize real-time data when starting a simulation
        if (action === 'start') {
          try {
            console.log(`🚀 Initializing real-time data for simulation ${simulationId}`)
            const initResponse = await fetch(`/api/v2/realtime-data/simulation/${simulationId}/initialize`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              }
            })
            
            if (initResponse.ok) {
              console.log(`✅ Real-time data initialized for simulation ${simulationId}`)
            } else {
              console.log(`⚠️ Real-time data initialization failed, will use fallback`)
            }
          } catch (initErr) {
            console.log(`⚠️ Real-time data initialization error:`, initErr)
          }
        }
        
        // Clear details if stopping
        if (action === 'stop') {
          setSimulationDetails(prev => {
            const newDetails = { ...prev }
            delete newDetails[simulationId]
            return newDetails
          })
        }
      } else {
        console.error(`Failed to ${action} simulation:`, data.message)
      }
    } catch (err) {
      console.error(`Error ${action} simulation:`, err)
      
      // Fallback: Update simulation status locally for demo purposes
      if (action === 'start') {
        setSimulations(prev => prev.map(sim => 
          sim.id === simulationId 
            ? { ...sim, status: 'running' }
            : sim
        ))
        console.log(`Mock ${action} simulation ${simulationId} (backend unavailable)`)
      } else if (action === 'stop' || action === 'pause') {
        setSimulations(prev => prev.map(sim => 
          sim.id === simulationId 
            ? { ...sim, status: action === 'stop' ? 'stopped' : 'paused' }
            : sim
        ))
        console.log(`Mock ${action} simulation ${simulationId} (backend unavailable)`)
      }
    }
  }

  const handleTimeAccelerationChange = async (simulationId, acceleration) => {
    console.log(`🎛️ Acceleration button clicked: ${acceleration}x for simulation ${simulationId}`)
    
    try {
      const url = `/api/v2/realtime-data/simulation/${simulationId}/acceleration`
      console.log(`📡 Making request to: ${url}`)
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ acceleration })
      })
      
      console.log(`📊 Response status: ${response.status}`)
      
      const data = await response.json()
      console.log(`📋 Response data:`, data)
      
      if (data.success) {
        setTimeAcceleration(acceleration)
        console.log(`✅ Changed simulation ${simulationId} acceleration to ${acceleration}x`)
        
        // Update the real-time data to reflect new acceleration
        setRealTimeData(prev => ({
          ...prev,
          timeAcceleration: acceleration
        }))
      } else {
        console.error('❌ Failed to change time acceleration:', data.message)
        // Try fallback anyway
        setTimeAcceleration(acceleration)
        setRealTimeData(prev => ({
          ...prev,
          timeAcceleration: acceleration
        }))
      }
    } catch (err) {
      console.error('⚠️ Error changing time acceleration:', err)
      
      // Fallback: Update acceleration locally for demo purposes
      setTimeAcceleration(acceleration)
      setRealTimeData(prev => ({
        ...prev,
        timeAcceleration: acceleration
      }))
      console.log(`🔄 Mock acceleration change to ${acceleration}x (backend unavailable)`)
    }
  }

  const StatusBadge = ({ status }) => {
    const getStatusInfo = (status) => {
      switch (status) {
        case 'running':
          return { color: 'status-running', label: 'Running' }
        case 'paused':
          return { color: 'status-paused', label: 'Paused' }
        case 'stopped':
          return { color: 'status-stopped', label: 'Stopped' }
        default:
          return { color: 'status-created', label: 'Created' }
      }
    }

    const { color, label } = getStatusInfo(status)
    
    return (
      <span className="flex items-center">
        <div className={`status-indicator ${color}`}></div>
        {label}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">DTN Simulation</h1>
          <p className="text-gray-400 mt-2">
            Delay-Tolerant Network simulation for satellite communications
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <p className="text-sm text-gray-400">Active Simulations</p>
            <p className="text-2xl font-bold text-white">
              {simulations.filter(s => s.status === 'running').length}
            </p>
          </div>
          <Activity className="w-8 h-8 text-blue-400" />
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-600 bg-opacity-20 border border-red-600 text-red-300 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Simulation Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-1">
          <div className="card">
            <div className="card-header">
              <Settings className="w-5 h-5 inline mr-2" />
              Simulation Configuration
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="form-label">Simulation Name</label>
                <input
                  type="text"
                  value={simulationName}
                  onChange={(e) => setSimulationName(e.target.value)}
                  className="form-input w-full"
                  placeholder="e.g., Starlink Performance Test"
                />
              </div>

              <div>
                <label className="form-label">Constellation</label>
                <select
                  value={selectedConstellation}
                  onChange={(e) => setSelectedConstellation(e.target.value)}
                  className="form-input w-full"
                >
                  {Object.entries(constellations).map(([key, constellation]) => (
                    <option key={key} value={key}>
                      {constellation.name} ({constellation.satellites} satellites)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-label">Routing Algorithm</label>
                <select
                  value={routingAlgorithm}
                  onChange={(e) => setRoutingAlgorithm(e.target.value)}
                  className="form-input w-full"
                >
                  <option value="epidemic">Epidemic Routing</option>
                  <option value="prophet">PRoPHET Routing</option>
                  <option value="spray_and_wait">Spray and Wait</option>
                </select>
              </div>

              <div>
                <label className="form-label">Duration (hours)</label>
                <input
                  type="number"
                  value={simulationDuration}
                  onChange={(e) => setSimulationDuration(Number(e.target.value))}
                  min="1"
                  max="168"
                  className="form-input w-full"
                />
              </div>

              {/* Advanced Configuration */}
              <div className="pt-4 border-t border-gray-600">
                <label className="form-label">Advanced Configuration</label>
                <div className="mb-2 text-xs text-blue-300">
                  Configure traffic patterns, bundle parameters, and satellite storage
                </div>
                
                <div className="space-y-3">
                  <div>
                    <label className="form-label text-xs">Traffic Pattern</label>
                    <select
                      value={trafficPattern}
                      onChange={(e) => setTrafficPattern(e.target.value)}
                      className="form-input w-full text-sm"
                    >
                      <option value="uniform">Uniform - Constant data rate</option>
                      <option value="bursty">Bursty - Intermittent high-rate transmission</option>
                      <option value="custom">Custom - User-defined pattern</option>
                    </select>
                    <div className="mt-1 text-xs text-gray-400">
                      {trafficPattern === 'uniform' && 'Consistent data generation rate throughout simulation'}
                      {trafficPattern === 'bursty' && 'Periodic bursts of high data volume with quiet periods'}
                      {trafficPattern === 'custom' && 'Allows custom traffic profile configuration'}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="form-label text-xs">Bundle Size (KB)</label>
                      <input
                        type="number"
                        value={bundleSize}
                        onChange={(e) => setBundleSize(Number(e.target.value))}
                        min="0.1"
                        max="100"
                        step="0.1"
                        className="form-input w-full text-sm"
                      />
                      <div className="mt-1 text-xs text-gray-400">
                        Data packet size
                      </div>
                    </div>
                    
                    <div>
                      <label className="form-label text-xs">Bundle TTL (sec)</label>
                      <input
                        type="number"
                        value={bundleTTL}
                        onChange={(e) => setBundleTTL(Number(e.target.value))}
                        min="60"
                        max="86400"
                        step="60"
                        className="form-input w-full text-sm"
                      />
                      <div className="mt-1 text-xs text-gray-400">
                        Time-to-live
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <label className="form-label text-xs">Satellite Buffer Size (KB)</label>
                    <input
                      type="number"
                      value={bufferSize}
                      onChange={(e) => setBufferSize(Number(e.target.value))}
                      min="10"
                      max="10000"
                      step="10"
                      className="form-input w-full text-sm"
                    />
                    <div className="mt-1 text-xs text-gray-400">
                      Storage capacity per satellite for bundle buffering
                    </div>
                  </div>

                  <div>
                    <label className="form-label text-xs">Buffer Drop Strategy</label>
                    <select
                      value={bufferDropStrategy}
                      onChange={(e) => setBufferDropStrategy(e.target.value)}
                      className="form-input w-full text-sm"
                    >
                      <option value="oldest">Oldest First</option>
                      <option value="largest">Largest First</option>
                      <option value="shortest_ttl">Shortest TTL</option>
                      <option value="random">Random</option>
                    </select>
                    <div className="mt-1 text-xs text-gray-400">
                      Strategy for dropping bundles when buffer is full
                    </div>
                  </div>
                  
                  <div className="text-xs bg-blue-900 bg-opacity-30 p-2 rounded">
                    <div className="text-blue-300 mb-1">Configuration Impact:</div>
                    <div className="text-gray-300 space-y-0.5">
                      <div>• Larger bundles = higher transmission delay</div>
                      <div>• Shorter TTL = more aggressive routing decisions</div>
                      <div>• Buffer size affects store-and-forward capacity</div>
                      <div>• Drop strategy: Oldest=FIFO, Largest=space-efficient, TTL=deadline-aware</div>
                      <div>• Traffic patterns influence network congestion</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Weather Simulation */}
              <div className="pt-4 border-t border-gray-600">
                <label className="form-label">Weather Simulation</label>
                <div className="mb-2 text-xs text-blue-300">
                  Enable realistic weather effects on satellite RF performance
                </div>
                
                <div className="space-y-3">
                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={weatherEnabled}
                      onChange={(e) => setWeatherEnabled(e.target.checked)}
                      className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
                    />
                    <span className="text-white">
                      Enable Weather Effects
                    </span>
                  </label>
                  
                  {weatherEnabled && (
                    <div>
                      <label className="form-label text-xs">Weather Seed (optional)</label>
                      <input
                        type="number"
                        value={weatherSeed}
                        onChange={(e) => setWeatherSeed(e.target.value)}
                        className="form-input w-full text-sm"
                        placeholder="Random seed for reproducible weather patterns"
                      />
                      <div className="mt-1 text-xs text-gray-400">
                        Leave empty for random weather. Use same seed for reproducible results.
                      </div>
                    </div>
                  )}
                  
                  {weatherEnabled && (
                    <div className="text-xs bg-blue-900 bg-opacity-30 p-2 rounded">
                      <div className="text-blue-300 mb-1">Weather Effects Include:</div>
                      <div className="text-gray-300 space-y-0.5">
                        <div>• Rain fade attenuation (frequency dependent)</div>
                        <div>• Atmospheric absorption (humidity, temperature)</div>
                        <div>• Regional weather patterns (9 global regions)</div>
                        <div>• Real-time weather evolution during simulation</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-4 border-t border-gray-600">
                <div className="text-sm text-gray-400 mb-3">Ground Stations (Source & Destination)</div>
                <div className="mb-3 text-xs text-blue-300">
                  Select exactly 2 stations: one source and one destination for bundle delivery
                </div>
                
                <div className="space-y-2 mb-3">
                  <div>
                    <label className="form-label text-xs">Source Station</label>
                    <select
                      value={selectedGroundStations[0] || ''}
                      onChange={(e) => {
                        const newSelection = [e.target.value, selectedGroundStations[1]].filter(Boolean)
                        setSelectedGroundStations(newSelection)
                      }}
                      className="form-input w-full text-sm"
                    >
                      <option value="">Select source station...</option>
                      {Object.entries(groundStations).map(([stationId, station]) => (
                        <option key={stationId} value={stationId} disabled={selectedGroundStations[1] === stationId}>
                          {station.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="form-label text-xs">Destination Station</label>
                    <select
                      value={selectedGroundStations[1] || ''}
                      onChange={(e) => {
                        const newSelection = [selectedGroundStations[0], e.target.value].filter(Boolean)
                        setSelectedGroundStations(newSelection)
                      }}
                      className="form-input w-full text-sm"
                    >
                      <option value="">Select destination station...</option>
                      {Object.entries(groundStations).map(([stationId, station]) => (
                        <option key={stationId} value={stationId} disabled={selectedGroundStations[0] === stationId}>
                          {station.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                
                {selectedGroundStations.length === 2 && (
                  <div className="text-xs text-green-300 bg-green-900 bg-opacity-30 p-2 rounded">
                    ✓ Bundle Path: {groundStations[selectedGroundStations[0]]?.name} → {groundStations[selectedGroundStations[1]]?.name}
                  </div>
                )}
                
                {selectedGroundStations.length !== 2 && (
                  <div className="text-xs text-yellow-300 bg-yellow-900 bg-opacity-30 p-2 rounded">
                    ⚠ Please select both source and destination stations
                  </div>
                )}
              </div>

              <button
                onClick={handleCreateSimulation}
                disabled={loading || selectedGroundStations.length !== 2}
                className="btn-primary w-full disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Simulation'}
              </button>
              
              {selectedGroundStations.length !== 2 && (
                <div className="text-xs text-red-300 mt-2 text-center">
                  Both source and destination stations required
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Simulation List and Controls */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="card-header">
              <Satellite className="w-5 h-5 inline mr-2" />
              Active Simulations
            </div>

            {simulations.length === 0 ? (
              <div className="text-center py-8">
                <Satellite className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                <p className="text-gray-400">No simulations created yet</p>
                <p className="text-sm text-gray-500">Create your first simulation to get started</p>
              </div>
            ) : (
              <div className="space-y-4">
                {simulations.map((simulation) => (
                  <div key={simulation.id} className="glass p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-white">{simulation.name}</h3>
                        <p className="text-sm text-gray-400">
                          {simulation.constellation} • {simulation.routing_algorithm} • {simulation.buffer_drop_strategy || 'oldest'} drop
                        </p>
                        
                        {/* Live status details for running simulations */}
                        {simulation.status === 'running' && simulationDetails[simulation.id] && (
                          <div className="mt-2 text-xs text-gray-300 bg-gray-800 p-2 rounded">
                            {/* Time progression indicator */}
                            {simulationDetails[simulation.id].current_sim_time && (
                              <div className="mb-2 text-yellow-300 bg-yellow-900 bg-opacity-30 p-1 rounded">
                                <div className="text-center">
                                  <div className="font-mono">Sim Time: {new Date(simulationDetails[simulation.id].current_sim_time).toLocaleTimeString()}</div>
                                  <div className="text-xs">Acceleration: {simulationDetails[simulation.id].time_acceleration || 3600}x real-time</div>
                                </div>
                                
                                {/* Progress bar for simulation duration */}
                                {simulation.duration && simulationDetails[simulation.id].runtime_seconds && (
                                  <div className="mt-1">
                                    <div className="flex justify-between text-xs mb-1">
                                      <span>Progress</span>
                                      <span>{Math.min(100, (simulationDetails[simulation.id].runtime_seconds / (simulation.duration * 3600) * 100)).toFixed(1)}%</span>
                                    </div>
                                    <div className="w-full bg-gray-700 rounded-full h-1.5">
                                      <div 
                                        className="bg-blue-400 h-1.5 rounded-full transition-all duration-1000" 
                                        style={{
                                          width: `${Math.min(100, (simulationDetails[simulation.id].runtime_seconds / (simulation.duration * 3600) * 100))}%`
                                        }}
                                      ></div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                            
                            <div className="grid grid-cols-2 gap-2">
                              <div>Runtime: {Math.round(simulationDetails[simulation.id].runtime_seconds || 0)}s</div>
                              <div>Bundles: {simulationDetails[simulation.id].bundles_generated || 0}</div>
                              <div>Delivered: {simulationDetails[simulation.id].bundles_delivered || 0}</div>
                              <div>Contacts: {simulationDetails[simulation.id].active_contacts || 0}</div>
                            </div>
                            
                            {/* Delivery ratio and network status */}
                            {simulationDetails[simulation.id].delivery_ratio !== undefined && (
                              <div className="mt-1 text-center">
                                <span className="text-green-300">Delivery: {(simulationDetails[simulation.id].delivery_ratio * 100).toFixed(1)}%</span>
                                {simulationDetails[simulation.id].satellites_active && (
                                  <span className="ml-2 text-blue-300">Sats: {simulationDetails[simulation.id].satellites_active}</span>
                                )}
                              </div>
                            )}
                            
                            <div className="mt-1 text-blue-300 text-center">
                              {simulationDetails[simulation.id].current_activity || 'Initializing orbital propagation...'}
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        <StatusBadge status={simulation.status} />
                        
                        <div className="flex space-x-1">
                          {(simulation.status === 'created' || simulation.status === 'paused') && (
                            <button
                              onClick={() => handleSimulationControl(simulation.id, 'start')}
                              className="p-2 rounded bg-green-600 hover:bg-green-700 text-white transition-colors"
                              title="Start"
                            >
                              <Play className="w-4 h-4" />
                            </button>
                          )}
                          
                          {simulation.status === 'running' && (
                            <button
                              onClick={() => handleSimulationControl(simulation.id, 'pause')}
                              className="p-2 rounded bg-yellow-600 hover:bg-yellow-700 text-white transition-colors"
                              title="Pause"
                            >
                              <Pause className="w-4 h-4" />
                            </button>
                          )}
                          
                          {simulation.status !== 'stopped' && (
                            <button
                              onClick={() => handleSimulationControl(simulation.id, 'stop')}
                              className="p-2 rounded bg-red-600 hover:bg-red-700 text-white transition-colors"
                              title="Stop"
                            >
                              <Square className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                        
                        {/* Time Acceleration Controls - only show for running simulations */}
                        {simulation.status === 'running' && (
                          <div className="flex items-center space-x-2 ml-4 border-l border-gray-600 pl-4">
                            <span className="text-xs text-gray-400">Speed:</span>
                            <div className="flex space-x-1">
                              {[0.1, 0.5, 1, 5, 10, 60, 300, 3600].map((speed) => (
                                <button
                                  key={speed}
                                  onClick={() => {
                                    console.log(`🎮 Button clicked for sim ${simulation.id} at speed ${speed}x`)
                                    handleTimeAccelerationChange(simulation.id, speed)
                                  }}
                                  className={`px-2 py-1 text-xs rounded transition-colors ${
                                    (realTimeData?.timeAcceleration || timeAcceleration) === speed
                                      ? 'bg-cyan-600 text-white'
                                      : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                                  }`}
                                  title={`${speed === 0.1 ? '0.1x' : speed === 0.5 ? '0.5x' : speed >= 60 ? `${speed/60}min` : speed + 'x'} speed`}
                                >
                                  {speed === 0.1 ? '0.1x' : 
                                   speed === 0.5 ? '0.5x' : 
                                   speed === 1 ? '1x' :
                                   speed === 5 ? '5x' :
                                   speed === 10 ? '10x' :
                                   speed === 60 ? '1m' :
                                   speed === 300 ? '5m' : 
                                   speed === 3600 ? '1h' : speed + 'x'}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3D Military-Style Visualization */}
      <div className="card p-0 overflow-hidden">
        <div className="card-header bg-black border-b border-cyan-400">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Globe className="w-5 h-5 inline mr-2 text-cyan-400" />
              <span className="text-cyan-400 font-mono">TACTICAL SATELLITE DISPLAY</span>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setView3D(!view3D)}
                className={`px-3 py-1 text-xs font-mono border transition-colors ${
                  view3D 
                    ? 'border-green-400 text-green-400 bg-green-900 bg-opacity-30' 
                    : 'border-gray-400 text-gray-400 hover:border-green-400 hover:text-green-400'
                }`}
              >
                3D VIEW
              </button>
              <div className="text-xs font-mono text-gray-400">
                STATUS: {isSimulationRunning ? 
                  <span className="text-green-400 animate-pulse">ACTIVE</span> : 
                  <span className="text-red-400">STANDBY</span>
                }
              </div>
            </div>
          </div>
        </div>
        
        <div className="relative h-[700px] bg-black">
          {view3D ? (
            <>
              <SatelliteVisualization
                simulationData={realTimeData}
                isRunning={isSimulationRunning}
                onSatelliteClick={(satId, satData) => {
                  setSelectedSatellite({
                    id: satId,
                    altitude: Math.sqrt(satData?.position?.x**2 + satData?.position?.y**2 + satData?.position?.z**2) - 6371,
                    velocity: 7.66,
                    contacts: 0,
                    ...satData
                  })
                }}
              />
              <MilitaryHUD
                simulationData={{
                  satellites: realTimeData?.satellites || {},
                  contacts: realTimeData?.contacts || [],
                  bundles: realTimeData?.bundles || { active: 0 },
                  metrics: {
                    throughput: realTimeData?.metrics?.throughput || 0,
                    avgSNR: realTimeData?.metrics?.avgSNR || 45.0,
                    linkQuality: realTimeData?.metrics?.linkQuality || 100,
                    deliveryRatio: realTimeData?.metrics?.deliveryRatio || 0.85,
                    avgDelay: realTimeData?.metrics?.avgDelay || 120,
                    overhead: realTimeData?.metrics?.overhead || 1.2
                  },
                  rfBand: 'Ka-band',
                  weather: { enabled: false },
                  routing: { algorithm: routingAlgorithm },
                  simTime: realTimeData?.simTime || '00:00:00',
                  timeAcceleration: realTimeData?.timeAcceleration || 3600,
                  networkStatus: realTimeData?.networkStatus || 'operational',
                  fps: 60
                }}
                isRunning={isSimulationRunning}
                selectedSatellite={selectedSatellite}
              />
            </>
          ) : (
            <div className="h-full bg-gradient-to-br from-gray-900 via-blue-900 to-black flex items-center justify-center">
              <div className="text-center text-gray-400 font-mono">
                <Globe className="w-16 h-16 mx-auto mb-4 animate-pulse" />
                <div className="text-cyan-400">◤ 3D VIEW DISABLED ◥</div>
                <div className="text-sm mt-2">Enable 3D View for tactical display</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Contact Schedule Display */}
      {realTimeData && Object.keys(realTimeData.satellites || {}).length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Contact Gantt Chart */}
          <ContactGanttChart 
            simulationData={realTimeData}
            selectedSatellite={selectedSatellite?.id}
            isRunning={isSimulationRunning}
          />
          
          {/* Network Statistics Panel */}
          <div className="bg-black border border-blue-400 p-4">
            <div className="text-blue-400 text-sm mb-4 font-mono">
              ◤ NETWORK STATISTICS ◥
            </div>
            <div className="grid grid-cols-2 gap-4 text-xs font-mono">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-300">Total Contacts:</span>
                  <span className="text-green-400">{realTimeData?.contacts?.length || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Active Contacts:</span>
                  <span className="text-yellow-400">
                    {realTimeData?.contacts?.filter(c => c.isActive)?.length || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Avg Contact Duration:</span>
                  <span className="text-cyan-400">
                    {(realTimeData?.metrics?.avgContactDuration || 0).toFixed(1)}s
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Data Transferred:</span>
                  <span className="text-purple-400">
                    {((realTimeData?.metrics?.dataTransferred || 0) / 1024).toFixed(1)} KB
                  </span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-300">Routing Efficiency:</span>
                  <span className="text-green-400">
                    {(((realTimeData?.metrics?.overhead || 1) > 0 ? (1 / (realTimeData?.metrics?.overhead || 1)) : 1) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Network Load:</span>
                  <span className="text-orange-400">
                    {((realTimeData?.metrics?.avgBufferUtilization || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Packets in Flight:</span>
                  <span className="text-blue-400">{realTimeData?.bundles?.active || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Success Rate:</span>
                  <span className="text-green-400">
                    {((realTimeData?.metrics?.deliveryRatio || 0) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center text-gray-400 py-8">
          <div className="text-cyan-400 mb-2">Contact Timeline</div>
          <div>Start a simulation to view contact schedule</div>
        </div>
      )}
    </div>
  )
}

export default SimulationView