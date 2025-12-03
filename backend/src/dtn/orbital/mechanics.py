"""
Orbital Mechanics Implementation

Provides accurate satellite position calculations using Keplerian orbital elements
and coordinate system transformations for realistic satellite mobility.
"""

import numpy as np
import math
from dataclasses import dataclass
from typing import Tuple, List, Optional
from datetime import datetime, timedelta

# Handle Skyfield import with graceful fallback
try:
    from skyfield.api import load, Topos, EarthSatellite
    from skyfield.timelib import Time
    SKYFIELD_AVAILABLE = True
except ImportError:
    SKYFIELD_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning("Skyfield not available - using simplified orbital mechanics")

# Earth constants
EARTH_RADIUS = 6371.0  # km
EARTH_MU = 398600.4418  # km³/s² (Earth's gravitational parameter)
EARTH_J2 = 1.08262668e-3  # J2 perturbation coefficient
EARTH_ROTATION_RATE = 7.2921159e-5  # rad/s


@dataclass
class KeplerianElements:
    """Keplerian orbital elements."""
    semi_major_axis: float  # km
    eccentricity: float
    inclination: float  # degrees
    raan: float  # Right Ascension of Ascending Node (degrees)
    arg_perigee: float  # Argument of perigee (degrees)
    mean_anomaly: float  # degrees
    epoch: datetime


@dataclass
class Position3D:
    """3D position vector."""
    x: float  # km
    y: float  # km
    z: float  # km
    
    def magnitude(self) -> float:
        """Calculate vector magnitude."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self) -> 'Position3D':
        """Return normalized vector."""
        mag = self.magnitude()
        if mag == 0:
            return Position3D(0, 0, 0)
        return Position3D(self.x/mag, self.y/mag, self.z/mag)


@dataclass
class GeodeticPosition:
    """Geodetic coordinates (latitude, longitude, altitude)."""
    latitude: float  # degrees
    longitude: float  # degrees
    altitude: float  # km


@dataclass
class SatelliteState:
    """Complete satellite state information."""
    satellite_id: str
    time: datetime
    position: Position3D  # ECI coordinates
    velocity: Position3D  # ECI coordinates
    geodetic: GeodeticPosition
    orbital_elements: KeplerianElements
    in_eclipse: bool = False


class OrbitalMechanics:
    """Orbital mechanics calculator using Skyfield for accuracy."""
    
    def __init__(self):
        # Load time scale and ephemeris data if Skyfield is available
        if SKYFIELD_AVAILABLE:
            try:
                self.ts = load.timescale()
                self.eph = load('de421.bsp')  # Planetary ephemeris
                self.earth = self.eph['earth']
                self.skyfield_ready = True
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Skyfield initialization failed: {e}")
                self.skyfield_ready = False
        else:
            self.skyfield_ready = False
    
    def propagate_orbit(
        self, 
        elements: KeplerianElements, 
        target_time: datetime
    ) -> SatelliteState:
        """Propagate orbital elements to target time."""
        
        # Calculate time difference
        time_diff = (target_time - elements.epoch).total_seconds()
        
        # Mean motion (rad/s)
        n = math.sqrt(EARTH_MU / elements.semi_major_axis**3)
        
        # Update mean anomaly
        mean_anomaly = elements.mean_anomaly + math.degrees(n * time_diff)
        mean_anomaly = mean_anomaly % 360
        
        # Solve Kepler's equation for eccentric anomaly
        eccentric_anomaly = self._solve_kepler_equation(
            math.radians(mean_anomaly), 
            elements.eccentricity
        )
        
        # Calculate true anomaly
        true_anomaly = self._eccentric_to_true_anomaly(
            eccentric_anomaly, 
            elements.eccentricity
        )
        
        # Calculate position and velocity in orbital plane
        orbital_pos, orbital_vel = self._orbital_to_cartesian(
            elements.semi_major_axis,
            elements.eccentricity,
            true_anomaly,
            n
        )
        
        # Transform to ECI coordinates
        eci_pos, eci_vel = self._orbital_to_eci(
            orbital_pos,
            orbital_vel,
            elements.inclination,
            elements.raan,
            elements.arg_perigee
        )
        
        # Convert to geodetic coordinates
        geodetic = self._eci_to_geodetic(eci_pos, target_time)
        
        # Check eclipse status
        in_eclipse = self._is_in_eclipse(eci_pos, target_time)
        
        # Update orbital elements
        updated_elements = KeplerianElements(
            semi_major_axis=elements.semi_major_axis,
            eccentricity=elements.eccentricity,
            inclination=elements.inclination,
            raan=elements.raan,
            arg_perigee=elements.arg_perigee,
            mean_anomaly=mean_anomaly,
            epoch=target_time
        )
        
        return SatelliteState(
            satellite_id="",  # Will be set by caller
            time=target_time,
            position=eci_pos,
            velocity=eci_vel,
            geodetic=geodetic,
            orbital_elements=updated_elements,
            in_eclipse=in_eclipse
        )
    
    def _solve_kepler_equation(self, mean_anomaly: float, eccentricity: float) -> float:
        """Solve Kepler's equation using Newton-Raphson method."""
        E = mean_anomaly  # Initial guess
        tolerance = 1e-12
        max_iterations = 100
        
        for _ in range(max_iterations):
            f = E - eccentricity * math.sin(E) - mean_anomaly
            fp = 1 - eccentricity * math.cos(E)
            
            delta_E = -f / fp
            E += delta_E
            
            if abs(delta_E) < tolerance:
                break
        
        return E
    
    def _eccentric_to_true_anomaly(self, eccentric_anomaly: float, eccentricity: float) -> float:
        """Convert eccentric anomaly to true anomaly."""
        beta = eccentricity / (1 + math.sqrt(1 - eccentricity**2))
        true_anomaly = eccentric_anomaly + 2 * math.atan(
            beta * math.sin(eccentric_anomaly) / (1 - beta * math.cos(eccentric_anomaly))
        )
        return true_anomaly
    
    def _orbital_to_cartesian(
        self, 
        semi_major_axis: float, 
        eccentricity: float, 
        true_anomaly: float,
        mean_motion: float
    ) -> Tuple[Position3D, Position3D]:
        """Convert orbital elements to position and velocity in orbital plane."""
        
        # Distance from Earth center
        r = semi_major_axis * (1 - eccentricity**2) / (1 + eccentricity * math.cos(true_anomaly))
        
        # Position in orbital plane
        x = r * math.cos(true_anomaly)
        y = r * math.sin(true_anomaly)
        z = 0
        
        # Velocity in orbital plane
        h = math.sqrt(EARTH_MU * semi_major_axis * (1 - eccentricity**2))
        vx = -(EARTH_MU / h) * math.sin(true_anomaly)
        vy = (EARTH_MU / h) * (eccentricity + math.cos(true_anomaly))
        vz = 0
        
        return Position3D(x, y, z), Position3D(vx, vy, vz)
    
    def _orbital_to_eci(
        self,
        orbital_pos: Position3D,
        orbital_vel: Position3D,
        inclination: float,
        raan: float,
        arg_perigee: float
    ) -> Tuple[Position3D, Position3D]:
        """Transform from orbital plane to ECI coordinates."""
        
        # Convert angles to radians
        i = math.radians(inclination)
        omega = math.radians(raan)
        w = math.radians(arg_perigee)
        
        # Rotation matrices
        cos_omega, sin_omega = math.cos(omega), math.sin(omega)
        cos_i, sin_i = math.cos(i), math.sin(i)
        cos_w, sin_w = math.cos(w), math.sin(w)
        
        # Combined rotation matrix elements
        r11 = cos_omega * cos_w - sin_omega * sin_w * cos_i
        r12 = -cos_omega * sin_w - sin_omega * cos_w * cos_i
        r13 = sin_omega * sin_i
        
        r21 = sin_omega * cos_w + cos_omega * sin_w * cos_i
        r22 = -sin_omega * sin_w + cos_omega * cos_w * cos_i
        r23 = -cos_omega * sin_i
        
        r31 = sin_w * sin_i
        r32 = cos_w * sin_i
        r33 = cos_i
        
        # Transform position
        eci_x = r11 * orbital_pos.x + r12 * orbital_pos.y + r13 * orbital_pos.z
        eci_y = r21 * orbital_pos.x + r22 * orbital_pos.y + r23 * orbital_pos.z
        eci_z = r31 * orbital_pos.x + r32 * orbital_pos.y + r33 * orbital_pos.z
        
        # Transform velocity
        eci_vx = r11 * orbital_vel.x + r12 * orbital_vel.y + r13 * orbital_vel.z
        eci_vy = r21 * orbital_vel.x + r22 * orbital_vel.y + r23 * orbital_vel.z
        eci_vz = r31 * orbital_vel.x + r32 * orbital_vel.y + r33 * orbital_vel.z
        
        return Position3D(eci_x, eci_y, eci_z), Position3D(eci_vx, eci_vy, eci_vz)
    
    def _eci_to_geodetic(self, eci_pos: Position3D, time: datetime) -> GeodeticPosition:
        """Convert ECI position to geodetic coordinates."""
        
        # Greenwich Mean Sidereal Time
        j2000_epoch = datetime(2000, 1, 1, 12, 0, 0)
        days_since_j2000 = (time - j2000_epoch).total_seconds() / 86400.0
        gmst = 18.697374558 + 24.06570982441908 * days_since_j2000
        gmst = (gmst % 24) * 15  # Convert to degrees
        gmst_rad = math.radians(gmst)
        
        # Rotate ECI to ECEF
        cos_gmst, sin_gmst = math.cos(gmst_rad), math.sin(gmst_rad)
        ecef_x = cos_gmst * eci_pos.x + sin_gmst * eci_pos.y
        ecef_y = -sin_gmst * eci_pos.x + cos_gmst * eci_pos.y
        ecef_z = eci_pos.z
        
        # Convert ECEF to geodetic using iterative method
        r = math.sqrt(ecef_x**2 + ecef_y**2)
        longitude = math.atan2(ecef_y, ecef_x)
        
        # Earth ellipsoid parameters (WGS84)
        a = 6378.137  # Semi-major axis (km)
        e2 = 0.00669437999014  # First eccentricity squared
        
        # Iterative solution for latitude
        latitude = math.atan2(ecef_z, r)
        for _ in range(5):  # Usually converges quickly
            N = a / math.sqrt(1 - e2 * math.sin(latitude)**2)
            altitude = r / math.cos(latitude) - N
            latitude = math.atan2(ecef_z, r * (1 - e2 * N / (N + altitude)))
        
        # Final altitude calculation
        N = a / math.sqrt(1 - e2 * math.sin(latitude)**2)
        altitude = r / math.cos(latitude) - N
        
        return GeodeticPosition(
            latitude=math.degrees(latitude),
            longitude=math.degrees(longitude),
            altitude=altitude
        )
    
    def _is_in_eclipse(self, eci_pos: Position3D, time: datetime) -> bool:
        """Determine if satellite is in Earth's shadow."""
        
        # Simplified eclipse model - check if Earth blocks line of sight to Sun
        # This would use more sophisticated shadow modeling in production
        
        # Sun vector (simplified - assumes Sun at infinite distance)
        # In reality, would use precise solar ephemeris
        day_of_year = time.timetuple().tm_yday
        solar_longitude = math.radians(360 * day_of_year / 365.25)
        
        sun_vector = Position3D(
            math.cos(solar_longitude),
            math.sin(solar_longitude),
            0
        )
        
        # Check if satellite is on night side of Earth
        sat_distance = eci_pos.magnitude()
        dot_product = (eci_pos.x * sun_vector.x + 
                      eci_pos.y * sun_vector.y + 
                      eci_pos.z * sun_vector.z) / sat_distance
        
        # Simple eclipse check - more sophisticated models would consider
        # umbra/penumbra and Earth's atmospheric effects
        return dot_product < -0.1 and sat_distance < 50000  # Within ~50,000 km
    
    def calculate_contact_geometry(
        self,
        sat_state: SatelliteState,
        ground_lat: float,
        ground_lon: float,
        ground_alt: float = 0.0
    ) -> Tuple[float, float, float]:
        """Calculate elevation, azimuth, and range to ground station."""
        
        # Convert ground station to ECEF
        lat_rad = math.radians(ground_lat)
        lon_rad = math.radians(ground_lon)
        
        a = 6378.137  # Earth semi-major axis (km)
        e2 = 0.00669437999014  # WGS84 eccentricity squared
        N = a / math.sqrt(1 - e2 * math.sin(lat_rad)**2)
        
        gs_ecef_x = (N + ground_alt) * math.cos(lat_rad) * math.cos(lon_rad)
        gs_ecef_y = (N + ground_alt) * math.cos(lat_rad) * math.sin(lon_rad)
        gs_ecef_z = (N * (1 - e2) + ground_alt) * math.sin(lat_rad)
        
        # Convert satellite ECI to ECEF (using current time)
        gmst_rad = self._calculate_gmst(sat_state.time)
        cos_gmst, sin_gmst = math.cos(gmst_rad), math.sin(gmst_rad)
        
        sat_ecef_x = cos_gmst * sat_state.position.x + sin_gmst * sat_state.position.y
        sat_ecef_y = -sin_gmst * sat_state.position.x + cos_gmst * sat_state.position.y
        sat_ecef_z = sat_state.position.z
        
        # Range vector from ground station to satellite
        range_x = sat_ecef_x - gs_ecef_x
        range_y = sat_ecef_y - gs_ecef_y
        range_z = sat_ecef_z - gs_ecef_z
        
        range_magnitude = math.sqrt(range_x**2 + range_y**2 + range_z**2)
        
        # Local topocentric coordinate system
        sin_lat, cos_lat = math.sin(lat_rad), math.cos(lat_rad)
        sin_lon, cos_lon = math.sin(lon_rad), math.cos(lon_rad)
        
        # Transform to topocentric coordinates
        south = -sin_lat * cos_lon * range_x - sin_lat * sin_lon * range_y + cos_lat * range_z
        east = -sin_lon * range_x + cos_lon * range_y
        up = cos_lat * cos_lon * range_x + cos_lat * sin_lon * range_y + sin_lat * range_z
        
        # Calculate elevation and azimuth
        elevation = math.degrees(math.atan2(up, math.sqrt(south**2 + east**2)))
        azimuth = math.degrees(math.atan2(east, south))
        if azimuth < 0:
            azimuth += 360
        
        return elevation, azimuth, range_magnitude
    
    def _calculate_gmst(self, time: datetime) -> float:
        """Calculate Greenwich Mean Sidereal Time."""
        j2000_epoch = datetime(2000, 1, 1, 12, 0, 0)
        days_since_j2000 = (time - j2000_epoch).total_seconds() / 86400.0
        gmst = 18.697374558 + 24.06570982441908 * days_since_j2000
        gmst = (gmst % 24) * 15  # Convert to degrees
        return math.radians(gmst)


def altitude_to_orbital_period(altitude: float) -> float:
    """Calculate orbital period from altitude (simplified circular orbit)."""
    semi_major_axis = EARTH_RADIUS + altitude
    return 2 * math.pi * math.sqrt(semi_major_axis**3 / EARTH_MU)


def create_constellation_elements(
    constellation_type: str,
    num_satellites: int,
    altitude: float,
    inclination: float
) -> List[KeplerianElements]:
    """Create orbital elements for a constellation."""
    
    elements_list = []
    epoch = datetime.now()
    
    if constellation_type == "walker_star":
        # Walker Star constellation
        planes = int(math.sqrt(num_satellites))
        sats_per_plane = num_satellites // planes
        
        for plane in range(planes):
            raan = 360.0 * plane / planes
            
            for sat in range(sats_per_plane):
                mean_anomaly = 360.0 * sat / sats_per_plane
                
                elements = KeplerianElements(
                    semi_major_axis=EARTH_RADIUS + altitude,
                    eccentricity=0.0,  # Circular orbit
                    inclination=inclination,
                    raan=raan,
                    arg_perigee=0.0,
                    mean_anomaly=mean_anomaly,
                    epoch=epoch
                )
                elements_list.append(elements)
    
    elif constellation_type == "single_plane":
        # Single orbital plane
        for sat in range(num_satellites):
            mean_anomaly = 360.0 * sat / num_satellites
            
            elements = KeplerianElements(
                semi_major_axis=EARTH_RADIUS + altitude,
                eccentricity=0.0,
                inclination=inclination,
                raan=0.0,
                arg_perigee=0.0,
                mean_anomaly=mean_anomaly,
                epoch=epoch
            )
            elements_list.append(elements)
    
    return elements_list