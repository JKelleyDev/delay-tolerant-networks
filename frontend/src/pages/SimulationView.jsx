import React, { useState, useEffect } from 'react'
import { Play, Pause, Square, Settings, Activity, Satellite, Globe } from 'lucide-react'

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

  const fetchConstellations = async () => {
    try {
      const response = await fetch('/api/v2/constellation/library')
      const data = await response.json()
      if (data.success) {
        setConstellations(data.data.constellations || {})
      }
    } catch (err) {
      console.error('Failed to fetch constellations:', err)
      setError('Failed to load constellations')
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
        time_step: 1.0
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
      setError('Network error creating simulation')
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
                            <div className="grid grid-cols-2 gap-2">
                              <div>Runtime: {simulationDetails[simulation.id].runtime_seconds}s</div>
                              <div>Bundles: {simulationDetails[simulation.id].bundles_generated || 0}</div>
                              <div>Delivered: {simulationDetails[simulation.id].bundles_delivered || 0}</div>
                              <div>Contacts: {simulationDetails[simulation.id].active_contacts || 0}</div>
                            </div>
                            <div className="mt-1 text-blue-300">
                              Activity: {simulationDetails[simulation.id].current_activity || 'Initializing...'}
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

      {/* 3D Visualization Placeholder */}
      <div className="card">
        <div className="card-header">
          <Globe className="w-5 h-5 inline mr-2" />
          3D Satellite Visualization
        </div>
        
        <div className="h-96 bg-gradient-to-br from-gray-800 to-blue-900 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <Globe className="w-16 h-16 text-blue-400 mx-auto mb-4 animate-pulse" />
            <h3 className="text-xl font-semibold text-white mb-2">3D Visualization</h3>
            <p className="text-gray-400">
              Real-time satellite tracking and communication visualization
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Three.js integration coming soon...
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SimulationView