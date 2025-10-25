import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'

// Components
import Layout from './components/Layout'
import SimulationView from './pages/SimulationView'
import ExperimentView from './pages/ExperimentView'
import ConstellationView from './pages/ConstellationView'

// Services
import { apiService } from './services/api'

// Create query client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000, // 30 seconds
    },
  },
})

function App() {
  const [apiStatus, setApiStatus] = useState('checking')
  const [error, setError] = useState(null)

  // Check API connectivity on startup
  useEffect(() => {
    const checkAPI = async () => {
      try {
        await apiService.healthCheck()
        setApiStatus('connected')
      } catch (err) {
        setApiStatus('disconnected')
        setError('Cannot connect to DTN Simulator backend')
        console.error('API connection failed:', err)
      }
    }

    checkAPI()

    // Check API status periodically
    const interval = setInterval(checkAPI, 30000) // Every 30 seconds
    return () => clearInterval(interval)
  }, [])

  if (apiStatus === 'checking') {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 to-blue-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <p className="text-white text-lg">Connecting to DTN Simulator...</p>
        </div>
      </div>
    )
  }

  if (apiStatus === 'disconnected') {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 to-red-900">
        <div className="text-center max-w-md">
          <div className="text-red-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <h2 className="text-white text-xl font-semibold mb-2">Connection Failed</h2>
          <p className="text-gray-300 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="btn-primary"
          >
            Retry Connection
          </button>
          <div className="mt-6 text-sm text-gray-400">
            <p>Make sure the backend server is running:</p>
            <code className="block mt-2 p-2 bg-gray-800 rounded">
              cd backend && python -m src.main
            </code>
          </div>
        </div>
      </div>
    )
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<SimulationView />} />
            <Route path="/simulation" element={<SimulationView />} />
            <Route path="/experiment" element={<ExperimentView />} />
            <Route path="/constellation" element={<ConstellationView />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  )
}

export default App