import React, { useState, useEffect } from 'react'
import { FlaskConical, Play, BarChart3, Download, Plus, Clock } from 'lucide-react'

const ExperimentView = () => {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [experiments, setExperiments] = useState([])
  const [constellations, setConstellations] = useState({})
  const [groundStations, setGroundStations] = useState({})
  const [loading, setLoading] = useState(false)
  const [runningExperiments, setRunningExperiments] = useState(new Set())
  const [selectedExperiment, setSelectedExperiment] = useState(null)
  const [experimentResults, setExperimentResults] = useState(null)
  const [showResults, setShowResults] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    constellation_id: 'starlink',
    routing_algorithms: ['epidemic', 'prophet'],
    duration: 24,
    bundle_rate: 1.0,
    buffer_size: 10485760, // 10MB
    ground_stations: ['gs_los_angeles', 'gs_tokyo']
  })

  useEffect(() => {
    fetchExperiments()
    fetchConstellations()
    fetchGroundStations()
  }, [])

  const fetchExperiments = async () => {
    try {
      const response = await fetch('/api/v2/experiment/list')
      const data = await response.json()
      if (data.success) {
        setExperiments(data.data.experiments || [])
      }
    } catch (err) {
      console.error('Failed to fetch experiments:', err)
    }
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch('/api/v2/experiment/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })

      const data = await response.json()
      if (data.success) {
        setShowCreateForm(false)
        setFormData({
          name: '',
          description: '',
          constellation_id: 'starlink',
          routing_algorithms: ['epidemic', 'prophet'],
          duration: 24,
          bundle_rate: 1.0,
          buffer_size: 10485760,
          ground_stations: ['gs_los_angeles', 'gs_tokyo']
        })
        await fetchExperiments()
      }
    } catch (err) {
      console.error('Error creating experiment:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAlgorithmToggle = (algorithm) => {
    const current = formData.routing_algorithms
    if (current.includes(algorithm)) {
      setFormData({
        ...formData,
        routing_algorithms: current.filter(a => a !== algorithm)
      })
    } else {
      setFormData({
        ...formData,
        routing_algorithms: [...current, algorithm]
      })
    }
  }

  const handleRunExperiment = async (experimentId) => {
    setRunningExperiments(prev => new Set([...prev, experimentId]))
    
    try {
      const response = await fetch(`/api/v2/experiment/${experimentId}/run`, {
        method: 'POST'
      })
      
      const data = await response.json()
      
      if (data.success) {
        console.log('Experiment completed:', data.data)
        await fetchExperiments() // Refresh experiment list
      } else {
        console.error('Experiment failed:', data.message)
      }
    } catch (err) {
      console.error('Error running experiment:', err)
    } finally {
      setRunningExperiments(prev => {
        const newSet = new Set(prev)
        newSet.delete(experimentId)
        return newSet
      })
    }
  }

  const handleViewResults = async (experimentId) => {
    try {
      const response = await fetch(`/api/v2/experiment/${experimentId}/results`)
      const data = await response.json()
      
      if (data.success) {
        setSelectedExperiment(experimentId)
        setExperimentResults(data.data)
        setShowResults(true)
      } else {
        console.error('Failed to get results:', data.message)
      }
    } catch (err) {
      console.error('Error fetching results:', err)
    }
  }

  const handleExportResults = async (experimentId) => {
    try {
      const response = await fetch(`/api/v2/experiment/${experimentId}/results`)
      const data = await response.json()
      
      if (data.success) {
        // Convert to CSV format
        const results = data.data.experiment.results
        const csvContent = generateResultsCSV(results)
        
        // Download CSV file
        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `experiment_${experimentId}_results.csv`
        a.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (err) {
      console.error('Error exporting results:', err)
    }
  }

  const generateResultsCSV = (results) => {
    const headers = [
      'Algorithm',
      'Delivery Ratio (%)',
      'Average Delay (minutes)', 
      'Network Overhead',
      'Average Hop Count',
      'Total Bundles',
      'Bundles Delivered',
      'Throughput (bundles/hour)'
    ]
    
    const rows = Object.entries(results).map(([algorithm, data]) => [
      algorithm,
      (data.delivery_ratio * 100).toFixed(1),
      (data.average_delay_seconds / 60).toFixed(1),
      data.network_overhead_ratio.toFixed(2),
      data.average_hop_count.toFixed(1),
      data.total_bundles_generated,
      data.bundles_delivered,
      data.throughput_bundles_per_hour.toFixed(1)
    ])
    
    return [headers, ...rows].map(row => row.join(',')).join('\n')
  }

  const getStatusBadge = (status) => {
    const colors = {
      created: 'bg-gray-600',
      running: 'bg-blue-600 animate-pulse',
      completed: 'bg-green-600',
      error: 'bg-red-600'
    }
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full text-white ${colors[status] || 'bg-gray-600'}`}>
        {status}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">DTN Experiments</h1>
          <p className="text-gray-400 mt-2">
            Compare routing algorithms and analyze network performance
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>New Experiment</span>
        </button>
      </div>

      {/* Create Experiment Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="card max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">Create New Experiment</h2>
              <button
                onClick={() => setShowCreateForm(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="form-label">Experiment Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="form-input w-full"
                  placeholder="e.g., Starlink Performance Comparison"
                  required
                />
              </div>

              <div>
                <label className="form-label">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="form-input w-full h-20 resize-none"
                  placeholder="Describe the experiment goals and methodology..."
                />
              </div>

              <div>
                <label className="form-label">Constellation</label>
                <select
                  value={formData.constellation_id}
                  onChange={(e) => setFormData({...formData, constellation_id: e.target.value})}
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
                <label className="form-label">Routing Algorithms to Compare</label>
                <div className="space-y-2">
                  {['epidemic', 'prophet', 'spray_and_wait'].map(algorithm => (
                    <label key={algorithm} className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={formData.routing_algorithms.includes(algorithm)}
                        onChange={() => handleAlgorithmToggle(algorithm)}
                        className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
                      />
                      <span className="text-white capitalize">
                        {algorithm.replace('_', ' ')} Routing
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="form-label">Ground Stations (Source & Destination)</label>
                <div className="mb-3 text-xs text-blue-300">
                  Select exactly 2 stations for DTN bundle routing experiments
                </div>
                
                <div className="space-y-2 mb-3">
                  <div>
                    <label className="form-label text-xs">Source Station</label>
                    <select
                      value={formData.ground_stations[0] || ''}
                      onChange={(e) => {
                        const newSelection = [e.target.value, formData.ground_stations[1]].filter(Boolean)
                        setFormData({...formData, ground_stations: newSelection})
                      }}
                      className="form-input w-full text-sm"
                    >
                      <option value="">Select source station...</option>
                      {Object.entries(groundStations).map(([stationId, station]) => (
                        <option key={stationId} value={stationId} disabled={formData.ground_stations[1] === stationId}>
                          {station.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="form-label text-xs">Destination Station</label>
                    <select
                      value={formData.ground_stations[1] || ''}
                      onChange={(e) => {
                        const newSelection = [formData.ground_stations[0], e.target.value].filter(Boolean)
                        setFormData({...formData, ground_stations: newSelection})
                      }}
                      className="form-input w-full text-sm"
                    >
                      <option value="">Select destination station...</option>
                      {Object.entries(groundStations).map(([stationId, station]) => (
                        <option key={stationId} value={stationId} disabled={formData.ground_stations[0] === stationId}>
                          {station.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                
                {formData.ground_stations.length === 2 && (
                  <div className="text-xs text-green-300 bg-green-900 bg-opacity-30 p-2 rounded">
                    ✓ Experiment Path: {groundStations[formData.ground_stations[0]]?.name} → {groundStations[formData.ground_stations[1]]?.name}
                  </div>
                )}
                
                {formData.ground_stations.length !== 2 && (
                  <div className="text-xs text-yellow-300 bg-yellow-900 bg-opacity-30 p-2 rounded">
                    ⚠ Please select both source and destination stations for DTN routing
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="form-label">Duration (hours)</label>
                  <input
                    type="number"
                    value={formData.duration}
                    onChange={(e) => setFormData({...formData, duration: Number(e.target.value)})}
                    className="form-input w-full"
                    min="1"
                    max="168"
                  />
                </div>

                <div>
                  <label className="form-label">Bundle Rate (bundles/sec)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.bundle_rate}
                    onChange={(e) => setFormData({...formData, bundle_rate: Number(e.target.value)})}
                    className="form-input w-full"
                    min="0.1"
                    max="10"
                  />
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="submit"
                  disabled={loading || formData.routing_algorithms.length === 0 || formData.ground_stations.length !== 2}
                  className="btn-primary flex-1 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Experiment'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Experiments List */}
      <div className="card">
        <div className="card-header">
          <FlaskConical className="w-5 h-5 inline mr-2" />
          Experiment Results
        </div>

        {experiments.length === 0 ? (
          <div className="text-center py-8">
            <FlaskConical className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <p className="text-gray-400">No experiments created yet</p>
            <p className="text-sm text-gray-500">Create your first experiment to compare routing algorithms</p>
          </div>
        ) : (
          <div className="space-y-4">
            {experiments.map((experiment) => (
              <div key={experiment.id} className="glass p-4 rounded-lg">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-semibold text-white">{experiment.name}</h3>
                      {getStatusBadge(experiment.status)}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-400">
                      <div>
                        <span className="text-gray-500">Constellation:</span>
                        <br />
                        <span className="text-white">{experiment.constellation}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Algorithms:</span>
                        <br />
                        <span className="text-white">
                          {experiment.algorithms?.join(', ') || 'N/A'}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Created:</span>
                        <br />
                        <span className="text-white">
                          {new Date(experiment.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    {experiment.status === 'created' && (
                      <button 
                        onClick={() => handleRunExperiment(experiment.id)}
                        disabled={runningExperiments.has(experiment.id)}
                        className="p-2 rounded bg-green-600 hover:bg-green-700 text-white transition-colors disabled:opacity-50"
                        title="Run Experiment"
                      >
                        {runningExperiments.has(experiment.id) ? (
                          <Clock className="w-4 h-4 animate-spin" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </button>
                    )}
                    
                    {experiment.status === 'completed' && (
                      <>
                        <button 
                          onClick={() => handleViewResults(experiment.id)}
                          className="p-2 rounded bg-blue-600 hover:bg-blue-700 text-white transition-colors"
                          title="View Results"
                        >
                          <BarChart3 className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleExportResults(experiment.id)}
                          className="p-2 rounded bg-green-600 hover:bg-green-700 text-white transition-colors"
                          title="Export Data"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      </>
                    )}
                    
                    {(experiment.status === 'running' || runningExperiments.has(experiment.id)) && (
                      <div className="flex items-center space-x-2 text-blue-400">
                        <Clock className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Running...</span>
                      </div>
                    )}
                    
                    {experiment.status === 'error' && (
                      <div className="flex items-center space-x-2 text-red-400">
                        <span className="text-sm">Failed</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card text-center">
          <div className="text-2xl font-bold text-white">
            {experiments.filter(e => e.status === 'completed').length}
          </div>
          <div className="text-gray-400">Completed</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-blue-400">
            {experiments.filter(e => e.status === 'running').length}
          </div>
          <div className="text-gray-400">Running</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-gray-400">
            {experiments.length}
          </div>
          <div className="text-gray-400">Total</div>
        </div>
      </div>

      {/* Results Modal */}
      {showResults && experimentResults && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="card max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">Experiment Results</h2>
              <button
                onClick={() => setShowResults(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {/* Experiment Info */}
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-semibold text-white mb-2">{experimentResults.experiment.name}</h3>
                <p className="text-gray-400 text-sm">{experimentResults.experiment.description}</p>
                <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                  <div>
                    <span className="text-gray-400">Constellation:</span>
                    <div className="text-white">{experimentResults.experiment.constellation}</div>
                  </div>
                  <div>
                    <span className="text-gray-400">Duration:</span>
                    <div className="text-white">{experimentResults.experiment.duration} hours</div>
                  </div>
                  <div>
                    <span className="text-gray-400">Bundle Rate:</span>
                    <div className="text-white">{experimentResults.experiment.bundle_rate} bundles/sec</div>
                  </div>
                </div>
              </div>

              {/* Results Comparison */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {Object.entries(experimentResults.experiment.results).map(([algorithm, data]) => (
                  <div key={algorithm} className="bg-gray-800 p-4 rounded-lg">
                    <h4 className="text-lg font-semibold text-white mb-3 capitalize">
                      {algorithm.replace('_', ' ')} Routing
                    </h4>
                    
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Delivery Ratio:</span>
                        <span className="text-white font-medium">
                          {(data.delivery_ratio * 100).toFixed(1)}%
                        </span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-gray-400">Avg Delay:</span>
                        <span className="text-white">
                          {(data.average_delay_seconds / 60).toFixed(1)} min
                        </span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-gray-400">Network Overhead:</span>
                        <span className="text-white">
                          {data.network_overhead_ratio.toFixed(1)}x
                        </span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-gray-400">Hop Count:</span>
                        <span className="text-white">
                          {data.average_hop_count.toFixed(1)}
                        </span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-gray-400">Bundles Generated:</span>
                        <span className="text-white">
                          {data.total_bundles_generated.toLocaleString()}
                        </span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-gray-400">Bundles Delivered:</span>
                        <span className="text-white">
                          {data.bundles_delivered.toLocaleString()}
                        </span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-gray-400">Throughput:</span>
                        <span className="text-white">
                          {data.throughput_bundles_per_hour.toFixed(1)} bundles/hr
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Performance Summary */}
              {experimentResults.comparison && (
                <div className="bg-gray-800 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-white mb-4">Performance Summary</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div className="bg-green-900 bg-opacity-30 p-3 rounded">
                      <div className="text-green-300 font-medium">Best Delivery Ratio</div>
                      <div className="text-white text-lg">
                        {experimentResults.comparison.best_delivery_ratio?.algorithm.replace('_', ' ')}
                      </div>
                      <div className="text-gray-300">
                        {(experimentResults.comparison.best_delivery_ratio?.value * 100).toFixed(1)}%
                      </div>
                    </div>
                    
                    <div className="bg-blue-900 bg-opacity-30 p-3 rounded">
                      <div className="text-blue-300 font-medium">Lowest Delay</div>
                      <div className="text-white text-lg">
                        {experimentResults.comparison.lowest_delay?.algorithm.replace('_', ' ')}
                      </div>
                      <div className="text-gray-300">
                        {(experimentResults.comparison.lowest_delay?.value / 60).toFixed(1)} min
                      </div>
                    </div>
                    
                    <div className="bg-purple-900 bg-opacity-30 p-3 rounded">
                      <div className="text-purple-300 font-medium">Most Efficient</div>
                      <div className="text-white text-lg">
                        {experimentResults.comparison.most_efficient?.algorithm.replace('_', ' ')}
                      </div>
                      <div className="text-gray-300">
                        {experimentResults.comparison.most_efficient?.value.toFixed(1)}x overhead
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex space-x-3">
                <button
                  onClick={() => handleExportResults(selectedExperiment)}
                  className="btn-primary flex items-center space-x-2"
                >
                  <Download className="w-4 h-4" />
                  <span>Export CSV</span>
                </button>
                <button
                  onClick={() => setShowResults(false)}
                  className="btn-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ExperimentView