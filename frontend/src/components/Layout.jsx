import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Satellite, Activity, FlaskConical, Globe, Menu, X } from 'lucide-react'

const Navigation = ({ isOpen, setIsOpen }) => {
  const location = useLocation()
  
  const navItems = [
    { path: '/simulation', label: 'Simulation', icon: Satellite },
    { path: '/experiment', label: 'Experiments', icon: FlaskConical },
    { path: '/constellation', label: 'Constellations', icon: Globe },
  ]

  return (
    <nav className={`glass fixed left-0 top-0 h-full w-64 transform transition-transform duration-300 z-50 ${
      isOpen ? 'translate-x-0' : '-translate-x-full'
    } lg:translate-x-0`}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Satellite className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold text-white">DTN Simulator</h1>
          </div>
          <button 
            onClick={() => setIsOpen(false)}
            className="lg:hidden text-gray-400 hover:text-white"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
                onClick={() => setIsOpen(false)}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Status indicator */}
      <div className="absolute bottom-6 left-6 right-6">
        <div className="glass p-4 rounded-lg">
          <div className="flex items-center space-x-3">
            <div className="status-indicator status-running"></div>
            <div>
              <p className="text-sm font-medium text-white">System Status</p>
              <p className="text-xs text-gray-400">Connected</p>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-40 p-2 rounded-lg glass text-white"
      >
        <Menu className="w-6 h-6" />
      </button>

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="lg:hidden fixed inset-0 z-40 bg-black bg-opacity-50"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Navigation */}
      <Navigation isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />

      {/* Main content */}
      <div className="lg:ml-64 min-h-screen">
        <div className="h-screen overflow-y-auto">
          <div className="p-6">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Layout