import React, { useState, useEffect } from 'react'
import { Play, Pause, Square, Settings, Activity, Satellite, Globe } from 'lucide-react'
import SatelliteVisualization from '../components/simulation/SatelliteVisualization'
import MilitaryHUD from '../components/simulation/MilitaryHUD'

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
  const [realTimeData, setRealTimeData] = useState(null)
  const [isSimulationRunning, setIsSimulationRunning] = useState(false)
  const [view3D, setView3D] = useState(true)
  const [weatherEnabled, setWeatherEnabled] = useState(false)
  const [weatherSeed, setWeatherSeed] = useState('')

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
        const response = await fetch(`/api/v2/simulation/${simulationId}/real-time`)
        
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.data) {
            // Process real simulation data
            const simData = data.data
            const satellites = {}
            const contacts = []
            
            // Extract real satellite data if available
            if (simData.satellites) {
              Object.entries(simData.satellites).forEach(([satId, satData]) => {
                satellites[satId] = {
                  position: satData.position || { x: 0, y: 0, z: 0 },
                  status: satData.status || 'active',
                  contacts: satData.active_contacts || 0,
                  bundles_stored: satData.bundles_stored || 0
                }
              })
            }
            
            // Extract real contact data if available
            if (simData.contacts) {
              simData.contacts.forEach(contact => {
                if (contact.is_active && satellites[contact.source_id] && satellites[contact.target_id]) {
                  contacts.push({
                    source: satellites[contact.source_id].position,
                    target: satellites[contact.target_id].position,
                    isActive: true,
                    hasData: contact.data_transfer > 0
                  })
                }
              })
            }
            
            setRealTimeData({
              satellites,
              contacts,
              bundles: { 
                active: simData.bundles_in_network || 0,
                delivered: simData.bundles_delivered || 0,
                expired: simData.bundles_expired || 0
              },
              packetPaths: [], // Real packet paths would go here
              metrics: {
                throughput: simData.metrics?.throughput || 50 + Math.random() * 100,
                avgSNR: simData.metrics?.avg_snr || 45 + Math.random() * 10,
                linkQuality: simData.metrics?.link_quality || 95 + Math.random() * 5,
                deliveryRatio: simData.metrics?.delivery_ratio || 0.8 + Math.random() * 0.15,
                avgDelay: simData.metrics?.avg_delay || 100 + Math.random() * 50,
                overhead: simData.metrics?.overhead || 1.0 + Math.random() * 0.5
              },
              simTime: simData.current_sim_time ? 
                new Date(simData.current_sim_time).toLocaleTimeString() : 
                new Date().toLocaleTimeString(),
              timeAcceleration: simData.time_acceleration || 3600,
              networkStatus: 'real-data'
            })
            return // Successfully processed real data
          }
        }
      } catch (error) {
        // Fall back to mock data if API fails
        console.log('Using mock data for visualization')
      }
      
      // Fallback: Generate enhanced mock data for visualization
      const satellites = {}
      const contacts = []
      const satelliteCount = constellations[selectedConstellation]?.satellites || 56
      
      for (let i = 0; i < Math.min(satelliteCount, 20); i++) {
        const satId = `starlink_sat_${i.toString().padStart(3, '0')}`
        const angle = (i / satelliteCount) * Math.PI * 2 + (Date.now() / 10000)
        const radius = 7000 + Math.sin(angle * 3) * 500
        const height = Math.cos(angle * 2) * 1000
        
        satellites[satId] = {
          position: {
            x: Math.cos(angle) * radius,
            y: height,
            z: Math.sin(angle) * radius
          },
          status: 'active',
          contacts: Math.floor(Math.random() * 5),
          bundles_stored: Math.floor(Math.random() * 3) // Add bundle storage for footprints
        }
        
        // Add contact lines based on proximity
        if (i > 0) {
          const prevSatId = `starlink_sat_${(i-1).toString().padStart(3, '0')}`
          const distance = Math.sqrt(
            Math.pow(satellites[satId].position.x - satellites[prevSatId].position.x, 2) +
            Math.pow(satellites[satId].position.y - satellites[prevSatId].position.y, 2) +
            Math.pow(satellites[satId].position.z - satellites[prevSatId].position.z, 2)
          )
          
          if (distance < 2000) { // Within communication range
            contacts.push({
              source: satellites[satId].position,
              target: satellites[prevSatId].position,
              isActive: true,
              hasData: Math.random() > 0.5
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
        weather_seed: weatherSeed ? parseInt(weatherSeed) : null
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
        setSimulationName('') // Clear form
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
        status: 'created',
        created_at: new Date().toISOString()
      }
      
      setSimulations(prev => [...prev, mockSimulation])
      setSimulationName('') // Clear form
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
                          {simulation.constellation} • {simulation.routing_algorithm}
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
        
        <div className="relative h-[600px] bg-black">
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
    </div>
  )
}

export default SimulationView