import React from 'react'
import { Activity, Satellite, Radio, Package, Zap, Globe } from 'lucide-react'

const MilitaryHUD = ({ simulationData, isRunning, selectedSatellite }) => {
  const activeContacts = simulationData?.contacts?.filter(c => c.isActive)?.length || 0
  const totalSatellites = simulationData?.satellites ? Object.keys(simulationData.satellites).length : 0
  const activeBundles = simulationData?.bundles?.active || 0
  const networkThroughput = simulationData?.metrics?.throughput || 0

  return (
    <div className="absolute inset-0 pointer-events-none">
      {/* Top Status Bar */}
      <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black via-gray-900 to-transparent p-4">
        <div className="flex items-center justify-between font-mono">
          <div className="flex items-center space-x-6">
            <div className="text-cyan-400 text-lg font-bold">
              ◤ DTN COMMAND CENTER ◥
            </div>
            <div className={`flex items-center space-x-2 ${isRunning ? 'text-green-400' : 'text-red-400'}`}>
              <Activity className="w-4 h-4" />
              <span className={isRunning ? 'animate-pulse' : ''}>
                {isRunning ? 'OPERATIONAL' : 'STANDBY'}
              </span>
            </div>
          </div>
          
          <div className="text-gray-400 text-sm">
            {new Date().toLocaleTimeString()} UTC
          </div>
        </div>
      </div>

      {/* Left Panel - System Status */}
      <div className="absolute left-4 top-20 space-y-2">
        {/* Network Status */}
        <div className="bg-black bg-opacity-80 border border-cyan-400 p-3 w-60">
          <div className="text-cyan-400 text-sm mb-3 flex items-center">
            <Globe className="w-4 h-4 mr-2" />
            NETWORK STATUS
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-300">Satellites:</span>
              <span className="text-green-400">{totalSatellites}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Active Links:</span>
              <span className="text-yellow-400">{simulationData?.metrics?.activeContacts || activeContacts}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Bundles Gen:</span>
              <span className="text-cyan-400">{simulationData?.bundles?.generated || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">In Buffers:</span>
              <span className="text-blue-400">{simulationData?.bundles?.in_buffers || activeBundles}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Delivered:</span>
              <span className="text-green-400">{simulationData?.bundles?.delivered || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Sats w/ Data:</span>
              <span className="text-purple-400">{simulationData?.metrics?.satellitesWithBundles || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Throughput:</span>
              <span className="text-purple-400">{networkThroughput.toFixed(1)} bndl/hr</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Buffer Util:</span>
              <span className="text-orange-400">{((simulationData?.metrics?.avgBufferUtilization || 0) * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* RF Status */}
        <div className="bg-black bg-opacity-80 border border-yellow-400 p-3 w-60">
          <div className="text-yellow-400 text-sm mb-3 flex items-center">
            <Radio className="w-4 h-4 mr-2" />
            RF SUBSYSTEM
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-300">Band:</span>
              <span className="text-green-400">{simulationData?.rfBand || 'Ka-band'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">SNR Avg:</span>
              <span className="text-cyan-400">{simulationData?.metrics?.avgSNR?.toFixed(1) || '0.0'} dB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Link Quality:</span>
              <span className="text-green-400">{simulationData?.metrics?.linkQuality?.toFixed(0) || '100'}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Weather:</span>
              <span className={simulationData?.weather?.enabled ? 'text-orange-400' : 'text-gray-400'}>
                {simulationData?.weather?.enabled ? 'ACTIVE' : 'DISABLED'}
              </span>
            </div>
          </div>
        </div>

        {/* DTN Routing */}
        <div className="bg-black bg-opacity-80 border border-green-400 p-3 w-60">
          <div className="text-green-400 text-sm mb-3 flex items-center">
            <Package className="w-4 h-4 mr-2" />
            DTN ROUTING
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-300">Algorithm:</span>
              <span className="text-cyan-400">{simulationData?.routing?.algorithm || 'Epidemic'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Delivery Ratio:</span>
              <span className="text-green-400">{((simulationData?.metrics?.deliveryRatio || 0) * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Avg Delay:</span>
              <span className="text-yellow-400">{(simulationData?.metrics?.avgDelay || 0).toFixed(1)}s</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Overhead:</span>
              <span className="text-orange-400">{(simulationData?.metrics?.overhead || 0).toFixed(1)}x</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Drop Strategy:</span>
              <span className="text-purple-400">{simulationData?.buffer_drop_strategy || 'oldest'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Target Info */}
      {selectedSatellite && (
        <div className="absolute right-4 top-20">
          <div className="bg-black bg-opacity-80 border border-red-400 p-3 w-60">
            <div className="text-red-400 text-sm mb-3 flex items-center">
              <Satellite className="w-4 h-4 mr-2" />
              TARGET ACQUIRED
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-300">ID:</span>
                <span className="text-white font-bold">{selectedSatellite.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Status:</span>
                <span className="text-green-400">OPERATIONAL</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Altitude:</span>
                <span className="text-cyan-400">{selectedSatellite.altitude || '550'} km</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Velocity:</span>
                <span className="text-yellow-400">{selectedSatellite.velocity || '7.66'} km/s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Contacts:</span>
                <span className="text-purple-400">{selectedSatellite.contacts || '0'}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Control Bar */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-gray-900 to-transparent p-4">
        <div className="flex items-center justify-between font-mono text-xs">
          <div className="flex items-center space-x-6 text-blue-400">
            <div>◤ NAVIGATION ◥</div>
            <div>MOUSE: Orbit • WHEEL: Zoom • CLICK: Select</div>
          </div>
          
          <div className="flex items-center space-x-4 text-gray-400">
            <div className="flex items-center space-x-2">
              <Zap className="w-3 h-3" />
              <span>SIM TIME: {simulationData?.simTime || '00:00:00'}</span>
              <span className={`ml-2 font-bold ${
                (simulationData?.timeAcceleration || 1) === 1 ? 'text-green-300' :
                (simulationData?.timeAcceleration || 1) < 10 ? 'text-yellow-300' :
                (simulationData?.timeAcceleration || 1) < 100 ? 'text-orange-300' : 'text-red-300'
              }`}>
                {simulationData?.timeAcceleration === 1 ? 'REAL-TIME' : 
                 simulationData?.timeAcceleration < 60 ? `${simulationData?.timeAcceleration || 1}x` :
                 simulationData?.timeAcceleration === 60 ? '1MIN/SEC' :
                 simulationData?.timeAcceleration === 300 ? '5MIN/SEC' :
                 simulationData?.timeAcceleration === 3600 ? '1HR/SEC' : 
                 `${simulationData?.timeAcceleration || 1}x`}
              </span>
            </div>
            <div>FPS: {simulationData?.fps || '60'}</div>
            <div className="text-xs text-gray-400">Network: {simulationData?.networkStatus || 'Unknown'}</div>
          </div>
        </div>
      </div>

      {/* Scanning Lines Effect */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-pulse"></div>
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-pulse"></div>
        <div className="absolute top-0 bottom-0 left-0 w-px bg-gradient-to-b from-transparent via-cyan-400 to-transparent animate-pulse"></div>
        <div className="absolute top-0 bottom-0 right-0 w-px bg-gradient-to-b from-transparent via-cyan-400 to-transparent animate-pulse"></div>
      </div>

      {/* Corner Decorations */}
      <div className="absolute top-4 left-4 w-8 h-8 border-l-2 border-t-2 border-cyan-400"></div>
      <div className="absolute top-4 right-4 w-8 h-8 border-r-2 border-t-2 border-cyan-400"></div>
      <div className="absolute bottom-4 left-4 w-8 h-8 border-l-2 border-b-2 border-cyan-400"></div>
      <div className="absolute bottom-4 right-4 w-8 h-8 border-r-2 border-b-2 border-cyan-400"></div>
    </div>
  )
}

export default MilitaryHUD