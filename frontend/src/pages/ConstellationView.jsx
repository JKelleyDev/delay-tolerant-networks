import React, { useState, useCallback, useEffect } from 'react'
import { Globe, Upload, Download, Trash2, Satellite, Info } from 'lucide-react'

const ConstellationView = () => {
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [uploadData, setUploadData] = useState({
    name: '',
    description: '',
    file: null
  })
  const [selectedConstellation, setSelectedConstellation] = useState(null)
  const [constellations, setConstellations] = useState({})
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchConstellations()
  }, [])

  const fetchConstellations = async () => {
    try {
      const response = await fetch('/api/v2/constellation/library')
      const data = await response.json()
      if (data.success) {
        setConstellations(data.data.constellations || {})
      }
    } catch (err) {
      console.error('Failed to fetch constellations:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const [uploadLoading, setUploadLoading] = useState(false)

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file && file.type === 'text/csv') {
      setUploadData(prev => ({ ...prev, file }))
    }
  }

  const handleUploadSubmit = async (e) => {
    e.preventDefault()
    if (uploadData.name && uploadData.file) {
      setUploadLoading(true)
      
      try {
        const formData = new FormData()
        formData.append('name', uploadData.name)
        formData.append('description', uploadData.description || '')
        formData.append('file', uploadData.file)
        
        console.log('Uploading constellation:', {
          name: uploadData.name,
          description: uploadData.description,
          fileName: uploadData.file.name,
          fileSize: uploadData.file.size
        })
        
        const response = await fetch('/api/v2/constellation/upload', {
          method: 'POST',
          body: formData
        })
        
        const data = await response.json()
        
        if (response.ok && data.success) {
          console.log('Upload successful:', data.message)
          setShowUploadForm(false)
          setUploadData({ name: '', description: '', file: null })
          await fetchConstellations() // Refresh constellation list
        } else {
          console.error('Upload failed:', {
            status: response.status,
            statusText: response.statusText,
            data: data
          })
        }
      } catch (err) {
        console.error('Upload failed:', err)
      } finally {
        setUploadLoading(false)
      }
    }
  }

  const getConstellationType = (type) => {
    const types = {
      leo: { label: 'LEO', color: 'bg-blue-600', description: 'Low Earth Orbit' },
      meo: { label: 'MEO', color: 'bg-green-600', description: 'Medium Earth Orbit' },
      geo: { label: 'GEO', color: 'bg-purple-600', description: 'Geostationary Orbit' },
      heo: { label: 'HEO', color: 'bg-orange-600', description: 'Highly Elliptical Orbit' },
      custom: { label: 'Custom', color: 'bg-gray-600', description: 'Custom Configuration' }
    }
    return types[type] || types.custom
  }

  const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Satellite Constellations</h1>
          <p className="text-gray-400 mt-2">
            Manage satellite constellation configurations for DTN simulations
          </p>
        </div>
        <button
          onClick={() => setShowUploadForm(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <Upload className="w-5 h-5" />
          <span>Upload Constellation</span>
        </button>
      </div>

      {/* Upload Modal */}
      {showUploadForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="card max-w-lg w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">Upload Custom Constellation</h2>
              <button
                onClick={() => setShowUploadForm(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div>
                <label className="form-label">Constellation Name</label>
                <input
                  type="text"
                  value={uploadData.name}
                  onChange={(e) => setUploadData({...uploadData, name: e.target.value})}
                  className="form-input w-full"
                  placeholder="e.g., My Custom Constellation"
                  required
                />
              </div>

              <div>
                <label className="form-label">Description</label>
                <textarea
                  value={uploadData.description}
                  onChange={(e) => setUploadData({...uploadData, description: e.target.value})}
                  className="form-input w-full h-20 resize-none"
                  placeholder="Describe the constellation purpose and configuration..."
                />
              </div>

              <div>
                <label className="form-label">CSV File</label>
                <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center">
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="hidden"
                    id="csvFileInput"
                  />
                  <label htmlFor="csvFileInput" className="cursor-pointer">
                    {uploadData.file ? (
                      <div>
                        <Upload className="w-8 h-8 text-green-400 mx-auto mb-2" />
                        <p className="text-white">{uploadData.file.name}</p>
                        <p className="text-sm text-gray-400">Click to change file</p>
                      </div>
                    ) : (
                      <div>
                        <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-white">Click to select CSV file</p>
                        <p className="text-sm text-gray-400 mt-1">
                          Format: satellite_id,name,altitude,inclination,raan,eccentricity,arg_perigee,mean_anomaly
                        </p>
                      </div>
                    )}
                  </label>
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="submit"
                  disabled={uploadLoading || !uploadData.name || !uploadData.file}
                  className="btn-primary flex-1 disabled:opacity-50"
                >
                  {uploadLoading ? 'Uploading...' : 'Upload Constellation'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowUploadForm(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Constellation Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {constellations && Object.entries(constellations).map(([key, constellation]) => {
          const typeInfo = getConstellationType(constellation.type)
          const isCustom = constellation.uploaded || false

          return (
            <div
              key={key}
              className={`card cursor-pointer transition-all duration-200 hover:scale-105 ${
                selectedConstellation === key ? 'ring-2 ring-blue-400' : ''
              }`}
              onClick={() => setSelectedConstellation(selectedConstellation === key ? null : key)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <Satellite className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{constellation.name}</h3>
                    <span className={`px-2 py-1 text-xs rounded-full text-white ${typeInfo.color}`}>
                      {typeInfo.label}
                    </span>
                  </div>
                </div>
                
                {isCustom && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      console.log('Delete constellation:', key)
                    }}
                    className="text-red-400 hover:text-red-300 p-1"
                    title="Delete constellation"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Satellites:</span>
                  <span className="text-white font-medium">
                    {formatNumber(constellation.satellites)}
                  </span>
                </div>
                
                {constellation.shells && constellation.shells.length > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Altitude:</span>
                    <span className="text-white">
                      {constellation.shells[0].altitude} km
                    </span>
                  </div>
                )}

                <p className="text-gray-400 text-xs mt-3 line-clamp-2">
                  {constellation.description}
                </p>
              </div>

              {selectedConstellation === key && constellation.shells && (
                <div className="mt-4 pt-4 border-t border-gray-600">
                  <h4 className="text-sm font-medium text-white mb-2">Orbital Shells</h4>
                  <div className="space-y-2">
                    {constellation.shells.map((shell, index) => (
                      <div key={index} className="text-xs bg-gray-700 p-2 rounded">
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <span className="text-gray-400">Alt:</span>
                            <span className="text-white ml-1">{shell.altitude} km</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Inc:</span>
                            <span className="text-white ml-1">{shell.inclination}°</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Count:</span>
                            <span className="text-white ml-1">{shell.count}</span>
                          </div>
                          {shell.eccentricity !== undefined && (
                            <div>
                              <span className="text-gray-400">Ecc:</span>
                              <span className="text-white ml-1">{shell.eccentricity}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Instructions */}
      <div className="card">
        <div className="card-header">
          <Info className="w-5 h-5 inline mr-2" />
          CSV Upload Format
        </div>
        
        <div className="space-y-4">
          <p className="text-gray-300">
            To upload a custom constellation, prepare a CSV file with the following columns:
          </p>
          
          <div className="bg-gray-800 p-4 rounded-lg font-mono text-sm">
            <div className="text-blue-400 mb-2">Required columns:</div>
            <div className="text-white">
              satellite_id,name,altitude,inclination,raan,eccentricity,arg_perigee,mean_anomaly
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="text-white font-medium mb-2">Parameter Descriptions:</h4>
              <ul className="space-y-1 text-gray-400">
                <li><strong>satellite_id:</strong> Unique identifier</li>
                <li><strong>name:</strong> Human-readable name</li>
                <li><strong>altitude:</strong> Orbital altitude in km</li>
                <li><strong>inclination:</strong> Orbital inclination in degrees</li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-medium mb-2">Advanced Parameters:</h4>
              <ul className="space-y-1 text-gray-400">
                <li><strong>raan:</strong> Right Ascension of Ascending Node (degrees)</li>
                <li><strong>eccentricity:</strong> Orbital eccentricity (0-1)</li>
                <li><strong>arg_perigee:</strong> Argument of perigee (degrees)</li>
                <li><strong>mean_anomaly:</strong> Mean anomaly (degrees)</li>
              </ul>
            </div>
          </div>

          <div className="mt-4">
            <a
              href="/sample_constellation.csv"
              download="sample_constellation.csv"
              className="btn-secondary inline-flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Download Sample CSV</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConstellationView