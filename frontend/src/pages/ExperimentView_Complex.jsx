import React, { useState } from 'react'
import { useQuery, useMutation } from 'react-query'
import { FlaskConical, Play, BarChart3, Download, Plus, Clock } from 'lucide-react'

import { apiService } from '../services/api'

const ExperimentView = () => {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    constellation_id: 'starlink',
    routing_algorithms: ['epidemic', 'prophet'],
    duration: 24,
    bundle_rate: 1.0,
    buffer_size: 10485760 // 10MB
  })

  // Fetch experiments
  const { data: experiments, refetch } = useQuery(
    'experiments',
    () => apiService.experiment.list(),
    {
      select: (data) => data.data?.experiments || [],
      refetchInterval: 10000
    }
  )

  // Fetch constellations for form
  const { data: constellations } = useQuery(
    'constellations',
    () => apiService.constellation.getLibrary(),
    {
      select: (data) => data.data?.constellations || {}
    }
  )

  // Create experiment mutation
  const createMutation = useMutation(
    (config) => apiService.experiment.create(config),
    {
      onSuccess: () => {
        setShowCreateForm(false)
        setFormData({
          name: '',
          description: '',
          constellation_id: 'starlink',
          routing_algorithms: ['epidemic', 'prophet'],
          duration: 24,
          bundle_rate: 1.0,
          buffer_size: 10485760
        })
        refetch()
      }
    }
  )

  const handleSubmit = (e) => {
    e.preventDefault()
    createMutation.mutate(formData)
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

  const formatDuration = (hours) => {
    if (hours < 24) return `${hours}h`
    const days = Math.floor(hours / 24)
    const remainingHours = hours % 24
    return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days}d`
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
                  {constellations && Object.entries(constellations).map(([key, constellation]) => (
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
                  disabled={createMutation.isLoading || formData.routing_algorithms.length === 0}
                  className="btn-primary flex-1"
                >
                  {createMutation.isLoading ? 'Creating...' : 'Create Experiment'}
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

        {(!experiments || experiments.length === 0) ? (
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
                    {experiment.status === 'completed' && (
                      <>
                        <button className="p-2 rounded bg-blue-600 hover:bg-blue-700 text-white transition-colors">
                          <BarChart3 className="w-4 h-4" />
                        </button>
                        <button className="p-2 rounded bg-green-600 hover:bg-green-700 text-white transition-colors">
                          <Download className="w-4 h-4" />
                        </button>
                      </>
                    )}
                    {experiment.status === 'running' && (
                      <div className="flex items-center space-x-2 text-blue-400">
                        <Clock className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Running...</span>
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
            {experiments?.filter(e => e.status === 'completed').length || 0}
          </div>
          <div className="text-gray-400">Completed</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-blue-400">
            {experiments?.filter(e => e.status === 'running').length || 0}
          </div>
          <div className="text-gray-400">Running</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-gray-400">
            {experiments?.length || 0}
          </div>
          <div className="text-gray-400">Total</div>
        </div>
      </div>
    </div>
  )
}

export default ExperimentView