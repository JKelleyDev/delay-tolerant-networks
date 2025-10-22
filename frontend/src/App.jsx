import React, { useRef, useState, useEffect, useMemo } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Stars, Stats } from "@react-three/drei";
import * as THREE from "three";
import { geodeticToECEF, ecefToGeodetic, useEarthPicking } from "./coordinates";
import { events } from "./events";

// Earth
function Earth({ sunDir = new THREE.Vector3(1, 0, 0) }) {
  const ref = useRef();
  const [detail, setDetail] = useState(64);

  // Fallback texture set (replace later with 4K assets)
  const textures = useMemo(() => {
    const L = new THREE.TextureLoader();
    const fallback = "https://threejs.org/examples/textures/land_ocean_ice_cloud_2048.jpg";
    return {
      day: L.load(fallback),
      night: L.load(fallback),
      spec: L.load(fallback),
      clouds: L.load(fallback),
    };
  }, []);

  // Spin Earth and adjust LOD
  useFrame(({ camera }) => {
    if (ref.current) ref.current.rotation.y += 0.0008;
    const d = camera.position.length();
    const target = d > 120000 ? 32 : 64;
    if (target !== detail) setDetail(target);
  });

  // Simple day/night blend shader
  const material = useMemo(() => {
    const uniforms = {
      dayTex: { value: textures.day },
      nightTex: { value: textures.night },
      specTex: { value: textures.spec },
      sunDir: { value: sunDir.clone().normalize() },
    };
    const frag = `
      uniform sampler2D dayTex, nightTex, specTex;
      uniform vec3 sunDir;
      varying vec3 vNormal; varying vec2 vUv; varying vec3 vPos;
      void main(){
        vec3 N = normalize(vNormal);
        float k = smoothstep(-0.1, 0.1, dot(N, normalize(sunDir)));
        vec3 day = texture2D(dayTex, vUv).rgb;
        vec3 night = texture2D(nightTex, vUv).rgb;
        float spec = texture2D(specTex, vUv).r;
        vec3 col = mix(night, day, k);
        float s = pow(max(dot(reflect(-normalize(sunDir), N), normalize(-vPos)), 0.0), 32.0);
        col += spec * s * vec3(0.8,0.9,1.0);
        gl_FragColor = vec4(col,1.0);
      }`;
    const vert = `
      varying vec3 vNormal; varying vec2 vUv; varying vec3 vPos;
      void main(){
        vUv = uv; vNormal = normalMatrix * normal;
        vec4 wp = modelViewMatrix * vec4(position,1.0); vPos = wp.xyz;
        gl_Position = projectionMatrix * wp;
      }`;
    return new THREE.ShaderMaterial({ uniforms, vertexShader: vert, fragmentShader: frag });
  }, [textures, sunDir]);

  return (
    <group>
      // Earth body
      <mesh ref={ref}>
        <sphereGeometry args={[6371, detail, detail]} />
        <primitive object={material} attach="material" />
      </mesh>
      {/* Set aside until can get real textures
      // Cloud layer
      <mesh>
        <sphereGeometry args={[6371 * 1.005, 64, 64]} />
        <meshBasicMaterial
          map={textures.clouds}
          transparent
          opacity={0.35}
          depthWrite={false}
        />
      </mesh>
      */}  
      // Thin atmosphere glow
      <mesh>
        <sphereGeometry args={[6371 * 1.02, 64, 64]} />
        <meshBasicMaterial transparent opacity={0.08} side={THREE.BackSide} />
      </mesh>
    </group>
  );
}

// Mars
function Mars() {
  const ref = useRef();
  const marsTexture = useMemo(
    () =>
      new THREE.TextureLoader().load(
        "https://upload.wikimedia.org/wikipedia/commons/4/46/Solarsystemscope_texture_2k_mars.jpg"
      ),
    []
  );
  useFrame(() => {
    if (ref.current) ref.current.rotation.y += 0.0008;
  });
  return (
    <mesh ref={ref} position={[120000, 0, 0]}>
      <sphereGeometry args={[3390, 64, 64]} />
      <meshStandardMaterial map={marsTexture} color="#b25b4c" roughness={1} />
    </mesh>
  );
}

// Single satellite mesh
function Satellite({ position, color = "red", name, isTransmitting = false }) {
  const meshRef = useRef();
  
  // Pulse effect when transmitting
  useFrame((state) => {
    if (meshRef.current && isTransmitting) {
      const pulse = 1 + 0.3 * Math.sin(state.clock.elapsedTime * 8);
      meshRef.current.scale.setScalar(pulse);
    } else if (meshRef.current) {
      meshRef.current.scale.setScalar(1);
    }
  });

  return (
    <group>
      <mesh ref={meshRef} position={position}>
        <sphereGeometry args={[50, 16, 16]} />
        <meshStandardMaterial 
          color={color} 
          emissive={isTransmitting ? "#ffffff" : color} 
          emissiveIntensity={isTransmitting ? 0.8 : 0.5} 
        />
      </mesh>
      {/* Satellite name label */}
      {name && (
        <mesh position={[position[0], position[1] + 150, position[2]]}>
          <planeGeometry args={[200, 50]} />
          <meshBasicMaterial transparent opacity={0.7} color="#000000" />
        </mesh>
      )}
    </group>
  );
}

// Bundle transmission visualization
function BundleTransmissionLines({ satellites }) {
  const [transmissions, setTransmissions] = useState([]);
  
  // Simulate random transmissions for visualization
  useEffect(() => {
    if (satellites.length < 2) return;
    
    const interval = setInterval(() => {
      if (Math.random() < 0.3) { // 30% chance of transmission every interval
        const source = satellites[Math.floor(Math.random() * satellites.length)];
        const dest = satellites[Math.floor(Math.random() * satellites.length)];
        
        if (source !== dest) {
          const transmission = {
            id: Date.now(),
            source: [source.x, source.y, source.z],
            destination: [dest.x, dest.y, dest.z],
            progress: 0,
            startTime: Date.now()
          };
          
          setTransmissions(prev => [...prev.slice(-4), transmission]); // Keep last 5 transmissions
        }
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [satellites]);
  
  // Update transmission progress
  useFrame(() => {
    setTransmissions(prev => 
      prev.map(trans => ({
        ...trans,
        progress: Math.min(1, (Date.now() - trans.startTime) / 3000) // 3 second transmission time
      })).filter(trans => trans.progress < 1)
    );
  });
  
  return (
    <>
      {transmissions.map(trans => {
        const startPos = new THREE.Vector3(...trans.source);
        const endPos = new THREE.Vector3(...trans.destination);
        const currentPos = startPos.clone().lerp(endPos, trans.progress);
        
        return (
          <group key={trans.id}>
            {/* Transmission line */}
            <line>
              <bufferGeometry>
                <bufferAttribute 
                  attach="attributes-position"
                  count={2}
                  array={new Float32Array([
                    ...trans.source,
                    currentPos.x, currentPos.y, currentPos.z
                  ])}
                  itemSize={3}
                />
              </bufferGeometry>
              <lineBasicMaterial color="#00ff00" opacity={0.6} transparent />
            </line>
            
            {/* Moving bundle particle */}
            <mesh position={[currentPos.x, currentPos.y, currentPos.z]}>
              <sphereGeometry args={[25, 8, 8]} />
              <meshBasicMaterial color="#00ff00" emissive="#00ff00" emissiveIntensity={0.5} />
            </mesh>
          </group>
        );
      })}
    </>
  );
}

// Satellite layer (polls Flask API)
function SatelliteLayer({ onUpdate, onStatusChange }) {
  const [satellites, setSatellites] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSatellites = async () => {
      try {
        const res = await fetch("http://localhost:5001/api/satellites");
        if (!res.ok) {
          throw new Error(`API request failed: ${res.status} ${res.statusText}`);
        }
        const data = await res.json();
        const sats = data.satellites || [];
        setSatellites(sats);
        onUpdate && onUpdate(sats);
        setError(null);
        setLoading(false);
        onStatusChange && onStatusChange({ error: null, loading: false, count: sats.length });
      } catch (e) {
        console.error("Failed to fetch satellites:", e);
        setError(e.message);
        setLoading(false);
        onStatusChange && onStatusChange({ error: e.message, loading: false, count: satellites.length });
        // Keep existing satellites on error rather than clearing them
      }
    };
    
    fetchSatellites();
    const id = setInterval(fetchSatellites, 2000); // Reduced frequency for better performance
    return () => clearInterval(id);
  }, [onUpdate]);

  // Show error indicator but keep rendering satellites if we have them
  if (error && satellites.length === 0) {
    console.warn("Satellite API error:", error);
    return null;
  }

  return (
    <>
      {satellites.map((sat, i) => {
        const isMars = sat.ref === "MARS";
        const base = new THREE.Vector3(sat.x, sat.y, sat.z);
        const offset = isMars ? new THREE.Vector3(120000, 0, 0) : new THREE.Vector3(0, 0, 0);
        const p = base.add(offset);
        return (
          <Satellite
            key={sat.name || i}
            position={[p.x, p.y, p.z]}
            color={isMars ? "orange" : "red"}
            name={sat.name}
            isTransmitting={Math.random() < 0.2} // Random transmission state for demo
          />
        );
      })}
      <BundleTransmissionLines satellites={satellites} />
    </>
  );
}

// Follow-camera mode
function FollowCamera({ satellites }) {
  const { camera } = useThree();
  const targetPos = useRef(new THREE.Vector3());
  useFrame(() => {
    if (!satellites || satellites.length === 0) return;
    const s = satellites.find((t) => t.name === "FollowMe") || satellites[0];
    if (!s) return;
    targetPos.current.set(s.x, s.y, s.z);
    const desired = targetPos.current.clone().addScalar(2000);
    camera.position.lerp(desired, 0.02);
    camera.lookAt(targetPos.current);
    events.emit("cameraMove", {
      position: camera.position.clone(),
      target: targetPos.current.clone(),
      fov: camera.fov,
    });
  });
  return null;
}

// Ground-view mode (camera at lat/lon/alt)
function GroundView({ lat = 33.9425, lon = -118.4081, altKm = 0.03 }) {
  const { camera } = useThree();
  const target = new THREE.Vector3(0, 0, 0);
  useFrame(() => {
    const pos = geodeticToECEF(lat, lon, altKm);
    const above = pos.clone().multiplyScalar(1.001);
    camera.position.lerp(above, 0.12);
    camera.lookAt(target);
    events.emit("cameraMove", {
      position: camera.position.clone(),
      target: target.clone(),
      fov: camera.fov,
    });
  });
  return null;
}

// Free-flight controls (WASD + mouse-look)
function FreeFlightControls({ speed = 1500 }) {
  const { camera, gl } = useThree();
  const vel = useRef(new THREE.Vector3());
  const keys = useRef({});

  // Key state
  useEffect(() => {
    const onDown = (e) => (keys.current[e.code] = true);
    const onUp = (e) => (keys.current[e.code] = false);
    window.addEventListener("keydown", onDown);
    window.addEventListener("keyup", onUp);
    return () => {
      window.removeEventListener("keydown", onDown);
      window.removeEventListener("keyup", onUp);
    };
  }, []);

  // Pointer lock + mouse look
  useEffect(() => {
    const el = gl.domElement;
    const onClick = () => el.requestPointerLock?.();
    const onMove = (e) => {
      if (document.pointerLockElement === el) {
        const dx = e.movementX || 0;
        const dy = e.movementY || 0;
        camera.rotation.order = "YXZ";
        camera.rotation.y -= dx * 0.002;
        camera.rotation.x -= dy * 0.002;
        camera.rotation.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, camera.rotation.x));
      }
    };
    el.addEventListener("click", onClick);
    window.addEventListener("mousemove", onMove);
    return () => {
      el.removeEventListener("click", onClick);
      window.removeEventListener("mousemove", onMove);
    };
  }, [camera, gl.domElement]);

  // Movement update
  useFrame((_, dt) => {
    vel.current.set(0, 0, 0);
    if (keys.current["KeyW"]) vel.current.z -= 1;
    if (keys.current["KeyS"]) vel.current.z += 1;
    if (keys.current["KeyA"]) vel.current.x -= 1;
    if (keys.current["KeyD"]) vel.current.x += 1;
    if (keys.current["Space"]) vel.current.y += 1;
    if (keys.current["ShiftLeft"] || keys.current["ShiftRight"]) vel.current.y -= 1;

    if (vel.current.lengthSq() > 0) {
      vel.current.normalize().multiplyScalar(speed * dt);
      // Move in camera local space
      const move = vel.current.clone().applyEuler(camera.rotation);
      camera.position.add(move);
    }
  });

  return null;
}

// Click-to-coordinate handler
function ClickHandler() {
  const { camera, gl } = useThree();
  const pick = useEarthPicking({ camera });
  useEffect(() => {
    const onClick = (e) => {
      const rect = gl.domElement.getBoundingClientRect();
      const ndcX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ndcY = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      const geo = pick(ndcX, ndcY);
      if (geo) {
        console.log("earthClick:", geo);
        events.emit("earthClick", geo);
      }
    };
    gl.domElement.addEventListener("click", onClick);
    return () => gl.domElement.removeEventListener("click", onClick);
  }, [gl, pick]);
  return null;
}

// Camera tween (time-based)
function useCameraTween() {
  const { camera } = useThree();
  const ref = useRef({ t: 0, dur: 1, fromPos: new THREE.Vector3(), toPos: new THREE.Vector3(), fromLook: new THREE.Vector3(), toLook: new THREE.Vector3(), active: false });

  const animateTo = (toPos, toLookAt, durationMs = 1200) => {
    ref.current.fromPos.copy(camera.position);
    ref.current.toPos.copy(toPos);
    ref.current.fromLook = ref.current.fromLook.set(0, 0, -1).applyQuaternion(camera.quaternion).add(camera.position);
    ref.current.toLook.copy(toLookAt);
    ref.current.dur = Math.max(1, durationMs) / 1000;
    ref.current.t = 0;
    ref.current.active = true;
  };

  useFrame((_, dt) => {
    if (!ref.current.active) return;
    ref.current.t += dt;
    const u = Math.min(1, ref.current.t / ref.current.dur);
    const s = u * u * (3 - 2 * u); // smoothstep
    const pos = ref.current.fromPos.clone().lerp(ref.current.toPos, s);
    const look = ref.current.fromLook.clone().lerp(ref.current.toLook, s);
    camera.position.copy(pos);
    camera.lookAt(look);
    if (u >= 1) ref.current.active = false;
  });

  return { animateTo };
}

// Lat/Lon grid overlay on the globe (every 30°)
function LatLonGrid({ radius = 6371, stepDeg = 30, color = "#2a89ff", opacity = 0.25 }) {
  const group = useRef();

  const buildCircle = (r, axis = "lat", segs = 128) => {
    const pts = [];
    for (let i = 0; i <= segs; i++) {
      const t = (i / segs) * Math.PI * 2;
      const x = Math.cos(t), y = Math.sin(t);
      // Start as equatorial circle in XZ plane, then rotate per axis
      pts.push(new THREE.Vector3(r * x, 0, r * y));
    }
    const geom = new THREE.BufferGeometry().setFromPoints(pts);
    if (axis === "lat") geom.rotateX(Math.PI / 2);
    return geom;
  };

  const material = useMemo(() => new THREE.LineBasicMaterial({ color, transparent: true, opacity }), [color, opacity]);

  const lines = useMemo(() => {
    const arr = [];
    // Latitudes (exclude poles)
    for (let lat = -90 + stepDeg; lat < 90; lat += stepDeg) {
      const r = radius * Math.cos(THREE.MathUtils.degToRad(lat));
      const g = buildCircle(r, "lat");
      g.rotateZ(THREE.MathUtils.degToRad(lat));
      arr.push(<lineLoop key={`lat-${lat}`} geometry={g} material={material} />);
    }
    // Longitudes
    for (let lon = 0; lon < 180; lon += stepDeg) {
      const g = buildCircle(radius, "lon");
      g.rotateY(THREE.MathUtils.degToRad(lon));
      arr.push(<lineLoop key={`lon-${lon}`} geometry={g} material={material} />);
      if (lon !== 0) {
        const g2 = buildCircle(radius, "lon");
        g2.rotateY(THREE.MathUtils.degToRad(-lon));
        arr.push(<lineLoop key={`lon--${lon}`} geometry={g2} material={material} />);
      }
    }
    return arr;
  }, [radius, stepDeg, material]);

  return <group ref={group}>{lines}</group>;
}

// Perf test (animated): instanced "satellites" orbiting Earth
// '+' adds 100, '-' removes 100
function PerfField({ initial = 0, baseRadius = 6800, speedScale = 0.05 }) {
  const [count, setCount] = useState(initial);
  const meshRef = useRef();

  // per-instance params
  const phases = useRef([]);      // initial angle
  const omegas = useRef([]);      // angular speed
  const radii  = useRef([]);      // orbital radius
  const incls  = useRef([]);      // inclination (radians)

  const tempObj = useMemo(() => new THREE.Object3D(), []);
  const rotX = useMemo(() => new THREE.Vector3(1,0,0), []);

  // hotkeys
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "+") setCount((c) => Math.min(5000, c + 100));
      if (e.key === "-") setCount((c) => Math.max(0, c - 100));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // ensure param arrays match count
  useEffect(() => {
    const N = count;
    const len = phases.current.length;

    if (N > len) {
      for (let i = len; i < N; i++) {
        // randomize ring, speed, and inclination
        const ring =  (i % 8);                                   // 8 rings
        const r    =  baseRadius + ring * 350 + Math.random()*80;
        const inc  =  THREE.MathUtils.degToRad((ring * 10) + (Math.random()*6 - 3));
        const om   =  speedScale * (6500 / r);                   // slower when farther
        phases.current[i] = Math.random() * Math.PI * 2;
        omegas.current[i] = om;
        radii.current[i]  = r;
        incls.current[i]  = inc;
      }
    } else if (N < len) {
      phases.current.length = N;
      omegas.current.length = N;
      radii.current.length  = N;
      incls.current.length  = N;
    }

    // init matrices once so the buffer exists
    const m = meshRef.current;
    if (m) {
      for (let i = 0; i < N; i++) {
        tempObj.position.set(radii.current[i], 0, 0);
        tempObj.updateMatrix();
        m.setMatrixAt(i, tempObj.matrix);
      }
      m.instanceMatrix.needsUpdate = true;
    }
  }, [count, baseRadius, speedScale, tempObj]);

  // animate orbits around Earth center
  useFrame((_, dt) => {
    const m = meshRef.current;
    if (!m) return;

    for (let i = 0; i < count; i++) {
      // advance phase
      phases.current[i] += omegas.current[i] * dt;

      // start in equatorial plane (x,z), then tilt by inclination
      const r   = radii.current[i];
      const ang = phases.current[i];
      const inc = incls.current[i];

      // position before tilt (equatorial ring)
      tempObj.position.set(Math.cos(ang) * r, 0, Math.sin(ang) * r);
      tempObj.rotation.set(0, 0, 0);

      // tilt orbit plane around X to get inclination
      tempObj.position.applyAxisAngle(rotX, inc);

      // (optional) orient the instance to face outward
      tempObj.lookAt(0, 0, 0);
      tempObj.rotateY(Math.PI);

      tempObj.updateMatrix();
      m.setMatrixAt(i, tempObj.matrix);
    }
    m.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={meshRef} args={[null, null, Math.max(1, count)]}>
      <sphereGeometry args={[30, 8, 8]} />
      <meshBasicMaterial color="#888" />
    </instancedMesh>
  );
}

// Connection status indicator
function ConnectionStatus({ error, loading, satelliteCount }) {
  const status = error ? "error" : loading ? "connecting" : "connected";
  const color = error ? "#ff4444" : loading ? "#ffaa00" : "#44ff44";
  
  return (
    <div style={{
      position: "fixed",
      top: "10px",
      right: "10px", 
      background: "rgba(0,0,0,0.7)",
      color: "white",
      padding: "8px 12px",
      borderRadius: "4px",
      fontSize: "12px",
      fontFamily: "monospace",
      zIndex: 1000
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
        <div style={{
          width: "8px",
          height: "8px", 
          borderRadius: "50%",
          backgroundColor: color
        }} />
        API: {status} {satelliteCount ? `(${satelliteCount} sats)` : ""}
      </div>
    </div>
  );
}

// Satellite Management Panel
function SatelliteManagementPanel({ visible, onClose }) {
  const [constellationInfo, setConstellationInfo] = useState(null);
  const [groundStations, setGroundStations] = useState([]);
  const [timeSpeed, setTimeSpeed] = useState(120);
  const [newSatForm, setNewSatForm] = useState({
    name: "",
    semi_major_axis_km: 7000,
    eccentricity: 0.001,
    inclination_deg: 98.0,
    raan_deg: 0,
    arg_perigee_deg: 0,
    true_anomaly_deg: 0,
    reference_body: "Earth"
  });
  const [newGroundStation, setNewGroundStation] = useState({
    name: "",
    latitude: 0,
    longitude: 0,
    altitude_km: 0,
    planet: "Earth"
  });

  // Load constellation info and ground stations
  useEffect(() => {
    if (visible) {
      fetchConstellationInfo();
      fetchGroundStations();
      fetchTimeSpeed();
    }
  }, [visible]);

  const fetchConstellationInfo = async () => {
    try {
      const response = await fetch("http://localhost:5001/api/constellation-info");
      const data = await response.json();
      setConstellationInfo(data);
    } catch (error) {
      console.error("Failed to fetch constellation info:", error);
    }
  };

  const fetchGroundStations = async () => {
    try {
      const response = await fetch("http://localhost:5001/api/ground-stations");
      const data = await response.json();
      setGroundStations(data.ground_stations || []);
    } catch (error) {
      console.error("Failed to fetch ground stations:", error);
    }
  };

  const fetchTimeSpeed = async () => {
    try {
      const response = await fetch("http://localhost:5001/api/time-speed");
      const data = await response.json();
      setTimeSpeed(data.speed_multiplier);
    } catch (error) {
      console.error("Failed to fetch time speed:", error);
    }
  };

  const handleAddSatellite = async () => {
    try {
      const response = await fetch("http://localhost:5001/api/satellites/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newSatForm)
      });
      const data = await response.json();
      if (data.status === "success") {
        alert(`Satellite ${newSatForm.name} added successfully!`);
        setNewSatForm({
          name: "",
          semi_major_axis_km: 7000,
          eccentricity: 0.001,
          inclination_deg: 98.0,
          raan_deg: 0,
          arg_perigee_deg: 0,
          true_anomaly_deg: 0,
          reference_body: "Earth"
        });
        fetchConstellationInfo();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert(`Failed to add satellite: ${error.message}`);
    }
  };

  const handleAddGroundStation = async () => {
    try {
      const response = await fetch("http://localhost:5001/api/ground-stations/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newGroundStation)
      });
      const data = await response.json();
      if (data.status === "success") {
        alert(`Ground station ${newGroundStation.name} added successfully!`);
        setNewGroundStation({
          name: "",
          latitude: 0,
          longitude: 0,
          altitude_km: 0,
          planet: "Earth"
        });
        fetchGroundStations();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert(`Failed to add ground station: ${error.message}`);
    }
  };

  const handleTimeSpeedChange = async (newSpeed) => {
    try {
      const response = await fetch("http://localhost:5001/api/time-speed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ speed: newSpeed })
      });
      const data = await response.json();
      if (data.status === "success") {
        setTimeSpeed(data.speed_multiplier);
      }
    } catch (error) {
      console.error("Failed to update time speed:", error);
    }
  };

  const handleCSVUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch("http://localhost:5001/api/satellites/load-csv", {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      if (data.status === "success") {
        alert(`Successfully loaded ${data.satellites.length} satellites from CSV!`);
        fetchConstellationInfo();
      } else {
        alert(`Error loading CSV: ${data.error}`);
      }
    } catch (error) {
      alert(`Failed to upload CSV: ${error.message}`);
    }
    event.target.value = '';
  };

  if (!visible) return null;

  const inputStyle = {
    width: "100%",
    padding: "4px 6px",
    margin: "2px 0",
    fontSize: "11px",
    border: "1px solid #555",
    borderRadius: "3px",
    background: "#333",
    color: "white"
  };

  const buttonStyle = {
    background: "#4CAF50",
    border: "none",
    color: "white",
    padding: "6px 12px",
    margin: "4px 2px",
    borderRadius: "3px",
    fontSize: "11px",
    cursor: "pointer"
  };

  return (
    <div style={{
      position: "fixed",
      top: "60px",
      left: "10px",
      background: "rgba(0,0,0,0.9)",
      color: "white",
      padding: "16px",
      borderRadius: "8px",
      fontSize: "12px",
      fontFamily: "monospace",
      zIndex: 1001,
      width: "350px",
      maxHeight: "80vh",
      overflowY: "auto",
      border: "1px solid #555"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <h3 style={{ margin: 0, fontSize: "14px" }}>🛰️ Satellite Management</h3>
        <button onClick={onClose} style={{ ...buttonStyle, background: "#f44336", fontSize: "10px" }}>✕</button>
      </div>

      {/* Time Speed Control */}
      <div style={{ marginBottom: "16px", padding: "8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px" }}>
        <div style={{ fontWeight: "bold", marginBottom: "6px" }}>⏱️ Time Speed Control</div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span>Speed: {timeSpeed}x</span>
          <input
            type="range"
            min="0.1"
            max="1000"
            step="0.1"
            value={timeSpeed}
            onChange={(e) => handleTimeSpeedChange(parseFloat(e.target.value))}
            style={{ flex: 1 }}
          />
        </div>
        <div style={{ fontSize: "10px", color: "#888", marginTop: "4px" }}>
          Drag slider to adjust simulation time speed (0.1x - 1000x)
        </div>
      </div>

      {/* Constellation Info */}
      {constellationInfo && (
        <div style={{ marginBottom: "16px", padding: "8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px" }}>
          <div style={{ fontWeight: "bold", marginBottom: "6px" }}>📊 Current Constellation</div>
          <div>Total Satellites: {constellationInfo.total_satellites}</div>
          <div>LEO: {constellationInfo.constellation_types.LEO}</div>
          <div>MEO: {constellationInfo.constellation_types.MEO}</div> 
          <div>GEO: {constellationInfo.constellation_types.GEO}</div>
          <div>Mars: {constellationInfo.constellation_types.MARS}</div>
          <div>Ground Stations: {constellationInfo.ground_stations.total}</div>
        </div>
      )}

      {/* CSV Upload */}
      <div style={{ marginBottom: "16px", padding: "8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px" }}>
        <div style={{ fontWeight: "bold", marginBottom: "6px" }}>📁 Load Satellites from CSV</div>
        <input
          type="file"
          accept=".csv"
          onChange={handleCSVUpload}
          style={{ ...inputStyle, background: "#444" }}
        />
        <div style={{ fontSize: "10px", color: "#888", marginTop: "4px" }}>
          CSV format: name,semi_major_axis_km,eccentricity,inclination_deg,raan_deg,arg_perigee_deg,true_anomaly_deg,epoch_unix,reference_body
        </div>
      </div>

      {/* Manual Satellite Addition */}
      <div style={{ marginBottom: "16px", padding: "8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px" }}>
        <div style={{ fontWeight: "bold", marginBottom: "6px" }}>➕ Add Satellite Manually</div>
        <input
          type="text"
          placeholder="Satellite Name"
          value={newSatForm.name}
          onChange={(e) => setNewSatForm({...newSatForm, name: e.target.value})}
          style={inputStyle}
        />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px" }}>
          <input
            type="number"
            placeholder="Semi-major axis (km)"
            value={newSatForm.semi_major_axis_km}
            onChange={(e) => setNewSatForm({...newSatForm, semi_major_axis_km: parseFloat(e.target.value)})}
            style={inputStyle}
          />
          <input
            type="number"
            placeholder="Eccentricity"
            step="0.001"
            value={newSatForm.eccentricity}
            onChange={(e) => setNewSatForm({...newSatForm, eccentricity: parseFloat(e.target.value)})}
            style={inputStyle}
          />
          <input
            type="number"
            placeholder="Inclination (deg)"
            value={newSatForm.inclination_deg}
            onChange={(e) => setNewSatForm({...newSatForm, inclination_deg: parseFloat(e.target.value)})}
            style={inputStyle}
          />
          <input
            type="number"
            placeholder="RAAN (deg)"
            value={newSatForm.raan_deg}
            onChange={(e) => setNewSatForm({...newSatForm, raan_deg: parseFloat(e.target.value)})}
            style={inputStyle}
          />
          <input
            type="number"
            placeholder="Arg. Perigee (deg)"
            value={newSatForm.arg_perigee_deg}
            onChange={(e) => setNewSatForm({...newSatForm, arg_perigee_deg: parseFloat(e.target.value)})}
            style={inputStyle}
          />
          <input
            type="number"
            placeholder="True Anomaly (deg)"
            value={newSatForm.true_anomaly_deg}
            onChange={(e) => setNewSatForm({...newSatForm, true_anomaly_deg: parseFloat(e.target.value)})}
            style={inputStyle}
          />
        </div>
        <select
          value={newSatForm.reference_body}
          onChange={(e) => setNewSatForm({...newSatForm, reference_body: e.target.value})}
          style={inputStyle}
        >
          <option value="Earth">Earth</option>
          <option value="Mars">Mars</option>
        </select>
        <button onClick={handleAddSatellite} style={buttonStyle}>Add Satellite</button>
      </div>

      {/* Ground Station Addition */}
      <div style={{ marginBottom: "16px", padding: "8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px" }}>
        <div style={{ fontWeight: "bold", marginBottom: "6px" }}>🏢 Add Ground Station</div>
        <input
          type="text"
          placeholder="Station Name"
          value={newGroundStation.name}
          onChange={(e) => setNewGroundStation({...newGroundStation, name: e.target.value})}
          style={inputStyle}
        />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px" }}>
          <input
            type="number"
            placeholder="Latitude (deg)"
            step="0.0001"
            value={newGroundStation.latitude}
            onChange={(e) => setNewGroundStation({...newGroundStation, latitude: parseFloat(e.target.value)})}
            style={inputStyle}
          />
          <input
            type="number"
            placeholder="Longitude (deg)"
            step="0.0001"
            value={newGroundStation.longitude}
            onChange={(e) => setNewGroundStation({...newGroundStation, longitude: parseFloat(e.target.value)})}
            style={inputStyle}
          />
          <input
            type="number"
            placeholder="Altitude (km)"
            step="0.001"
            value={newGroundStation.altitude_km}
            onChange={(e) => setNewGroundStation({...newGroundStation, altitude_km: parseFloat(e.target.value)})}
            style={inputStyle}
          />
          <select
            value={newGroundStation.planet}
            onChange={(e) => setNewGroundStation({...newGroundStation, planet: e.target.value})}
            style={inputStyle}
          >
            <option value="Earth">Earth</option>
            <option value="Mars">Mars</option>
          </select>
        </div>
        <button onClick={handleAddGroundStation} style={buttonStyle}>Add Ground Station</button>
      </div>

      {/* Ground Stations List */}
      <div style={{ marginBottom: "16px", padding: "8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px" }}>
        <div style={{ fontWeight: "bold", marginBottom: "6px" }}>🌍 Ground Stations ({groundStations.length})</div>
        <div style={{ maxHeight: "120px", overflowY: "auto", fontSize: "10px" }}>
          {groundStations.map((station, i) => (
            <div key={i} style={{ padding: "2px 0", borderBottom: "1px solid #333" }}>
              <strong>{station.name}</strong> ({station.planet})<br/>
              Lat: {station.latitude.toFixed(4)}°, Lon: {station.longitude.toFixed(4)}°
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Experiment Configuration Panel
function ExperimentConfigPanel({ visible, onClose, onRunExperiment }) {
  const [config, setConfig] = useState({
    algorithms: "epidemic,prophet",
    duration_hours: 0.1,
    node_counts: "5,10,15",
    buffer_sizes: "10,20,50",
    ttl_minutes: "60,120,240",
    bundle_rate: 30,
    repetitions: 1
  });

  const handleRunExperiment = async () => {
    const params = new URLSearchParams(config);
    params.set('run_all', 'false');  // Run just E1 for speed
    
    try {
      const response = await fetch(`http://localhost:5001/api/run-experiments?${params}`);
      const data = await response.json();
      
      if (data.status === "completed") {
        console.log("Configured experiment completed:", data);
        alert("Experiment completed! Check console for detailed results.");
        onRunExperiment && onRunExperiment(data);
      } else {
        throw new Error(data.error || "Experiment failed");
      }
    } catch (error) {
      console.error("Experiment error:", error);
      alert(`Experiment failed: ${error.message}`);
    }
  };

  if (!visible) return null;

  const inputStyle = {
    width: "100%",
    padding: "4px 6px",
    margin: "2px 0",
    fontSize: "11px",
    border: "1px solid #555",
    borderRadius: "3px",
    background: "#333",
    color: "white"
  };

  const buttonStyle = {
    background: "#2196F3",
    border: "none",
    color: "white",
    padding: "8px 16px",
    margin: "4px 2px",
    borderRadius: "3px",
    fontSize: "11px",
    cursor: "pointer"
  };

  return (
    <div style={{
      position: "fixed",
      top: "60px",
      right: "10px",
      background: "rgba(0,0,0,0.9)",
      color: "white",
      padding: "16px",
      borderRadius: "8px",
      fontSize: "12px",
      fontFamily: "monospace",
      zIndex: 1001,
      width: "300px",
      border: "1px solid #555"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <h3 style={{ margin: 0, fontSize: "14px" }}>🧪 Experiment Configuration</h3>
        <button onClick={onClose} style={{ ...buttonStyle, background: "#f44336", fontSize: "10px" }}>✕</button>
      </div>

      <div style={{ marginBottom: "12px" }}>
        <label style={{ display: "block", marginBottom: "4px", fontSize: "11px", fontWeight: "bold" }}>
          Routing Algorithms (comma-separated):
        </label>
        <input
          type="text"
          value={config.algorithms}
          onChange={(e) => setConfig({...config, algorithms: e.target.value})}
          style={inputStyle}
          placeholder="epidemic,prophet,spray_wait"
        />
      </div>

      <div style={{ marginBottom: "12px" }}>
        <label style={{ display: "block", marginBottom: "4px", fontSize: "11px", fontWeight: "bold" }}>
          Duration (hours):
        </label>
        <input
          type="number"
          step="0.01"
          value={config.duration_hours}
          onChange={(e) => setConfig({...config, duration_hours: parseFloat(e.target.value)})}
          style={inputStyle}
        />
      </div>

      <div style={{ marginBottom: "12px" }}>
        <label style={{ display: "block", marginBottom: "4px", fontSize: "11px", fontWeight: "bold" }}>
          Node Counts (comma-separated):
        </label>
        <input
          type="text"
          value={config.node_counts}
          onChange={(e) => setConfig({...config, node_counts: e.target.value})}
          style={inputStyle}
          placeholder="5,10,15,25"
        />
      </div>

      <div style={{ marginBottom: "12px" }}>
        <label style={{ display: "block", marginBottom: "4px", fontSize: "11px", fontWeight: "bold" }}>
          Buffer Sizes (MB, comma-separated):
        </label>
        <input
          type="text"
          value={config.buffer_sizes}
          onChange={(e) => setConfig({...config, buffer_sizes: e.target.value})}
          style={inputStyle}
          placeholder="5,20,80"
        />
      </div>

      <div style={{ marginBottom: "12px" }}>
        <label style={{ display: "block", marginBottom: "4px", fontSize: "11px", fontWeight: "bold" }}>
          TTL Values (minutes, comma-separated):
        </label>
        <input
          type="text"
          value={config.ttl_minutes}
          onChange={(e) => setConfig({...config, ttl_minutes: e.target.value})}
          style={inputStyle}
          placeholder="30,120,480"
        />
      </div>

      <div style={{ marginBottom: "12px" }}>
        <label style={{ display: "block", marginBottom: "4px", fontSize: "11px", fontWeight: "bold" }}>
          Bundle Generation Rate (per hour):
        </label>
        <input
          type="number"
          value={config.bundle_rate}
          onChange={(e) => setConfig({...config, bundle_rate: parseInt(e.target.value)})}
          style={inputStyle}
        />
      </div>

      <div style={{ marginBottom: "16px" }}>
        <label style={{ display: "block", marginBottom: "4px", fontSize: "11px", fontWeight: "bold" }}>
          Repetitions:
        </label>
        <input
          type="number"
          min="1"
          max="10"
          value={config.repetitions}
          onChange={(e) => setConfig({...config, repetitions: parseInt(e.target.value)})}
          style={inputStyle}
        />
      </div>

      <button onClick={handleRunExperiment} style={buttonStyle}>
        Run Configured Experiment
      </button>

      <div style={{ marginTop: "12px", fontSize: "10px", color: "#888" }}>
        This will run the E1 protocol comparison experiment with your custom parameters.
        Results will be logged to console and saved to experiment_results folder.
      </div>
    </div>
  );
}

// Enhanced DTN Control Panel
function DTNControlPanel({ onRunSimulation, onRunExperiments, simulationStatus }) {
  const [showSatelliteManager, setShowSatelliteManager] = useState(false);
  const [showExperimentConfig, setShowExperimentConfig] = useState(false);

  return (
    <>
      <div style={{
        position: "fixed",
        top: "10px",
        left: "10px",
        background: "rgba(0,0,0,0.8)",
        color: "white",
        padding: "12px",
        borderRadius: "6px",
        fontSize: "12px",
        fontFamily: "monospace",
        zIndex: 1000,
        minWidth: "200px"
      }}>
        <div style={{ marginBottom: "8px", fontWeight: "bold" }}>
          🛰️ DTN Simulation
        </div>
        
        <button 
          onClick={onRunSimulation}
          disabled={simulationStatus.running}
          style={{
            background: "#4CAF50",
            border: "none",
            color: "white",
            padding: "6px 12px",
            margin: "2px",
            borderRadius: "3px",
            fontSize: "11px",
            cursor: simulationStatus.running ? "not-allowed" : "pointer",
            opacity: simulationStatus.running ? 0.6 : 1
          }}
        >
          {simulationStatus.running ? "Running..." : "Run Simulation"}
        </button>
        
        <button 
          onClick={onRunExperiments}
          disabled={simulationStatus.running}
          style={{
            background: "#2196F3",
            border: "none",
            color: "white", 
            padding: "6px 12px",
            margin: "2px",
            borderRadius: "3px",
            fontSize: "11px",
            cursor: simulationStatus.running ? "not-allowed" : "pointer",
            opacity: simulationStatus.running ? 0.6 : 1
          }}
        >
          Run Experiments
        </button>

        <button 
          onClick={() => setShowSatelliteManager(true)}
          style={{
            background: "#FF9800",
            border: "none",
            color: "white", 
            padding: "6px 12px",
            margin: "2px",
            borderRadius: "3px",
            fontSize: "11px",
            cursor: "pointer"
          }}
        >
          Manage Satellites
        </button>

        <button 
          onClick={() => setShowExperimentConfig(true)}
          style={{
            background: "#9C27B0",
            border: "none",
            color: "white", 
            padding: "6px 12px",
            margin: "2px",
            borderRadius: "3px",
            fontSize: "11px",
            cursor: "pointer"
          }}
        >
          Configure Experiments
        </button>
        
        {simulationStatus.lastResult && (
          <div style={{ marginTop: "8px", fontSize: "10px" }}>
            <div>Last Result:</div>
            <div>Delivery: {simulationStatus.lastResult.delivery_ratio}</div>
            <div>Nodes: {simulationStatus.lastResult.total_nodes}</div>
            <div>Bundles: {simulationStatus.lastResult.bundles_delivered}/{simulationStatus.lastResult.bundles_created}</div>
          </div>
        )}
      </div>

      <SatelliteManagementPanel 
        visible={showSatelliteManager}
        onClose={() => setShowSatelliteManager(false)}
      />
      <ExperimentConfigPanel 
        visible={showExperimentConfig}
        onClose={() => setShowExperimentConfig(false)}
      />
    </>
  );
}

// Main app
export default function App() {
  const [latestSats, setLatestSats] = useState([]);
  const [mode, setMode] = useState("orbital");
  const [apiStatus, setApiStatus] = useState({ error: null, loading: true });
  const [simulationStatus, setSimulationStatus] = useState({ 
    running: false, 
    lastResult: null 
  });

  // DTN Simulation functions
  const runDTNSimulation = async () => {
    setSimulationStatus({ running: true, lastResult: null });
    
    try {
      const response = await fetch("http://localhost:5001/api/run-simulation");
      const data = await response.json();
      
      if (data.status === "completed") {
        setSimulationStatus({ 
          running: false, 
          lastResult: data.summary 
        });
        console.log("Simulation completed:", data.results);
      } else {
        throw new Error(data.error || "Simulation failed");
      }
    } catch (error) {
      console.error("Simulation error:", error);
      setSimulationStatus({ running: false, lastResult: null });
    }
  };

  const runDTNExperiments = async () => {
    setSimulationStatus({ running: true, lastResult: null });
    
    try {
      const response = await fetch("http://localhost:5001/api/run-experiments");
      const data = await response.json();
      
      if (data.status === "completed") {
        setSimulationStatus({ 
          running: false, 
          lastResult: { 
            summary: "Experiments completed",
            details: "Check console for full results"
          }
        });
        console.log("Experiments completed:", data.summary);
        alert("Experiments completed! Check browser console for detailed results.");
      } else {
        throw new Error(data.error || "Experiments failed");
      }
    } catch (error) {
      console.error("Experiments error:", error);
      setSimulationStatus({ running: false, lastResult: null });
    }
  };

  // Hotkeys for camera modes
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "1") setMode("orbital");
      if (e.key === "2") setMode("follow");
      if (e.key === "3") setMode("ground");
      if (e.key === "4") setMode("free");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <>
      <ConnectionStatus 
        error={apiStatus.error} 
        loading={apiStatus.loading} 
        satelliteCount={apiStatus.count} 
      />
      <DTNControlPanel 
        onRunSimulation={() => runDTNSimulation()}
        onRunExperiments={() => runDTNExperiments()}
        simulationStatus={simulationStatus}
      />
      <Canvas
        camera={{ position: [0, 8000, 180000], fov: 60, far: 1000000 }}
        style={{ width: "100vw", height: "100vh", background: "black" }}
      >
        <Stats /> {/* FPS monitor */}

        <ambientLight intensity={0.3} />
        <directionalLight position={[100000, 50000, 50000]} intensity={2} />

        <Earth />
        <LatLonGrid radius={6371} stepDeg={30} opacity={0.18} />
        {/* Perf smoke test (spawn with '+' / remove with '-') */}
        <PerfField initial={0} />
        <Mars />

        <pointLight position={[120000, 10000, 30000]} intensity={0.6} />

        <SatelliteLayer 
          onUpdate={setLatestSats} 
          onStatusChange={setApiStatus}
        />
        <ClickHandler />

        <OrbitControls
          enableZoom
          minDistance={8000}
          maxDistance={400000}
          enabled={mode === "orbital"}
        />
        {mode === "follow" && <FollowCamera satellites={latestSats} />}
        {mode === "ground" && <GroundView />}
        {mode === "free" && <FreeFlightControls />}

        <Stars radius={300000} depth={50} count={5000} factor={4} />
      </Canvas>
    </>
  );
}