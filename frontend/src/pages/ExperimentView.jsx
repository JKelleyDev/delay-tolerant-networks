import React, { useState, useEffect } from 'react'
import { FlaskConical, Play, BarChart3, Download, Plus, Clock } from 'lucide-react'

const ExperimentView = () => {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [experiments, setExperiments] = useState([])
  const [constellations, setConstellations] = useState({})
  const [groundStations, setGroundStations] = useState({})
  const [rfBands, setRfBands] = useState({})
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
    ttl_minutes: 60, // Bundle TTL in minutes
    ground_stations: ['gs_los_angeles', 'gs_tokyo'],
    rf_band: 'ka-band', // Default to Ka-band (modern broadband)
    weather_enabled: false, // Weather simulation
    weather_seed: null // Random seed for weather
  })
  const [experimentPresets, setExperimentPresets] = useState({})
  const [showPresets, setShowPresets] = useState(false)

  useEffect(() => {
    fetchExperiments()
    fetchConstellations()
    fetchGroundStations()
    fetchRfBands()
    fetchExperimentPresets()
  }, [])

  const fetchExperimentPresets = async () => {
    try {
      const response = await fetch('/api/v2/experiment/presets')
      const data = await response.json()
      if (data.success) {
        setExperimentPresets(data.data.presets || {})
      }
    } catch (err) {
      console.error('Failed to fetch experiment presets:', err)
    }
  }

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

  const fetchRfBands = async () => {
    try {
      const response = await fetch('/api/v2/rf_bands/library')
      const data = await response.json()
      if (data.success) {
        setRfBands(data.data.rf_bands || {})
      }
    } catch (err) {
      console.error('Failed to fetch RF bands:', err)
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
          ground_stations: ['gs_los_angeles', 'gs_tokyo'],
          rf_band: 'ka-band',
          weather_enabled: false,
          weather_seed: null
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
      // Network Layer
      'Delivery Ratio (%)',
      'Average Delay (minutes)', 
      'Network Overhead',
      'Routing Efficiency',
      'Total Bundles',
      'Bundles Delivered',
      // Physical Layer
      'RF Throughput (Mbps)',
      'Average SNR (dB)',
      'Average Data Rate (Mbps)',
      'Link Availability (%)',
      'Link Margin (dB)',
      'Data Transmitted (MB)',
      'RF Limited Contacts',
      // Weather Effects
      'Weather Affected Contacts',
      'Average Weather Attenuation (dB)',
      // Cross-Layer
      'Cross-Layer Performance Score'
    ]
    
    const rows = Object.entries(results).map(([algorithm, data]) => [
      algorithm,
      // Network Layer
      (data.delivery_ratio * 100).toFixed(1),
      (data.average_delay_seconds / 60).toFixed(1),
      data.network_overhead_ratio.toFixed(2),
      data.network_layer_routing_efficiency ? data.network_layer_routing_efficiency.toFixed(3) : 'N/A',
      data.total_bundles_generated,
      data.bundles_delivered,
      // Physical Layer
      data.rf_throughput_mbps ? data.rf_throughput_mbps.toFixed(2) : '0.00',
      data.average_snr_db ? data.average_snr_db.toFixed(1) : '0.0',
      data.average_data_rate_mbps ? data.average_data_rate_mbps.toFixed(1) : '0.0',
      data.rf_link_availability_percent ? data.rf_link_availability_percent.toFixed(1) : '0.0',
      data.average_link_margin_db ? data.average_link_margin_db.toFixed(1) : '0.0',
      data.total_data_transmitted_mb ? data.total_data_transmitted_mb.toFixed(1) : '0.0',
      data.rf_limited_contacts || 0,
      // Weather Effects
      data.weather_affected_contacts || 0,
      data.average_weather_attenuation_db ? data.average_weather_attenuation_db.toFixed(1) : '0.0',
      // Cross-Layer
      data.cross_layer_performance_score ? data.cross_layer_performance_score.toFixed(3) : '0.000'
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
                <label className="form-label">RF Frequency Band</label>
                <div className="mb-2 text-xs text-blue-300">
                  Choose the satellite communication frequency band for realistic RF analysis
                </div>
                <select
                  value={formData.rf_band}
                  onChange={(e) => setFormData({...formData, rf_band: e.target.value})}
                  className="form-input w-full"
                >
                  {Object.entries(rfBands).map(([key, band]) => (
                    <option key={key} value={key}>
                      {band.name} ({band.frequency_ghz.toFixed(1)} GHz, {band.bandwidth_mhz.toFixed(0)} MHz)
                    </option>
                  ))}
                </select>
                
                {formData.rf_band && rfBands[formData.rf_band] && (
                  <div className="mt-2 text-xs bg-gray-800 p-2 rounded">
                    <div className="text-gray-300 mb-1">RF Specifications:</div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-gray-400">Frequency:</span>
                        <span className="text-white ml-1">{rfBands[formData.rf_band].frequency_ghz.toFixed(1)} GHz</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Bandwidth:</span>
                        <span className="text-white ml-1">{rfBands[formData.rf_band].bandwidth_mhz.toFixed(0)} MHz</span>
                      </div>
                      <div>
                        <span className="text-gray-400">TX Power:</span>
                        <span className="text-white ml-1">{rfBands[formData.rf_band].tx_power_watts.toFixed(0)}W</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Required SNR:</span>
                        <span className="text-white ml-1">{rfBands[formData.rf_band].required_snr_db.toFixed(0)} dB</span>
                      </div>
                    </div>
                    <div className="mt-1">
                      <span className="text-gray-400">Applications:</span>
                      <span className="text-green-300 ml-1">{rfBands[formData.rf_band].typical_applications?.join(', ')}</span>
                    </div>
                  </div>
                )}
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

              <div>
                <label className="form-label">Weather Simulation</label>
                <div className="mb-2 text-xs text-blue-300">
                  Enable realistic weather effects on satellite RF performance
                </div>
                
                <div className="space-y-3">
                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={formData.weather_enabled}
                      onChange={(e) => setFormData({...formData, weather_enabled: e.target.checked})}
                      className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
                    />
                    <span className="text-white">
                      Enable Weather Simulation
                    </span>
                  </label>
                  
                  {formData.weather_enabled && (
                    <div>
                      <label className="form-label text-xs">Weather Seed (optional)</label>
                      <input
                        type="number"
                        value={formData.weather_seed || ''}
                        onChange={(e) => setFormData({...formData, weather_seed: e.target.value ? parseInt(e.target.value) : null})}
                        className="form-input w-full text-sm"
                        placeholder="Random seed for reproducible weather patterns"
                      />
                      <div className="mt-1 text-xs text-gray-400">
                        Leave empty for random weather. Use same seed for reproducible results.
                      </div>
                    </div>
                  )}
                  
                  {formData.weather_enabled && (
                    <div className="text-xs bg-blue-900 bg-opacity-30 p-2 rounded">
                      <div className="text-blue-300 mb-1">Weather Effects Include:</div>
                      <div className="text-gray-300 space-y-0.5">
                        <div>• Rain fade attenuation (frequency dependent)</div>
                        <div>• Atmospheric absorption (humidity, temperature)</div>
                        <div>• Cloud cover effects on RF links</div>
                        <div>• Regional weather patterns (9 global regions)</div>
                        <div>• Real-time weather evolution during experiment</div>
                      </div>
                    </div>
                  )}
                </div>
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

              {/* E2/E3 Experiment Parameters */}
              <div className="mt-4 p-3 bg-gray-800 rounded-lg">
                <h4 className="text-sm font-medium text-blue-300 mb-3">DTN Parameters (for E2/E3 experiments)</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Buffer Size</label>
                    <select
                      value={formData.buffer_size}
                      onChange={(e) => setFormData({...formData, buffer_size: Number(e.target.value)})}
                      className="form-input w-full"
                    >
                      <option value={5242880}>5 MB (E2 test)</option>
                      <option value={10485760}>10 MB (default)</option>
                      <option value={20971520}>20 MB (E2 test)</option>
                      <option value={52428800}>50 MB</option>
                      <option value={83886080}>80 MB (E2 test)</option>
                    </select>
                    <p className="text-xs text-gray-400 mt-1">Per-satellite bundle buffer size</p>
                  </div>

                  <div>
                    <label className="form-label">Bundle TTL</label>
                    <select
                      value={formData.ttl_minutes}
                      onChange={(e) => setFormData({...formData, ttl_minutes: Number(e.target.value)})}
                      className="form-input w-full"
                    >
                      <option value={30}>30 minutes (E3 test)</option>
                      <option value={60}>1 hour (default)</option>
                      <option value={120}>2 hours (E3 test)</option>
                      <option value={240}>4 hours</option>
                      <option value={480}>8 hours (E3 test)</option>
                    </select>
                    <p className="text-xs text-gray-400 mt-1">Time-to-live for bundles in the network</p>
                  </div>
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
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 text-sm">
                  <div>
                    <span className="text-gray-400">Constellation:</span>
                    <div className="text-white">{experimentResults.experiment.constellation}</div>
                  </div>
                  <div>
                    <span className="text-gray-400">RF Band:</span>
                    <div className="text-white">
                      {experimentResults.experiment.rf_band ? 
                        rfBands[experimentResults.experiment.rf_band]?.name || experimentResults.experiment.rf_band 
                        : 'Ka-band'}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400">Weather:</span>
                    <div className="text-white">
                      {experimentResults.experiment.weather_enabled ? 
                        `Enabled${experimentResults.experiment.weather_seed ? ` (Seed: ${experimentResults.experiment.weather_seed})` : ''}` 
                        : 'Disabled'}
                    </div>
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
                
                {/* RF Band Details */}
                {experimentResults.experiment.rf_band && rfBands[experimentResults.experiment.rf_band] && (
                  <div className="mt-3 p-2 bg-gray-700 rounded text-xs">
                    <span className="text-blue-300">📡 RF Specifications: </span>
                    <span className="text-gray-300">
                      {rfBands[experimentResults.experiment.rf_band].frequency_ghz.toFixed(1)} GHz, 
                      {rfBands[experimentResults.experiment.rf_band].bandwidth_mhz.toFixed(0)} MHz bandwidth, 
                      {rfBands[experimentResults.experiment.rf_band].tx_power_watts.toFixed(0)}W TX power
                    </span>
                  </div>
                )}
              </div>

              {/* Results Comparison */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {Object.entries(experimentResults.experiment.results).map(([algorithm, data]) => (
                  <div key={algorithm} className="bg-gray-800 p-4 rounded-lg">
                    <h4 className="text-lg font-semibold text-white mb-3 capitalize">
                      {algorithm.replace('_', ' ')} Routing
                    </h4>
                    
                    {/* Network Layer Performance */}
                    <div className="mb-4">
                      <h5 className="text-sm font-medium text-gray-300 mb-2 border-b border-gray-600 pb-1">
                        🌐 Network Layer (DTN Routing)
                      </h5>
                      <div className="space-y-2 text-sm">
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
                          <span className="text-gray-400">Routing Efficiency:</span>
                          <span className="text-white">
                            {data.network_layer_routing_efficiency ? data.network_layer_routing_efficiency.toFixed(3) : 'N/A'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Physical Layer Performance */}
                    <div className="mb-4">
                      <h5 className="text-sm font-medium text-gray-300 mb-2 border-b border-gray-600 pb-1">
                        📡 Physical Layer (RF Performance)
                      </h5>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-400">RF Throughput:</span>
                          <span className="text-white font-medium">
                            {data.rf_throughput_mbps ? data.rf_throughput_mbps.toFixed(2) : '0.00'} Mbps
                          </span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-gray-400">Average SNR:</span>
                          <span className="text-white">
                            {data.average_snr_db ? data.average_snr_db.toFixed(1) : '0.0'} dB
                          </span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-gray-400">Data Rate:</span>
                          <span className="text-white">
                            {data.average_data_rate_mbps ? data.average_data_rate_mbps.toFixed(1) : '0.0'} Mbps
                          </span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-gray-400">Link Availability:</span>
                          <span className="text-white">
                            {data.rf_link_availability_percent ? data.rf_link_availability_percent.toFixed(1) : '0.0'}%
                          </span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-gray-400">Link Margin:</span>
                          <span className="text-white">
                            {data.average_link_margin_db ? data.average_link_margin_db.toFixed(1) : '0.0'} dB
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Weather Effects */}
                    {experimentResults.experiment.weather_enabled && (
                      <div className="mb-4">
                        <h5 className="text-sm font-medium text-gray-300 mb-2 border-b border-gray-600 pb-1">
                          🌦️ Weather Effects
                        </h5>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-400">Weather Affected Contacts:</span>
                            <span className="text-white">
                              {data.weather_affected_contacts || 0}
                            </span>
                          </div>
                          
                          <div className="flex justify-between">
                            <span className="text-gray-400">Avg Weather Attenuation:</span>
                            <span className="text-white">
                              {data.average_weather_attenuation_db ? data.average_weather_attenuation_db.toFixed(1) : '0.0'} dB
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Cross-Layer Analysis */}
                    <div>
                      <h5 className="text-sm font-medium text-gray-300 mb-2 border-b border-gray-600 pb-1">
                        🔗 Cross-Layer Integration
                      </h5>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Data Transmitted:</span>
                          <span className="text-white">
                            {data.total_data_transmitted_mb ? data.total_data_transmitted_mb.toFixed(1) : '0.0'} MB
                          </span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-gray-400">RF Limited Contacts:</span>
                          <span className="text-white">
                            {data.rf_limited_contacts || 0}
                          </span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-gray-400">Performance Score:</span>
                          <span className="text-white font-medium">
                            {data.cross_layer_performance_score ? data.cross_layer_performance_score.toFixed(3) : '0.000'}
                          </span>
                        </div>
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