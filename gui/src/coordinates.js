import * as THREE from "three";

const EARTH_RADIUS = 6371;
const MARS_RADIUS = 3390;

// Return radius for selected planet
export function getPlanetRadius(planet = "earth") {
  return planet.toLowerCase() === "mars" ? MARS_RADIUS : EARTH_RADIUS;
}

// WGS-84 constants
const a = 6378.137;               // semi-major axis (km)
const f = 1 / 298.257223563;
const e2 = 2 * f - f * f;

// Convert geodetic → ECEF
export function geodeticToECEF(latDeg, lonDeg, altKm = 0) {
  const lat = THREE.MathUtils.degToRad(latDeg);
  const lon = THREE.MathUtils.degToRad(lonDeg);
  const sinφ = Math.sin(lat);
  const cosφ = Math.cos(lat);
  const sinλ = Math.sin(lon);
  const cosλ = Math.cos(lon);

  const N = a / Math.sqrt(1 - e2 * sinφ * sinφ);
  const x = (N + altKm) * cosφ * cosλ;
  const y = (N + altKm) * cosφ * sinλ;
  const z = (N * (1 - e2) + altKm) * sinφ;

  return new THREE.Vector3(x, z, -y); // match scene axes
}

// Convert ECEF → geodetic
export function ecefToGeodetic(x, y, z) {
  const X = x, Y = -z, Z = y;
  const b = a * (1 - f);
  const ep2 = (a * a - b * b) / (b * b);
  const p = Math.hypot(X, Y);
  const θ = Math.atan2(Z * a, p * b);
  const sinθ = Math.sin(θ);
  const cosθ = Math.cos(θ);
  const lat = Math.atan2(Z + ep2 * b * sinθ * sinθ, p - e2 * a * cosθ * cosθ);
  const lon = Math.atan2(Y, X);
  const sinφ = Math.sin(lat);
  const N = a / Math.sqrt(1 - e2 * sinφ * sinφ);
  const alt = p / Math.cos(lat) - N;

  return {
    lat: THREE.MathUtils.radToDeg(lat),
    lon: THREE.MathUtils.radToDeg(lon),
    altKm: alt,
  };
}

// Convert ECEF → scene position
export function ecefToPosition(x, y, z) {
  return new THREE.Vector3(x, z, -y);
}

// Screen → geodetic (sphere intersection)
export function useEarthPicking({ camera }) {
  const raycaster = new THREE.Raycaster();
  const sphere = new THREE.Sphere(new THREE.Vector3(0, 0, 0), EARTH_RADIUS);
  return (ndcX, ndcY) => {
    raycaster.setFromCamera({ x: ndcX, y: ndcY }, camera);
    const hit = new THREE.Vector3();
    const ok = raycaster.ray.intersectSphere(sphere, hit);
    if (!ok) return null;
    return ecefToGeodetic(hit.x, hit.y, hit.z);
  };
}