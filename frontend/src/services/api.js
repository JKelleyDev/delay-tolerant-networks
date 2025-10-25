/**
 * API Service for DTN Simulator
 * 
 * Provides methods to interact with the FastAPI backend.
 */

import axios from 'axios'

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api/v2',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
api.interceptors.request.use((config) => {
  console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export const apiService = {
  // Health check
  async healthCheck() {
    const response = await api.get('/health')
    return response.data
  },

  // Root endpoint info
  async getInfo() {
    const response = await api.get('/')
    return response.data
  },

  // Simulation endpoints
  simulation: {
    async create(config) {
      const response = await api.post('/simulation/create', config)
      return response.data
    },

    async list() {
      const response = await api.get('/simulation/list')
      return response.data
    },

    async get(simulationId) {
      const response = await api.get(`/simulation/${simulationId}`)
      return response.data
    },

    async start(simulationId) {
      const response = await api.post(`/simulation/${simulationId}/start`)
      return response.data
    },

    async pause(simulationId) {
      const response = await api.post(`/simulation/${simulationId}/pause`)
      return response.data
    },

    async stop(simulationId) {
      const response = await api.post(`/simulation/${simulationId}/stop`)
      return response.data
    },

    async delete(simulationId) {
      const response = await api.delete(`/simulation/${simulationId}`)
      return response.data
    },

    async getStatus(simulationId) {
      const response = await api.get(`/simulation/${simulationId}/status`)
      return response.data
    },

    async getMetrics(simulationId) {
      const response = await api.get(`/simulation/${simulationId}/metrics`)
      return response.data
    },

    async getSatellites(simulationId) {
      const response = await api.get(`/simulation/${simulationId}/satellites`)
      return response.data
    },

    async getGroundStations(simulationId) {
      const response = await api.get(`/simulation/${simulationId}/ground_stations`)
      return response.data
    },
  },

  // Constellation endpoints
  constellation: {
    async getLibrary() {
      const response = await api.get('/constellation/library')
      return response.data
    },

    async get(constellationId) {
      const response = await api.get(`/constellation/${constellationId}`)
      return response.data
    },

    async upload(name, description, file) {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('description', description)
      formData.append('file', file)

      const response = await api.post('/constellation/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    },

    async getSatellites(constellationId, limit = null) {
      const params = limit ? { limit } : {}
      const response = await api.get(`/constellation/${constellationId}/satellites`, { params })
      return response.data
    },

    async delete(constellationId) {
      const response = await api.delete(`/constellation/${constellationId}`)
      return response.data
    },

    async generateTLE(constellationId) {
      const response = await api.get(`/constellation/${constellationId}/generate`)
      return response.data
    },
  },

  // Experiment endpoints
  experiment: {
    async create(config) {
      const response = await api.post('/experiment/create', config)
      return response.data
    },

    async list() {
      const response = await api.get('/experiment/list')
      return response.data
    },

    async get(experimentId) {
      const response = await api.get(`/experiment/${experimentId}`)
      return response.data
    },

    async getStatus(experimentId) {
      const response = await api.get(`/experiment/${experimentId}/status`)
      return response.data
    },

    async getResults(experimentId) {
      const response = await api.get(`/experiment/${experimentId}/results`)
      return response.data
    },

    async getMetrics(experimentId) {
      const response = await api.get(`/experiment/${experimentId}/metrics`)
      return response.data
    },

    async export(experimentId, format = 'csv') {
      const response = await api.post(`/experiment/${experimentId}/export`, { format })
      return response.data
    },

    async delete(experimentId) {
      const response = await api.delete(`/experiment/${experimentId}`)
      return response.data
    },
  },

  // Real-time endpoints
  realtime: {
    async getConnections() {
      const response = await api.get('/realtime/connections')
      return response.data
    },

    async broadcast(message) {
      const response = await api.post('/realtime/broadcast', message)
      return response.data
    },

    async sendToSimulation(simulationId, message) {
      const response = await api.post(`/realtime/simulation/${simulationId}/send`, message)
      return response.data
    },
  },
}

// WebSocket service for real-time data
export class WebSocketService {
  constructor() {
    this.connections = new Map()
  }

  connect(endpoint, simulationId, onMessage, onError = null) {
    const wsUrl = `ws://localhost:8000/api/v2/realtime/${endpoint}/${simulationId}`
    
    if (this.connections.has(wsUrl)) {
      console.warn(`WebSocket already connected to ${wsUrl}`)
      return this.connections.get(wsUrl)
    }

    const ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log(`WebSocket connected: ${endpoint}/${simulationId}`)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error(`WebSocket error for ${endpoint}:`, error)
      if (onError) onError(error)
    }

    ws.onclose = (event) => {
      console.log(`WebSocket closed for ${endpoint}:`, event.code, event.reason)
      this.connections.delete(wsUrl)
    }

    this.connections.set(wsUrl, ws)
    return ws
  }

  disconnect(endpoint, simulationId) {
    const wsUrl = `ws://localhost:8000/api/v2/realtime/${endpoint}/${simulationId}`
    const ws = this.connections.get(wsUrl)
    
    if (ws) {
      ws.close()
      this.connections.delete(wsUrl)
    }
  }

  disconnectAll() {
    for (const ws of this.connections.values()) {
      ws.close()
    }
    this.connections.clear()
  }

  // Convenience methods for specific endpoints
  connectSimulation(simulationId, onMessage, onError) {
    return this.connect('simulation', simulationId, onMessage, onError)
  }

  connectMetrics(simulationId, onMessage, onError) {
    return this.connect('metrics', simulationId, onMessage, onError)
  }

  connectVisualization(simulationId, onMessage, onError) {
    return this.connect('visualization', simulationId, onMessage, onError)
  }
}

export const wsService = new WebSocketService()

export default apiService