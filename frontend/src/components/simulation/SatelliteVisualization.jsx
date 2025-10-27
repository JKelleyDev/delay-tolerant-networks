import React, { useRef, useEffect, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'

const SatelliteVisualization = ({ simulationData, isRunning, onSatelliteClick }) => {
  const mountRef = useRef(null)
  const sceneRef = useRef(null)
  const rendererRef = useRef(null)
  const cameraRef = useRef(null)
  const controlsRef = useRef(null)
  const satelliteGroupRef = useRef(null)
  const contactLinesRef = useRef(null)
  const bundleGroupRef = useRef(null)
  const [selectedSatellite, setSelectedSatellite] = useState(null)

  useEffect(() => {
    if (!mountRef.current) return

    // Scene setup with dark space background
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x000511) // Deep space blue
    sceneRef.current = scene

    // Camera setup - positioned for dramatic view
    const camera = new THREE.PerspectiveCamera(
      60,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      50000
    )
    camera.position.set(15000, 10000, 15000)
    cameraRef.current = camera

    // Renderer with anti-aliasing for crisp visuals
    const renderer = new THREE.WebGLRenderer({ 
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    })
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight)
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 0.8
    rendererRef.current = renderer

    // Orbital controls for cinematic camera movement
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    controls.screenSpacePanning = false
    controls.minDistance = 7000
    controls.maxDistance = 30000
    controls.target.set(0, 0, 0)
    controlsRef.current = controls

    // Create Earth with simple, reliable texture approach
    const earthGeometry = new THREE.SphereGeometry(6371, 64, 64)
    const textureLoader = new THREE.TextureLoader()
    
    // Use reliable CDN Earth texture
    const earthTexture = textureLoader.load(
      'https://threejs.org/examples/textures/planets/earth_atmos_2048.jpg',
      (texture) => {
        texture.wrapS = THREE.RepeatWrapping
        texture.wrapT = THREE.ClampToEdgeWrapping
        console.log('Earth texture loaded successfully')
      },
      (progress) => {
        console.log('Loading Earth texture...', (progress.loaded / progress.total * 100) + '%')
      },
      (error) => {
        console.warn('Failed to load Three.js Earth texture, using backup')
        // Use backup Earth texture from different CDN
        const backupTexture = textureLoader.load(
          'https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/The_Earth_seen_from_Apollo_17.jpg/1024px-The_Earth_seen_from_Apollo_17.jpg'
        )
        earthMaterial.map = backupTexture
        earthMaterial.needsUpdate = true
      }
    )
    
    // Simple, reliable Earth material
    const earthMaterial = new THREE.MeshPhongMaterial({
      map: earthTexture,
      shininess: 1,
      transparent: false
    })
    
    const earth = new THREE.Mesh(earthGeometry, earthMaterial)
    earth.rotation.x = -Math.PI * 0.02 // Earth's axial tilt
    scene.add(earth)

    // Simple atmospheric glow
    const atmosphereGeometry = new THREE.SphereGeometry(6500, 64, 64)
    const atmosphereMaterial = new THREE.ShaderMaterial({
      uniforms: {
        glowColor: { value: new THREE.Color(0x00aaff) }
      },
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 glowColor;
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.6 - dot(vNormal, vec3(0, 0, 1.0)), 2.0);
          gl_FragColor = vec4(glowColor, intensity * 0.4);
        }
      `,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      transparent: true
    })
    
    const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial)
    scene.add(atmosphere)

    // Starfield background for space ambiance
    const starGeometry = new THREE.BufferGeometry()
    const starMaterial = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 2,
      sizeAttenuation: false
    })
    
    const starVertices = []
    for (let i = 0; i < 10000; i++) {
      const x = (Math.random() - 0.5) * 100000
      const y = (Math.random() - 0.5) * 100000
      const z = (Math.random() - 0.5) * 100000
      starVertices.push(x, y, z)
    }
    
    starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starVertices, 3))
    const stars = new THREE.Points(starGeometry, starMaterial)
    scene.add(stars)

    // Simple but effective lighting
    const sunLight = new THREE.DirectionalLight(0xffffff, 1.2)
    sunLight.position.set(50000, 30000, 50000)
    sunLight.castShadow = true
    sunLight.shadow.mapSize.width = 2048
    sunLight.shadow.mapSize.height = 2048
    scene.add(sunLight)

    // Ambient lighting for visibility
    const ambientLight = new THREE.AmbientLight(0x404040, 0.4)
    scene.add(ambientLight)

    // Satellite group for organization
    const satelliteGroup = new THREE.Group()
    satelliteGroupRef.current = satelliteGroup
    scene.add(satelliteGroup)

    // Contact lines group
    const contactLines = new THREE.Group()
    contactLinesRef.current = contactLines
    scene.add(contactLines)

    // Bundle visualization group
    const bundleGroup = new THREE.Group()
    bundleGroupRef.current = bundleGroup
    scene.add(bundleGroup)

    // Ground stations group - will rotate with Earth
    const groundStationGroup = new THREE.Group()
    earth.add(groundStationGroup) // Add to Earth so it rotates with it
    
    // Add major ground stations
    const groundStations = [
      { name: 'Los Angeles', lat: 34.0522, lon: -118.2437, color: 0x00ff00 },
      { name: 'Tokyo', lat: 35.6762, lon: 139.6503, color: 0x00ff00 },
      { name: 'London', lat: 51.5074, lon: -0.1278, color: 0xffaa00 },
      { name: 'Sydney', lat: -33.8688, lon: 151.2093, color: 0xffaa00 }
    ]
    
    groundStations.forEach(gs => {
      // Convert lat/lon to 3D coordinates
      const phi = (90 - gs.lat) * (Math.PI / 180)
      const theta = (gs.lon + 180) * (Math.PI / 180)
      const radius = 6371 + 50 // Slightly above Earth surface
      
      const x = -(radius * Math.sin(phi) * Math.cos(theta))
      const y = radius * Math.cos(phi)
      const z = radius * Math.sin(phi) * Math.sin(theta)
      
      // Ground station antenna
      const gsGeometry = new THREE.ConeGeometry(30, 100, 8)
      const gsMaterial = new THREE.MeshPhongMaterial({
        color: gs.color,
        emissive: gs.color,
        emissiveIntensity: 0.3
      })
      const gsAntenna = new THREE.Mesh(gsGeometry, gsMaterial)
      gsAntenna.position.set(x, y, z)
      gsAntenna.lookAt(0, 0, 0)
      
      // Rotating dish animation
      gsAntenna.userData = { rotationSpeed: 0.02 }
      
      // Simple beam indicator (no large range visualization)
      const beamGeometry = new THREE.CylinderGeometry(2, 20, 100, 8)
      const beamMaterial = new THREE.MeshBasicMaterial({
        color: gs.color,
        transparent: true,
        opacity: 0.3
      })
      const beam = new THREE.Mesh(beamGeometry, beamMaterial)
      beam.position.copy(gsAntenna.position)
      beam.lookAt(0, 0, 0)
      
      // Ground station label
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')
      canvas.width = 256
      canvas.height = 64
      context.fillStyle = '#00ff88'
      context.font = '20px "Courier New", monospace'
      context.fillText(gs.name, 10, 40)
      
      const texture = new THREE.CanvasTexture(canvas)
      const labelMaterial = new THREE.SpriteMaterial({ map: texture })
      const label = new THREE.Sprite(labelMaterial)
      label.scale.set(400, 100, 1)
      label.position.copy(gsAntenna.position)
      label.position.y += 150
      
      groundStationGroup.add(gsAntenna)
      groundStationGroup.add(beam)
      groundStationGroup.add(label)
    })

    // Grid reference for scale (optional)
    const gridHelper = new THREE.PolarGridHelper(20000, 16, 8, 64, 0x333333, 0x333333)
    gridHelper.position.y = -8000
    scene.add(gridHelper)

    mountRef.current.appendChild(renderer.domElement)

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate)
      
      // Rotate Earth slowly
      earth.rotation.y += 0.001
      
      // Animate satellite footprints and transmission beams
      if (satelliteGroupRef.current) {
        satelliteGroupRef.current.children.forEach(child => {
          if (child.userData && child.userData.isActive) {
            child.userData.time += 0.05
            const pulse = Math.sin(child.userData.time) * 0.2 + 0.8
            
            if (child.material) {
              // Single material (footprint)
              child.material.opacity = child.userData.baseOpacity * pulse
              const scale = 1 + Math.sin(child.userData.time * 1.5) * 0.1
              child.scale.setScalar(scale)
            } else if (child.children) {
              // Group with multiple children (beam lines)
              child.children.forEach(line => {
                if (line.material) {
                  line.material.opacity = line.material.userData?.baseOpacity || 
                    (line.material.opacity / pulse) * pulse
                }
              })
            }
          }
        })
      }
      
      // Gentle star rotation
      stars.rotation.y += 0.0002
      
      controls.update()
      renderer.render(scene, camera)
    }
    animate()

    // Handle window resize
    const handleResize = () => {
      if (!mountRef.current) return
      
      const width = mountRef.current.clientWidth
      const height = mountRef.current.clientHeight
      
      camera.aspect = width / height
      camera.updateProjectionMatrix()
      renderer.setSize(width, height)
    }
    
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement)
      }
      renderer.dispose()
    }
  }, [])

  // Update satellites when simulation data changes
  useEffect(() => {
    if (!satelliteGroupRef.current || !simulationData?.satellites) return

    // Clear existing satellites
    satelliteGroupRef.current.clear()

    // Create satellites with military-style appearance
    Object.entries(simulationData.satellites).forEach(([satId, satData]) => {
      // Satellite geometry - angular military design
      const satGeometry = new THREE.OctahedronGeometry(50, 0)
      
      // Satellite material with glow effect
      const satMaterial = new THREE.MeshPhongMaterial({
        color: satData.status === 'active' ? 0x00ff88 : 0xff4444,
        emissive: satData.status === 'active' ? 0x002211 : 0x221100,
        shininess: 100,
        transparent: true,
        opacity: 0.9
      })
      
      const satellite = new THREE.Mesh(satGeometry, satMaterial)
      
      // Position satellite
      const position = satData.position || { x: 0, y: 0, z: 0 }
      satellite.position.set(position.x, position.y, position.z)
      
      // Add satellite label
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')
      canvas.width = 256
      canvas.height = 64
      context.fillStyle = '#00ff88'
      context.font = '24px "Courier New", monospace'
      context.fillText(satId.replace('starlink_sat_', 'SAT-'), 10, 40)
      
      const texture = new THREE.CanvasTexture(canvas)
      const labelMaterial = new THREE.SpriteMaterial({ map: texture })
      const label = new THREE.Sprite(labelMaterial)
      label.scale.set(500, 125, 1)
      label.position.copy(satellite.position)
      label.position.y += 200
      
      // Create Earth footprint projection (only show when transmitting)
      const isTransmitting = (satData.contacts || 0) > 0 || (satData.bundles_stored || 0) > 0
      let footprintProjection = null
      
      if (isTransmitting) {
        // Calculate satellite's footprint on Earth surface
        const satAltitude = Math.sqrt(position.x ** 2 + position.y ** 2 + position.z ** 2) - 6371
        const earthRadius = 6371
        
        // Calculate footprint radius (coverage circle on Earth)
        const footprintRadius = earthRadius * Math.acos(earthRadius / (earthRadius + satAltitude))
        
        // Project footprint onto Earth surface
        const satToEarth = new THREE.Vector3(position.x, position.y, position.z).normalize()
        const footprintCenter = satToEarth.clone().multiplyScalar(earthRadius)
        
        // Create circular footprint on Earth surface
        const footprintGeometry = new THREE.CircleGeometry(footprintRadius, 32)
        const footprintMaterial = new THREE.MeshBasicMaterial({
          color: (satData.bundles_stored || 0) > 0 ? 0x00ff44 : 0x0088ff,
          transparent: true,
          opacity: 0.6,
          side: THREE.DoubleSide
        })
        
        footprintProjection = new THREE.Mesh(footprintGeometry, footprintMaterial)
        footprintProjection.position.copy(footprintCenter)
        footprintProjection.lookAt(0, 0, 0) // Face away from Earth center
        
        // Add pulsing animation for active transmission
        footprintProjection.userData = { 
          isActive: true,
          baseOpacity: 0.6,
          time: Math.random() * Math.PI * 2 // Random start phase
        }
        
        // Add transmission beam from satellite to Earth footprint
        const satPos = new THREE.Vector3(position.x, position.y, position.z)
        const earthPos = footprintCenter.clone()
        
        // Create multiple beam lines for a cone effect
        const beamLines = new THREE.Group()
        
        // Main center beam
        const centerPoints = [satPos, earthPos]
        const centerGeometry = new THREE.BufferGeometry().setFromPoints(centerPoints)
        const centerMaterial = new THREE.LineBasicMaterial({
          color: (satData.bundles_stored || 0) > 0 ? 0x00ff44 : 0x0088ff,
          linewidth: 3,
          transparent: true,
          opacity: 0.8
        })
        const centerBeam = new THREE.Line(centerGeometry, centerMaterial)
        beamLines.add(centerBeam)
        
        // Add cone edge lines for beam spread
        const beamSpread = footprintRadius * 0.3 // Beam widens as it approaches Earth
        const perpVector1 = new THREE.Vector3(1, 0, 0).cross(satToEarth).normalize()
        const perpVector2 = new THREE.Vector3(0, 1, 0).cross(satToEarth).normalize()
        
        for (let i = 0; i < 8; i++) {
          const angle = (i / 8) * Math.PI * 2
          const offset = perpVector1.clone().multiplyScalar(Math.cos(angle) * beamSpread)
            .add(perpVector2.clone().multiplyScalar(Math.sin(angle) * beamSpread))
          
          const edgePoint = earthPos.clone().add(offset)
          const edgePoints = [satPos, edgePoint]
          const edgeGeometry = new THREE.BufferGeometry().setFromPoints(edgePoints)
          const edgeMaterial = new THREE.LineBasicMaterial({
            color: (satData.bundles_stored || 0) > 0 ? 0x00ff44 : 0x0088ff,
            transparent: true,
            opacity: 0.3
          })
          const edgeBeam = new THREE.Line(edgeGeometry, edgeMaterial)
          beamLines.add(edgeBeam)
        }
        
        beamLines.userData = {
          isActive: true,
          baseOpacity: 0.6,
          time: Math.random() * Math.PI * 2
        }
        
        satelliteGroupRef.current.add(beamLines)
      }
      
      // Add bundle storage indicator
      if ((satData.bundles_stored || 0) > 0) {
        const bundleGeometry = new THREE.SphereGeometry(20, 8, 8)
        const bundleMaterial = new THREE.MeshBasicMaterial({
          color: 0xffaa00,
          transparent: true,
          opacity: 0.8
        })
        const bundleIndicator = new THREE.Mesh(bundleGeometry, bundleMaterial)
        bundleIndicator.position.copy(satellite.position)
        bundleIndicator.position.y += 100
        satelliteGroupRef.current.add(bundleIndicator)
      }
      
      satellite.userData = { id: satId, data: satData }
      
      satelliteGroupRef.current.add(satellite)
      satelliteGroupRef.current.add(label)
      if (footprintProjection) {
        satelliteGroupRef.current.add(footprintProjection)
      }
    })
  }, [simulationData?.satellites])

  // Update contact lines and bundle routing
  useEffect(() => {
    if (!contactLinesRef.current || !simulationData?.contacts) return

    // Clear existing contact lines
    contactLinesRef.current.clear()

    // Draw active contact lines with sci-fi beam effects
    simulationData.contacts.forEach((contact, index) => {
      if (contact.isActive) {
        const points = [
          new THREE.Vector3(contact.source.x, contact.source.y, contact.source.z),
          new THREE.Vector3(contact.target.x, contact.target.y, contact.target.z)
        ]
        
        const geometry = new THREE.BufferGeometry().setFromPoints(points)
        const material = new THREE.LineBasicMaterial({
          color: contact.hasData ? 0x00ffff : 0x004488,
          linewidth: contact.hasData ? 3 : 1,
          transparent: true,
          opacity: contact.hasData ? 0.8 : 0.3
        })
        
        const line = new THREE.Line(geometry, material)
        contactLinesRef.current.add(line)
        
        // Add pulsing effect for data transmission
        if (contact.hasData) {
          // Create multiple pulses for step-by-step visualization
          const numPulses = 3
          for (let i = 0; i < numPulses; i++) {
            const pulseGeometry = new THREE.SphereGeometry(15, 8, 8)
            const pulseMaterial = new THREE.MeshBasicMaterial({
              color: 0x00ffff,
              transparent: true,
              opacity: 0.8 - (i * 0.2)
            })
            const pulse = new THREE.Mesh(pulseGeometry, pulseMaterial)
            
            // Stagger pulse timing for step-by-step effect
            const time = (Date.now() / 800) + (i * 0.3)
            const progress = (time % 1)
            pulse.position.lerpVectors(points[0], points[1], progress)
            
            // Add trail effect
            const trailGeometry = new THREE.SphereGeometry(8, 6, 6)
            const trailMaterial = new THREE.MeshBasicMaterial({
              color: 0x0088ff,
              transparent: true,
              opacity: 0.3
            })
            const trail = new THREE.Mesh(trailGeometry, trailMaterial)
            const trailProgress = Math.max(0, progress - 0.1)
            trail.position.lerpVectors(points[0], points[1], trailProgress)
            
            contactLinesRef.current.add(pulse)
            contactLinesRef.current.add(trail)
          }
        }
      }
    })
    
    // Add packet path visualization if enabled
    if (simulationData?.packetPaths) {
      simulationData.packetPaths.forEach(path => {
        // Draw complete path with different colors for each hop
        const pathColors = [0xff0000, 0x00ff00, 0x0000ff, 0xffff00, 0xff00ff]
        
        path.hops.forEach((hop, hopIndex) => {
          if (hopIndex < path.hops.length - 1) {
            const startPos = new THREE.Vector3(hop.x, hop.y, hop.z)
            const endPos = new THREE.Vector3(
              path.hops[hopIndex + 1].x,
              path.hops[hopIndex + 1].y,
              path.hops[hopIndex + 1].z
            )
            
            const hopGeometry = new THREE.BufferGeometry().setFromPoints([startPos, endPos])
            const hopMaterial = new THREE.LineBasicMaterial({
              color: pathColors[hopIndex % pathColors.length],
              linewidth: 2,
              transparent: true,
              opacity: 0.7
            })
            
            const hopLine = new THREE.Line(hopGeometry, hopMaterial)
            contactLinesRef.current.add(hopLine)
            
            // Add hop number labels
            const labelCanvas = document.createElement('canvas')
            const labelContext = labelCanvas.getContext('2d')
            labelCanvas.width = 64
            labelCanvas.height = 64
            labelContext.fillStyle = '#ffffff'
            labelContext.font = '24px "Courier New", monospace'
            labelContext.fillText(`${hopIndex + 1}`, 20, 40)
            
            const labelTexture = new THREE.CanvasTexture(labelCanvas)
            const labelMaterial = new THREE.SpriteMaterial({ map: labelTexture })
            const hopLabel = new THREE.Sprite(labelMaterial)
            hopLabel.scale.set(200, 200, 1)
            hopLabel.position.lerpVectors(startPos, endPos, 0.5)
            contactLinesRef.current.add(hopLabel)
          }
        })
      })
    }
  }, [simulationData?.contacts, simulationData?.packetPaths])

  // Click handler for satellite selection
  useEffect(() => {
    if (!rendererRef.current || !cameraRef.current) return

    const raycaster = new THREE.Raycaster()
    const mouse = new THREE.Vector2()

    const handleClick = (event) => {
      const rect = mountRef.current.getBoundingClientRect()
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

      raycaster.setFromCamera(mouse, cameraRef.current)
      
      if (satelliteGroupRef.current) {
        const intersects = raycaster.intersectObjects(satelliteGroupRef.current.children, true)
        
        if (intersects.length > 0) {
          const selectedObject = intersects[0].object
          if (selectedObject.userData && selectedObject.userData.id) {
            setSelectedSatellite(selectedObject.userData.id)
            if (onSatelliteClick) {
              onSatelliteClick(selectedObject.userData.id, selectedObject.userData.data)
            }
          }
        }
      }
    }

    mountRef.current.addEventListener('click', handleClick)
    
    return () => {
      if (mountRef.current) {
        mountRef.current.removeEventListener('click', handleClick)
      }
    }
  }, [onSatelliteClick])

  return (
    <div className="relative w-full h-full">
      <div ref={mountRef} className="w-full h-full" />
      
      {/* Military-style HUD overlay - moved to right */}
      <div className="absolute top-10 right-4 bg-black bg-opacity-70 border border-cyan-400 p-4 font-mono text-green-400">
        <div className="text-cyan-400 text-sm mb-2">◤ COMMAND CENTER ◥</div>
        <div className="space-y-1 text-xs">
          <div>STATUS: {isRunning ? <span className="text-green-400 animate-pulse">ACTIVE</span> : <span className="text-red-400">STANDBY</span>}</div>
          <div>SATELLITES: {simulationData?.satellites ? Object.keys(simulationData.satellites).length : 0}</div>
          <div>CONTACTS: {simulationData?.contacts ? simulationData.contacts.filter(c => c.isActive).length : 0}</div>
          <div>BUNDLES: {simulationData?.bundles?.active || 0}</div>
        </div>
      </div>

      {/* Satellite selection info - moved below command center */}
      {selectedSatellite && (
        <div className="absolute top-36 right-4 bg-black bg-opacity-70 border border-yellow-400 p-4 font-mono text-yellow-400">
          <div className="text-sm mb-2">◤ TARGET ACQUIRED ◥</div>
          <div className="space-y-1 text-xs">
            <div>ID: {selectedSatellite}</div>
            <div>STATUS: TRACKING</div>
            <div className="text-green-400 cursor-pointer" onClick={() => setSelectedSatellite(null)}>
              [CLEAR TARGET]
            </div>
          </div>
        </div>
      )}

      {/* Control instructions - moved to right */}
      <div className="absolute bottom-10 right-4 bg-black bg-opacity-70 border border-blue-400 p-4 font-mono text-blue-400">
        <div className="text-sm mb-2">◤ CONTROLS ◥</div>
        <div className="space-y-1 text-xs">
          <div>MOUSE: Orbit Camera</div>
          <div>WHEEL: Zoom</div>
          <div>CLICK: Select Satellite</div>
        </div>
      </div>
    </div>
  )
}

export default SatelliteVisualization