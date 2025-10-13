"""
Orbital Mechanics Module for DTN Satellite Simulation

Provides core orbital mechanics calculations for:
- Satellite position propagation
- Orbital parameter conversions
- Coordinate system transformations (ECI, ECEF, geodetic)

Pair 2 Implementation Tasks:
- Complete all TODO functions with proper orbital mechanics calculations
- Implement SGP4/SDP4 propagation algorithms for realistic satellite motion
- Add coordinate system transformations (ECI, ECEF, geodetic)
- Validate calculations against known satellite data (TLE)

Dependencies to install:
- numpy: pip install numpy
- scipy: pip install scipy
- skyfield: pip install skyfield (for SGP4/TLE support)
"""

import math
from typing import Tuple, List
from dataclasses import dataclass
import time
from skyfield.api import load  # type: ignore
from skyfield.sgp4lib import EarthSatellite  # type: ignore
from flask import Flask, jsonify


@dataclass
class OrbitalElements:
    """Keplerian orbital elements defining a satellite orbit."""

    semi_major_axis: float  # km
    eccentricity: float  # 0-1
    inclination: float  # degrees
    raan: float  # Right Ascension of Ascending Node (degrees)
    arg_perigee: float  # Argument of perigee (degrees)
    true_anomaly: float  # True anomaly (degrees)
    epoch: float  # Unix timestamp of orbital elements


@dataclass
class Position3D:
    """3D position vector in a specified coordinate system."""

    x: float
    y: float
    z: float
    coordinate_system: str = "ECI"

    def magnitude(self) -> float:
        """Calculate vector magnitude."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)


@dataclass
class Velocity3D:
    """3D velocity vector in a specified coordinate system."""

    vx: float
    vy: float
    vz: float
    coordinate_system: str = "ECI"


@dataclass
class StateVector:
    """Combined position and velocity state vector."""

    position: Position3D
    velocity: Velocity3D
    timestamp: float


class OrbitalMechanics:
    """Core orbital mechanics calculations for satellite simulation."""

    # Earth parameters
    EARTH_RADIUS: float = 6378.137  # km (WGS84)
    EARTH_MU: float = 398600.4418  # km³/s²
    EARTH_ROTATION_RATE: float = 7.2921159e-5  # rad/s

    def __init__(self) -> None:
        self.ts = load.timescale()

    def calculate_orbital_period(self, semi_major_axis: float) -> float:
        """
        Compute orbital period using Kepler's third law.

        T = 2 * pi * sqrt(a^3 / mu)

        Args:
            semi_major_axis (float): Semi-major axis (km)

        Returns:
            float: Orbital period (s)
        """
        return 2 * math.pi * math.sqrt(semi_major_axis**3 / self.EARTH_MU)

    def calculate_orbital_velocity(self, r: float, a: float) -> float:
        """
        Compute orbital velocity using the Vis-Viva equation.

        v = sqrt(mu * (2/r - 1/a))

        Args:
            radius (float): Distance from Earth's center (km)
            semi_major_axis (float): Semi-major axis (km)

        Returns:
            float: Orbital velocity (km/s)
        """
        return math.sqrt(self.EARTH_MU * (2.0 / r - 1.0 / a))

    def kepler_to_cartesian(
        self, elements: OrbitalElements, time_offset: float = 0.0
    ) -> StateVector:
        """
        Convert Keplerian orbital elements to Cartesian ECI state vector.

        Uses Newton-Raphson solution to Kepler's equation for eccentric anomaly.

        Args:
            elements (OrbitalElements): Keplerian elements
            time_offset (float): Time since epoch (s)

        Returns:
            StateVector: ECI position and velocity at given time
        """
        a = elements.semi_major_axis
        e = elements.eccentricity
        i = math.radians(elements.inclination)
        raan = math.radians(elements.raan)
        argp = math.radians(elements.arg_perigee)
        nu0 = math.radians(elements.true_anomaly)

        n = math.sqrt(self.EARTH_MU / a**3)
        M = nu0 + n * time_offset

        # Solve Kepler's equation E - e*sin(E) = M
        E = M
        for _ in range(20):
            E -= (E - e * math.sin(E) - M) / (1 - e * math.cos(E))

        nu = 2 * math.atan2(
            math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2)
        )
        r = a * (1 - e * math.cos(E))

        x_orb = r * math.cos(nu)
        y_orb = r * math.sin(nu)

        vx_orb = -math.sqrt(self.EARTH_MU / a) / r * math.sin(E)
        vy_orb = math.sqrt(self.EARTH_MU / a) / r * math.sqrt(1 - e**2) * math.cos(E)

        # Rotation matrices
        cos_raan, sin_raan = math.cos(raan), math.sin(raan)
        cos_i, sin_i = math.cos(i), math.sin(i)
        cos_argp, sin_argp = math.cos(argp), math.sin(argp)

        R11 = cos_raan * cos_argp - sin_raan * sin_argp * cos_i
        R12 = -cos_raan * sin_argp - sin_raan * cos_argp * cos_i
        R21 = sin_raan * cos_argp + cos_raan * sin_argp * cos_i
        R22 = -sin_raan * sin_argp + cos_raan * cos_argp * cos_i
        R31 = sin_argp * sin_i
        R32 = cos_argp * sin_i

        x = R11 * x_orb + R12 * y_orb
        y = R21 * x_orb + R22 * y_orb
        z = R31 * x_orb + R32 * y_orb
        vx = R11 * vx_orb + R12 * vy_orb
        vy = R21 * vx_orb + R22 * vy_orb
        vz = R31 * vx_orb + R32 * vy_orb

        return StateVector(
            Position3D(x, y, z, "ECI"),
            Velocity3D(vx, vy, vz, "ECI"),
            elements.epoch + time_offset,
        )

    def propagate_orbit(
        self, elements: OrbitalElements, target_time: float
    ) -> StateVector:
        """
        Simplified Keplerian orbit propagation.

        Args:
            elements (OrbitalElements): Keplerian elements
            target_time (float): Unix timestamp for propagation

        Returns:
            StateVector: ECI state vector at target_time
        """
        dt = target_time - elements.epoch
        return self.kepler_to_cartesian(elements, dt)

    # ------------------------
    # New TLE/SGP4 integration
    # ------------------------

    def propagate_tle(
        self,
        tle_line1: str,
        tle_line2: str,
        name: str = "TLE Sat",
        ts_time: float | None = None,
    ) -> Tuple[float, float]:
        """
        Propagate a satellite from TLE using SGP4.

        Args:
            tle_line1: First TLE line.
            tle_line2: Second TLE line.
            name: Optional satellite name.
            ts_time: Optional UNIX timestamp; defaults to now.

        Returns:
            Tuple(lat, lon) in degrees.
        """
        satellite = EarthSatellite(tle_line1, tle_line2, name, self.ts)

        if ts_time is None:
            t = self.ts.now()
        else:
            t = self.ts.utc(*time.gmtime(ts_time)[:6])

        geocentric = satellite.at(t)
        subpoint = geocentric.subpoint()
        return subpoint.latitude.degrees, subpoint.longitude.degrees

    def eci_to_ecef(self, eci_position: Position3D, timestamp: float) -> Position3D:
        """
        Convert ECI coordinates to ECEF using Earth rotation.

        Args:
            eci_position (Position3D): Position in ECI frame
            timestamp (float): Unix timestamp

        Returns:
            Position3D: Position in ECEF frame
        """
        theta = self.EARTH_ROTATION_RATE * (timestamp % 86400)
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        x = cos_t * eci_position.x + sin_t * eci_position.y
        y = -sin_t * eci_position.x + cos_t * eci_position.y
        z = eci_position.z
        return Position3D(x, y, z, "ECEF")

    def ecef_to_geodetic(self, ecef_position: Position3D) -> Tuple[float, float, float]:
        """
        Convert ECEF coordinates to geodetic (lat, lon, alt) using spherical Earth.

        Args:
            ecef_position (Position3D): ECEF coordinates

        Returns:
            Tuple[float, float, float]: (latitude in degrees, longitude in degrees,
                altitude in km)
        """
        x, y, z = ecef_position.x, ecef_position.y, ecef_position.z
        lon = math.degrees(math.atan2(y, x))
        r = math.sqrt(x**2 + y**2)
        lat = math.degrees(math.atan2(z, r))
        alt = math.sqrt(x**2 + y**2 + z**2) - self.EARTH_RADIUS
        return lat, lon, alt

    def calculate_ground_track(self, state_vector: StateVector) -> Tuple[float, float]:
        """
        Compute subsatellite ground track latitude and longitude.

        Args:
            state_vector (StateVector): ECI state vector

        Returns:
            Tuple[float, float]: (latitude deg, longitude deg)
        """
        ecef = self.eci_to_ecef(state_vector.position, state_vector.timestamp)
        lat, lon, _ = self.ecef_to_geodetic(ecef)
        return lat, lon


class ConstellationGenerator:
    """Generate satellite constellation configurations"""

    def generate_walker_constellation(
        self,
        total_satellites: int,
        orbital_planes: int,
        altitude_km: float,
        inclination_deg: float,
    ) -> List[OrbitalElements]:
        """TODO: Implement Walker constellation generation"""
        raise NotImplementedError("Pair 2: Implement Walker constellation generation")

    def generate_preset_constellation(self, preset_name: str) -> List[OrbitalElements]:
        """TODO: Implement preset constellation configurations"""
        raise NotImplementedError("Pair 2: Implement preset constellation generation")


# Example usage
# -----------------------------
# API / Test entrypoint (drop-in)
# -----------------------------
if __name__ == "__main__":
    import sys

    # Run: python orbital_mechanics.py api
    if len(sys.argv) > 1 and sys.argv[1].lower() == "api":
        from flask_cors import CORS

        app = Flask(__name__)
        CORS(app)

        orbital_calc = OrbitalMechanics()

        # Example satellites (tweak as you like)
        # Earth-centered (ECI at epoch; propagated each request)
        satellites = {
            "SAT-001": {
                "ele": OrbitalElements(
                    semi_major_axis=6793.0,
                    eccentricity=0.0003,
                    inclination=51.6,
                    raan=180.0,
                    arg_perigee=90.0,
                    true_anomaly=0.0,
                    epoch=time.time(),
                ),
                "ref": "EARTH",
            },
            "SAT-002": {
                "ele": OrbitalElements(
                    semi_major_axis=6871.0,
                    eccentricity=0.0001,
                    inclination=97.6,
                    raan=90.0,
                    arg_perigee=0.0,
                    true_anomaly=180.0,
                    epoch=time.time(),
                ),
                "ref": "EARTH",
            },
            # Treat these as Mars-orbit demo by tagging ref="MARS"
            # (Front-end will offset by Mars mesh position.)
            "SAT-M1": {
                "ele": OrbitalElements(
                    semi_major_axis=3390.0 + 400.0,  # crude LMO radius (km)
                    eccentricity=0.0005,
                    inclination=25.0,
                    raan=30.0,
                    arg_perigee=0.0,
                    true_anomaly=0.0,
                    epoch=time.time(),
                ),
                "ref": "MARS",
            },
            "SAT-M2": {
                "ele": OrbitalElements(
                    semi_major_axis=3390.0 + 700.0,
                    eccentricity=0.0010,
                    inclination=60.0,
                    raan=200.0,
                    arg_perigee=45.0,
                    true_anomaly=180.0,
                    epoch=time.time(),
                ),
                "ref": "MARS",
            },
        }

        @app.route("/api/satellites")
        def get_satellites():
            now = time.time()
            speed = 120.0
            print(f"[API] speed={speed}")

            result = []
            for sat_id, cfg in satellites.items():
                ele = cfg["ele"]
                try:
                    # scale time passed since epoch
                    dt = (now - ele.epoch) * speed
                    target_time = ele.epoch + dt

                    st = orbital_calc.propagate_orbit(ele, target_time)
                    result.append(
                        {
                            "name": sat_id,
                            "x": st.position.x,
                            "y": st.position.y,
                            "z": st.position.z,
                            "ref": cfg.get("ref", "EARTH"),
                            "frame": "ECI",
                        }
                    )
                except Exception as e:
                    print(f"[WARN] {sat_id} propagate error: {e}")
            return jsonify({"satellites": result})

        @app.route("/api/health")
        def health():
            return jsonify({"status": "ok", "satellites": len(satellites)})

        print("=" * 60)
        print("🛰  DTN Satellite API Server")
        print("=" * 60)
        print("GET  /api/health        -> status")
        print("GET  /api/satellites    -> positions (ECEF km)")
        print("Note: 'ref' == 'MARS' will render near your Mars mesh.")
        print("=" * 60)
        app.run(host="0.0.0.0", port=5000, debug=True)

    else:
        # TEST MODE
        print("Running orbital mechanics tests…")
        iss = OrbitalElements(
            semi_major_axis=6793.0,
            eccentricity=0.0003,
            inclination=51.6,
            raan=180.0,
            arg_perigee=90.0,
            true_anomaly=0.0,
            epoch=time.time(),
        )
        omx = OrbitalMechanics()
        period = omx.calculate_orbital_period(iss.semi_major_axis)
        print(f"ISS-like orbital period: {period/60:.1f} min")
        st = omx.propagate_orbit(iss, time.time())
        ecef = omx.eci_to_ecef(st.position, time.time())
        lat, lon, alt = omx.ecef_to_geodetic(ecef)
        print(
            f"ECI pos: ({st.position.x:.1f}, "
            f"{st.position.y:.1f}, "
            f"{st.position.z:.1f}) km"
        )
        print(f"ECEF/ground track: {lat:.2f}°, {lon:.2f}°, alt {alt:.1f} km")
        print("Done.")


# Convenience wrappers for testing
def orbital_period(semi_major_axis: float) -> float:
    return OrbitalMechanics().calculate_orbital_period(semi_major_axis)


def orbital_velocity(radius: float, semi_major_axis: float) -> float:
    return OrbitalMechanics().calculate_orbital_velocity(radius, semi_major_axis)


def keplerian_to_cartesian(
    elements: OrbitalElements, time_offset: float = 0
) -> StateVector:
    """Wrapper for OrbitalMechanics.kepler_to_cartesian"""
    return OrbitalMechanics().kepler_to_cartesian(elements, time_offset)


def ground_track(state_vector: StateVector) -> Tuple[float, float]:
    """Wrapper for OrbitalMechanics.calculate_ground_track"""
    return OrbitalMechanics().calculate_ground_track(state_vector)
