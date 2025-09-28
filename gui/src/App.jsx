// src/App.jsx
import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";

// This component draws the Earth and makes it spin
function Earth() {
  const earthRef = useRef();

  // This hook runs every frame (like a game loop)
  useFrame(() => {
    if (earthRef.current) {
      earthRef.current.rotation.y += 0.0015; // spin slowly
    }
  });

  return (
    <mesh ref={earthRef}>
      {/* A sphere shape (radius=1, detail=64x64) */}
      <sphereGeometry args={[1, 64, 64]} />
      {/* Paint it with an Earth texture */}
      <meshStandardMaterial
        map={new THREE.TextureLoader().load(
          "https://threejs.org/examples/textures/land_ocean_ice_cloud_2048.jpg"
        )}
      />
    </mesh>
  );
}

export default function App() {
  return (
    <Canvas
      camera={{ position: [0, 0, 3], fov: 60 }}
      style={{ width: "100vw", height: "100vh", background: "black" }}
    >
      {/* Basic lighting so we can see the Earth */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} intensity={1} />

      {/* Drop in our Earth */}
      <Earth />

      {/* Mouse controls: click and drag to move, scroll to zoom */}
      <OrbitControls enableZoom={true} />
    </Canvas>
  );
}
