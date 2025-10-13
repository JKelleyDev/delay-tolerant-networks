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
function Satellite({ position, color = "red" }) {
  return (
    <mesh position={position}>
      <sphereGeometry args={[50, 16, 16]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.5} />
    </mesh>
  );
}

// Satellite layer (polls Flask API)
function SatelliteLayer({ onUpdate }) {
  const [satellites, setSatellites] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSatellites = async () => {
      try {
        const res = await fetch("http://localhost:5000/api/satellites");
        if (!res.ok) throw new Error("API request failed");
        const data = await res.json();
        const sats = data.satellites || [];
        setSatellites(sats);
        onUpdate && onUpdate(sats);
        setError(null);
      } catch (e) {
        setError(e.message);
      }
    };
    fetchSatellites();
    const id = setInterval(fetchSatellites, 1000);
    return () => clearInterval(id);
  }, [onUpdate]);

  if (error) return null;

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
          />
        );
      })}
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

// Main app
export default function App() {
  const [latestSats, setLatestSats] = useState([]);
  const [mode, setMode] = useState("orbital");

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
    <Canvas
      camera={{ position: [0, 8000, 180000], fov: 60, far: 1000000 }}
      style={{ width: "100vw", height: "100vh", background: "black" }}
    >
      <Stats /> {/* FPS monitor */}

      <ambientLight intensity={0.3} />
      <directionalLight position={[100000, 50000, 50000]} intensity={2} />

      <Earth />
      <LatLonGrid radius={6371} stepDeg={30} opacity={0.18} />
      // Perf smoke test (spawn with '+' / remove with '-')
      <PerfField initial={0} />+
      <Mars />

      <pointLight position={[120000, 10000, 30000]} intensity={0.6} />

      <SatelliteLayer onUpdate={setLatestSats} />
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
  );
}