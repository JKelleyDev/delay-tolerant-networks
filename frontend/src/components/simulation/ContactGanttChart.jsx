import React, { useEffect, useRef, useState } from 'react'

const ContactGanttChart = ({ simulationData, selectedSatellite, isRunning }) => {
  const canvasRef = useRef(null)
  const [scrollOffset, setScrollOffset] = useState(0)
  const [animationTime, setAnimationTime] = useState(Date.now())
  
  // Update animation time for moving timeline
  useEffect(() => {
    if (!isRunning) return
    
    const interval = setInterval(() => {
      setAnimationTime(Date.now())
    }, 100) // Update 10 times per second for smooth animation
    
    return () => clearInterval(interval)
  }, [isRunning])
  
  useEffect(() => {
    if (!canvasRef.current || !simulationData?.satellites || typeof simulationData.satellites !== 'object') return
    
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const width = canvas.width
    const height = canvas.height
    
    // Clear canvas
    ctx.fillStyle = '#000011'
    ctx.fillRect(0, 0, width, height)
    
    // Chart parameters
    const timeWindow = 3600 // 1 hour time window in seconds
    const currentSimTime = simulationData.currentSimTime || 0
    const startTime = currentSimTime
    const endTime = startTime + timeWindow

    // Calculate simulated time for progress indicators (moved up to avoid reference error)
    const timeAcceleration = simulationData.timeAcceleration || 1
    const realTimeStart = animationTime / 1000
    const timeSinceStart = realTimeStart - (realTimeStart % 60)
    const simulatedTime = currentSimTime + (timeSinceStart * timeAcceleration / 60) % timeWindow

    const satellites = Object.keys(simulationData.satellites)
    const maxVisibleRows = Math.floor((height - 60) / 25) // Reserve space for legend
    const rowHeight = 25
    const timeScale = (width - 100) / timeWindow // pixels per second
    
    // Calculate scroll bounds
    const maxScrollOffset = Math.max(0, satellites.length - maxVisibleRows)
    const actualScrollOffset = Math.max(0, Math.min(scrollOffset, maxScrollOffset))
    
    // Get visible satellites
    const visibleSatellites = satellites.slice(actualScrollOffset, actualScrollOffset + maxVisibleRows)
    
    // Draw time axis
    ctx.strokeStyle = '#333'
    ctx.fillStyle = '#888'
    ctx.font = '10px Courier New'
    
    // Time grid lines
    for (let t = 0; t <= timeWindow; t += 300) { // Every 5 minutes
      const x = 80 + (t * timeScale)
      ctx.beginPath()
      ctx.moveTo(x, 20)
      ctx.lineTo(x, height - 10)
      ctx.stroke()
      
      // Time labels
      const minutes = Math.floor(t / 60)
      ctx.fillText(`+${minutes}m`, x - 15, 15)
    }
    
    // Draw satellite rows and contacts
    visibleSatellites.forEach((satId, index) => {
      const y = 30 + (index * rowHeight)
      const satellite = simulationData.satellites[satId]
      
      // Satellite label
      ctx.fillStyle = selectedSatellite === satId ? '#00ff88' : '#00aaff'
      ctx.font = selectedSatellite === satId ? 'bold 10px Courier New' : '10px Courier New'
      const shortId = satId.replace('starlink_sat_', 'S-')
      ctx.fillText(shortId, 5, y + 12)
      
      // Row separator
      ctx.strokeStyle = '#222'
      ctx.beginPath()
      ctx.moveTo(80, y - 2)
      ctx.lineTo(width, y - 2)
      ctx.stroke()
      
      // Draw contact windows for this satellite
      const timelineContacts = simulationData.timelineContacts || simulationData.contacts || []
      const contacts = Array.isArray(timelineContacts) ? 
        timelineContacts.filter(contact => 
          contact.source_id === satId || contact.target_id === satId
        ) : []
      
      // Generate predicted future contacts if we don't have enough
      const generatePredictedContacts = (satId, currentTime) => {
        const predictedContacts = []
        const satellites = Object.keys(simulationData.satellites)
        
        // Generate future contacts for next hour
        for (let t = 0; t < timeWindow; t += 600) { // Every 10 minutes
          if (Math.random() > 0.4) { // 60% chance of contact opportunity
            const targetSat = satellites[Math.floor(Math.random() * satellites.length)]
            if (targetSat !== satId) {
              const contactStart = currentTime + t + Math.random() * 300 // Some randomness
              const duration = 180 + Math.random() * 420 // 3-10 minutes
              
              predictedContacts.push({
                source_id: satId,
                target_id: targetSat,
                start_time: contactStart,
                end_time: contactStart + duration,
                duration_seconds: duration,
                status: 'scheduled',
                isActive: false,
                hasData: Math.random() > 0.6,
                elevation_angle: 15 + Math.random() * 55
              })
            }
          }
        }
        return predictedContacts
      }
      
      // Add predicted contacts if we don't have enough real ones
      const predictedContacts = contacts.length < 3 ? generatePredictedContacts(satId, currentSimTime) : []
      const allContacts = [...contacts, ...predictedContacts]
      
      allContacts.forEach(contact => {
        // Handle both timestamp strings and Date objects
        let contactStart, contactEnd
        if (contact.start_time instanceof Date) {
          contactStart = contact.start_time.getTime() / 1000
          contactEnd = contact.end_time.getTime() / 1000
        } else if (typeof contact.start_time === 'string') {
          contactStart = new Date(contact.start_time).getTime() / 1000
          contactEnd = new Date(contact.end_time).getTime() / 1000
        } else if (typeof contact.start_time === 'number') {
          contactStart = contact.start_time
          contactEnd = contact.end_time || (contactStart + (contact.duration_seconds || 300))
        } else {
          // Final fallback
          contactStart = startTime + (Math.random() * timeWindow / 2)
          contactEnd = contactStart + (contact.duration_seconds || 300)
        }
        
        // Check if contact overlaps with our time window
        if (contactEnd < startTime || contactStart > endTime) return
        
        const relativeStart = Math.max(0, contactStart - startTime)
        const relativeEnd = Math.min(timeWindow, contactEnd - startTime)
        
        const x1 = 80 + (relativeStart * timeScale)
        const x2 = 80 + (relativeEnd * timeScale)
        const contactWidth = Math.max(2, x2 - x1)
        
        // Color based on contact type and status
        if (contact.status === 'active' || contact.isActive) {
          ctx.fillStyle = contact.hasData ? '#00ff44' : '#0088ff' // Active contact
        } else if (contact.status === 'scheduled') {
          ctx.fillStyle = '#ffaa00' // Scheduled contact
        } else if (contact.status === 'potential') {
          ctx.fillStyle = '#666666' // Potential contact
        } else {
          // Fallback based on isActive
          ctx.fillStyle = contact.isActive ? '#0088ff' : '#444444'
        }
        
        // Draw contact bar
        ctx.fillRect(x1, y + 2, contactWidth, rowHeight - 6)
        
        // Draw border for active contacts
        if (contact.status === 'active' || contact.isActive) {
          ctx.strokeStyle = '#fff'
          ctx.lineWidth = 1
          ctx.strokeRect(x1, y + 2, contactWidth, rowHeight - 6)
        }
        
        // Add contact info if there's room
        if (contactWidth > 30) {
          ctx.fillStyle = '#fff'
          ctx.font = '8px Courier New'
          const targetId = contact.source_id === satId ? contact.target_id : contact.source_id
          const shortTarget = targetId.replace(/^(starlink_sat_|gs_)/, '')
          ctx.fillText(shortTarget.substring(0, 6), x1 + 2, y + 12)
        }
        
        // Add progress indicator for active contacts
        if (contact.status === 'active' || contact.isActive) {
          let progress = contact.progress
          
          // Calculate progress based on current time if not provided
          if (progress === undefined) {
            const contactDuration = contactEnd - contactStart
            const elapsed = simulatedTime - contactStart
            progress = Math.max(0, Math.min(1, elapsed / contactDuration))
          }
          
          const progressWidth = contactWidth * progress
          ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
          ctx.fillRect(x1, y + 2, progressWidth, rowHeight - 6)
          
          // Add progress percentage text
          if (contactWidth > 50 && progress > 0) {
            ctx.fillStyle = '#fff'
            ctx.font = '7px Courier New'
            ctx.fillText(`${(progress * 100).toFixed(0)}%`, x1 + contactWidth - 20, y + 15)
          }
        }
      })
      
      // Buffer utilization indicator
      const bufferUtil = satellite.buffer_utilization || 0
      const bufferBarWidth = 60
      const bufferX = width - bufferBarWidth - 10
      
      // Buffer background - make it visible even when empty
      ctx.fillStyle = '#222'
      ctx.fillRect(bufferX, y + 4, bufferBarWidth, 10)
      
      // Buffer border
      ctx.strokeStyle = '#666'
      ctx.strokeRect(bufferX, y + 4, bufferBarWidth, 10)
      
      // Buffer fill
      if (bufferUtil > 0) {
        const fillWidth = bufferBarWidth * bufferUtil
        if (bufferUtil > 0.8) ctx.fillStyle = '#ff4444'
        else if (bufferUtil > 0.6) ctx.fillStyle = '#ffaa00'
        else if (bufferUtil > 0.4) ctx.fillStyle = '#ffff00'
        else ctx.fillStyle = '#00ff44'
        
        ctx.fillRect(bufferX + 1, y + 5, fillWidth - 2, 8)
      }
      
      // Buffer percentage
      ctx.fillStyle = bufferUtil > 0 ? '#000' : '#aaa'
      ctx.font = '8px Courier New'
      ctx.fillText(`${(bufferUtil * 100).toFixed(0)}%`, bufferX + 2, y + 11)
      
      // Bundle count indicator
      const bundleCount = satellite.bundles_stored || 0
      if (bundleCount > 0) {
        ctx.fillStyle = '#ff8800'
        ctx.beginPath()
        ctx.arc(bufferX - 15, y + 8, 4, 0, Math.PI * 2)
        ctx.fill()
        
        ctx.fillStyle = '#fff'
        ctx.font = '8px Courier New'
        ctx.fillText(bundleCount.toString(), bufferX - 18, y + 10)
      }
    })
    
    // Current time indicator - moves with simulation time (simulatedTime already calculated above)
    const timeProgressInWindow = simulatedTime / timeWindow
    const currentTimeX = 80 + (timeProgressInWindow * (width - 100))
    
    // Clamp to visible area
    const clampedTimeX = Math.max(80, Math.min(currentTimeX, width - 20))
    
    ctx.strokeStyle = '#ff0000'
    ctx.lineWidth = 2
    ctx.setLineDash([5, 5])
    ctx.beginPath()
    ctx.moveTo(clampedTimeX, 20)
    ctx.lineTo(clampedTimeX, height - 10)
    ctx.stroke()
    ctx.setLineDash([])
    
    // Add current time label
    ctx.fillStyle = '#ff0000'
    ctx.font = 'bold 10px Courier New'
    const timeStr = simulationData.simTime || '00:00:00'
    const labelX = Math.min(clampedTimeX + 5, width - 120)
    ctx.fillText(`NOW: ${timeStr}`, labelX, 15)
    
    // Legend
    ctx.fillStyle = '#fff'
    ctx.font = '10px Courier New'
    ctx.fillText('CONTACT SCHEDULE', 5, height - 40)
    
    // Legend items
    const legendItems = [
      { color: '#00ff44', text: 'Active w/ Data' },
      { color: '#0088ff', text: 'Active' },
      { color: '#ffaa00', text: 'Scheduled' },
      { color: '#666666', text: 'Potential' }
    ]
    
    legendItems.forEach((item, i) => {
      const x = 5 + (i * 80)
      const y = height - 25
      
      ctx.fillStyle = item.color
      ctx.fillRect(x, y, 12, 8)
      
      ctx.fillStyle = '#aaa'
      ctx.font = '8px Courier New'
      ctx.fillText(item.text, x + 15, y + 6)
    })
    
    // Scroll indicators
    if (satellites.length > maxVisibleRows) {
      // Scroll up indicator
      if (actualScrollOffset > 0) {
        ctx.fillStyle = '#00ff88'
        ctx.font = '12px Courier New'
        ctx.fillText('▲', width - 20, 25)
      }
      
      // Scroll down indicator
      if (actualScrollOffset < maxScrollOffset) {
        ctx.fillStyle = '#00ff88'
        ctx.font = '12px Courier New'
        ctx.fillText('▼', width - 20, height - 45)
      }
      
      // Scroll position indicator
      ctx.fillStyle = '#666'
      ctx.font = '8px Courier New'
      ctx.fillText(`${actualScrollOffset + 1}-${Math.min(actualScrollOffset + maxVisibleRows, satellites.length)} of ${satellites.length}`, width - 80, height - 5)
    }
    
  }, [simulationData, selectedSatellite, scrollOffset, animationTime])
  
  const handleWheel = (event) => {
    event.preventDefault()
    const satellites = Object.keys(simulationData?.satellites || {})
    const maxVisibleRows = Math.floor((300 - 60) / 25) // Canvas height minus legend space
    const maxScrollOffset = Math.max(0, satellites.length - maxVisibleRows)
    
    if (event.deltaY > 0) {
      // Scroll down
      setScrollOffset(prev => Math.min(prev + 1, maxScrollOffset))
    } else {
      // Scroll up
      setScrollOffset(prev => Math.max(prev - 1, 0))
    }
  }
  
  return (
    <div className="bg-black border border-cyan-400 p-2">
      <div className="text-cyan-400 text-xs mb-2 font-mono">
        ◤ CONTACT TIMELINE ◥
      </div>
      <canvas
        ref={canvasRef}
        width={400}
        height={300}
        className="border border-gray-600"
        style={{ background: '#000011' }}
        onWheel={handleWheel}
      />
      <div className="text-xs text-gray-400 mt-1 font-mono">
        Timeline shows next hour • Red line = current time • Speed: {simulationData?.timeAcceleration || 1}x • Scroll to view all satellites
      </div>
    </div>
  )
}

export default ContactGanttChart