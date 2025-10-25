import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { Play, Pause, Square, Settings, Activity, Satellite, Globe } from 'lucide-react'

import { apiService } from '../services/api'

const SimulationView = () => {
  const [selectedConstellation, setSelectedConstellation] = useState('starlink')
  const [routingAlgorithm, setRoutingAlgorithm] = useState('epidemic')
  const [simulationDuration, setSimulationDuration] = useState(6)
  const [currentSimulation, setCurrentSimulation] = useState(null)
  
  const queryClient = useQueryClient()

  // Fetch available constellations
  const { data: constellations } = useQuery(
    'constellations',
    () => apiService.constellation.getLibrary(),
    {
      select: (data) => data.data?.constellations || {}
    }
  )

  // Fetch simulation list
  const { data: simulations, refetch: refetchSimulations } = useQuery(
    'simulations',
    () => apiService.simulation.list(),
    {
      select: (data) => data.data?.simulations || [],
      refetchInterval: 5000 // Refresh every 5 seconds
    }
  )

  // Create simulation mutation
  const createSimulationMutation = useMutation(
    (config) => apiService.simulation.create(config),
    {
      onSuccess: (data) => {
        setCurrentSimulation(data.data.simulation_id)
        refetchSimulations()
      }
    }
  )

  // Control simulation mutations
  const startMutation = useMutation(
    (id) => apiService.simulation.start(id),
    {
      onSuccess: () => refetchSimulations()
    }
  )

  const pauseMutation = useMutation(
    (id) => apiService.simulation.pause(id),
    {
      onSuccess: () => refetchSimulations()
    }
  )

  const stopMutation = useMutation(
    (id) => apiService.simulation.stop(id),
    {
      onSuccess: () => refetchSimulations()
    }
  )

  const handleCreateSimulation = () => {
    const config = {
      name: `DTN Simulation - ${new Date().toLocaleTimeString()}`,
      constellation_id: selectedConstellation,
      routing_algorithm: routingAlgorithm,
      duration: simulationDuration,
      ground_stations: ['gs_la', 'gs_tokyo'],
      time_step: 1.0
    }

    createSimulationMutation.mutate(config)
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
              {simulations?.filter(s => s.status === 'running').length || 0}
            </p>
          </div>
          <Activity className="w-8 h-8 text-blue-400" />
        </div>
      </div>

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
                <label className="form-label">Constellation</label>
                <select
                  value={selectedConstellation}
                  onChange={(e) => setSelectedConstellation(e.target.value)}
                  className="form-input w-full"
                >
                  {constellations && Object.entries(constellations).map(([key, constellation]) => (
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
                <div className="text-sm text-gray-400 mb-3">Ground Stations</div>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Globe className="w-4 h-4 text-blue-400" />
                    <span className="text-white">Los Angeles</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Globe className="w-4 h-4 text-blue-400" />
                    <span className="text-white">Tokyo</span>
                  </div>
                </div>
              </div>

              <button
                onClick={handleCreateSimulation}
                disabled={createSimulationMutation.isLoading}
                className="btn-primary w-full"
              >
                {createSimulationMutation.isLoading ? 'Creating...' : 'Create Simulation'}
              </button>
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

            {(!simulations || simulations.length === 0) ? (
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
                      <div>
                        <h3 className="font-semibold text-white">{simulation.name}</h3>
                        <p className="text-sm text-gray-400">
                          {simulation.constellation} • {simulation.routing_algorithm}
                        </p>
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        <StatusBadge status={simulation.status} />
                        
                        <div className="flex space-x-1">
                          {simulation.status === 'created' || simulation.status === 'paused' ? (
                            <button
                              onClick={() => startMutation.mutate(simulation.id)}
                              className="p-2 rounded bg-green-600 hover:bg-green-700 text-white transition-colors"
                              title="Start"
                            >
                              <Play className="w-4 h-4" />
                            </button>
                          ) : null}
                          
                          {simulation.status === 'running' ? (
                            <button
                              onClick={() => pauseMutation.mutate(simulation.id)}
                              className="p-2 rounded bg-yellow-600 hover:bg-yellow-700 text-white transition-colors"
                              title="Pause"
                            >
                              <Pause className="w-4 h-4" />
                            </button>
                          ) : null}
                          
                          {simulation.status !== 'stopped' ? (
                            <button
                              onClick={() => stopMutation.mutate(simulation.id)}
                              className="p-2 rounded bg-red-600 hover:bg-red-700 text-white transition-colors"
                              title="Stop"
                            >
                              <Square className="w-4 h-4" />
                            </button>
                          ) : null}
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