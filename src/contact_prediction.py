"""
Contact Window Prediction Module for DTN Satellite Simulation

This module predicts communication contact windows between satellites and
ground stations, calculates line-of-sight visibility, and manages contact
scheduling for DTN routing.

Pair 2 Implementation Tasks:
- Implement line-of-sight calculations with elevation angle constraints
- Create contact window prediction algorithms for different orbit types
- Add contact quality metrics (duration, max elevation, data rate)
- Integrate with orbital mechanics for real-time contact prediction

Dependencies:
- astropy: pip install astropy
- numpy: pip install numpy
- src.orbital_mechanics: Local orbital mechanics module
"""
from datetime import datetime, UTC
from astropy import units as u
from astropy import coordinates as coord
from astropy.time import Time
import numpy as np
from typing import List, Dict, Tuple, Optional, NamedTuple
from dataclasses import dataclass
import time

from src.orbital_mechanics import (
    OrbitalElements,
    Position3D,
    OrbitalMechanics,
    Velocity3D,
)

@dataclass
class GroundStation:
    """Ground station configuration for contact calculations"""

    name: str
    latitude_deg: float  # -90 to 90
    longitude_deg: float  # -180 to 180
    altitude_m: float  # meters above sea level
    min_elevation_deg: float = 10.0  # minimum elevation for contact
    antenna_diameter_m: float = 10.0
    max_data_rate_mbps: float = 100.0
    e2: float = 6.6943799901377997e-3 # WGS-84 eccentricity squared

    def to_ecef_position(self) -> Position3D:
        """
        Convert ground station location to ECEF coordinates

        Returns:
            Position3D in ECEF coordinate system

        Use WGS84 ellipsoid parameters for accurate conversion
        """
        a = OrbitalMechanics.EARTH_RADIUS * 1000 #convert to meters
        n = a/np.sqrt(1 - (self.e2 * np.sin(np.deg2rad(self.latitude_deg)) ** 2))
        
        x = (n + self.altitude_m) * np.cos(np.deg2rad(self.latitude_deg)) * np.cos(np.deg2rad(self.longitude_deg))
        y = (n + self.altitude_m) * np.cos(np.deg2rad(self.latitude_deg)) * np.sin(np.deg2rad(self.longitude_deg))
        z = ((n + self.altitude_m) * (1 - self.e2)) * np.sin(np.deg2rad(self.latitude_deg))

        return Position3D(x, y, z, coordinate_system="ECEF")


class ContactWindow(NamedTuple):
    """Contact window between satellite and ground station"""

    satellite_id: str
    ground_station: str
    start_time: float  # Unix timestamp
    end_time: float  # Unix timestamp
    duration_seconds: float
    max_elevation_deg: float
    max_data_rate_mbps: float
    average_range_km: float


@dataclass
class ContactQuality:
    """Contact quality metrics at specific time"""

    elevation_deg: float
    azimuth_deg: float
    range_km: float
    data_rate_mbps: float
    signal_strength_db: float
    doppler_shift_hz: float


class ContactPredictor:
    """Predicts contact windows between satellites and ground stations"""

    def __init__(self, orbital_mechanics: OrbitalMechanics):
        """
        Initialize contact predictor

        Args:
            orbital_mechanics: Orbital mechanics calculator instance
        """
        self.orbital_mechanics = orbital_mechanics
        self.ground_stations: Dict[str, GroundStation] = {}

    def add_ground_station(self, station: GroundStation) -> None:
        """Add ground station to contact prediction system"""
        self.ground_stations[station.name] = station

    def calculate_elevation_azimuth(
        self,
        satellite_position: Position3D,
        ground_station: GroundStation,
        timestamp: Time,
    ) -> Tuple[float, float]:
        """
        Calculate elevation and azimuth angles from ground station to satellite

        Args:
            satellite_position: Satellite position in ECI coordinates
            ground_station: Ground station configuration
            timestamp: Astropy time object for coordinate conversion

        Returns:
            Tuple of (elevation_deg, azimuth_deg)

        Steps:
        1. Convert satellite ECI position to ECEF
        2. Convert ground station geodetic to ECEF
        3. Calculate range vector from station to satellite
        4. Transform to topocentric (SEZ) coordinates
        5. Calculate elevation and azimuth angles
        """

        # satellite ECI to ECEF, utilizes GCRS ECI frame
        cartrep = coord.CartesianRepresentation(x=satellite_position.x, y=satellite_position.y, z=satellite_position.z,
                                                unit=u.m)
        gcrs = coord.GCRS(cartrep, obstime=timestamp)
        itrs = gcrs.transform_to(coord.ICRS(obstime=timestamp))  # convert to ECEF frame
        loc = coord.EarthLocation(*itrs.cartesian.cartrep)

        satellite_coordinates = Position3D(loc.lat, loc.lon, loc.height, coordinate_system="ECEF")

        # ground station geodetic to ECEF
        ground_station_coordinates = ground_station.to_ecef_position()

        #calculate range vector, target - observer
        d = np.array([
            satellite_coordinates.x - ground_station_coordinates.x,
            satellite_coordinates.y - ground_station_coordinates.y,
            satellite_coordinates.z - ground_station_coordinates.z,
        ])

        # transform to SEZ coordinates
        sin_lat = np.sin(ground_station_coordinates.x); cos_lat = np.cos(ground_station_coordinates.x)
        sin_lon = np.sin(ground_station_coordinates.y); cos_lon = np.cos(ground_station_coordinates.y)

        R = np.array([
            [sin_lat*cos_lon, sin_lat*sin_lon, -cos_lat],
            [-sin_lon, cos_lon, 0],
            [cos_lat*cos_lon, cos_lat*sin_lon, sin_lat],
        ])

        south, east, zenith = R.dot(d)

        #calculate elevation and azimuth angles
        elevation = np.arctan2(zenith, np.sqrt(south**2 + east**2))
        azimuth = np.arctan2(east, -south)
        #make sure azimuth is within [0,360)
        azimuth = azimuth % (2 * np.pi)
        return np.rad2deg(elevation), np.rad2deg(azimuth)

    def satellite_eci_to_ecef(
            self,
            satellite_position: Position3D,
            timestamp: Time,
    ) -> Position3D:
        """
        Helper function to convert satellite ECI to ECEF
        Args:
            satellite_position: Satellite position in ECI coordinates
            timestamp: Astropy time object for coordinate conversion

        Returns:
            Position3D: Satellite position using ECEF coordinates
        """
        # satellite ECI to ECEF, utilizes GCRS ECI frame
        cartrep = coord.CartesianRepresentation(x=satellite_position.x, y=satellite_position.y, z=satellite_position.z,
                                                unit=u.m)
        gcrs = coord.GCRS(cartrep, obstime=timestamp)
        itrs = gcrs.transform_to(coord.ICRS(obstime=timestamp))  # convert to ECEF frame
        loc = coord.EarthLocation(*itrs.cartesian.cartrep)

        return Position3D(loc.lat, loc.lon, loc.height, coordinate_system="ECEF")

    def calculate_range(
        self,
        satellite_position: Position3D,
        ground_station: GroundStation,
        timestamp: Time,
    ) -> float:
        """
        Calculate range (distance) from ground station to satellite

        Args:
            satellite_position: Satellite position in ECI coordinates
            ground_station: Ground station configuration
            timestamp: Time for coordinate conversion

        Returns:
            Range in meters

        Calculate Euclidean distance between satellite and ground station
        """
        satellite_coordinates = self.satellite_eci_to_ecef(satellite_position, timestamp)

        # ground station geodetic to ECEF
        ground_station_coordinates = ground_station.to_ecef_position()

        # calculate euclidian distance (magnitude of range vector
        x_dist = (satellite_coordinates.x - ground_station_coordinates.x) ** 2
        y_dist = (satellite_coordinates.y - ground_station_coordinates.y) ** 2
        z_dist = (satellite_coordinates.z - ground_station_coordinates.z) ** 2
        return np.sqrt(x_dist + y_dist + z_dist)

    def is_visible(
        self,
        satellite_position: Position3D,
        ground_station: GroundStation,
        timestamp: Time,
    ) -> bool:
        """
        Check if satellite is visible from ground station

        Args:
            satellite_position: Satellite position in ECI coordinates
            ground_station: Ground station configuration
            timestamp: Time for coordinate conversion

        Returns:
            True if satellite is above minimum elevation

        Use elevation angle calculation and compare with minimum elevation
        """
        #get elevation and azimuth
        elevation, azimuth = self.calculate_elevation_azimuth(satellite_position, ground_station, timestamp)

        return elevation > ground_station.min_elevation_deg

    def calculate_contact_quality(
        self,
        satellite_position: Position3D,
        satellite_velocity: Velocity3D,
        ground_station: GroundStation,
        timestamp: Time,
    ) -> ContactQuality:
        """
        Calculate detailed contact quality metrics

        Args:
            satellite_position: Satellite position in ECI
            satellite_velocity: Satellite velocity in ECI
            ground_station: Ground station configuration
            timestamp: Time for calculations

        Returns:
            ContactQuality with all metrics

        Include elevation, azimuth, range, data rate, signal strength, Doppler
        """
        # get elevation and azimuth
        elevation, azimuth = self.calculate_elevation_azimuth(satellite_position, ground_station, timestamp)

        # get magnitude of range vector
        range = self.calculate_range(satellite_position, ground_station, timestamp)

        # calculate doppler - first get satellite and ground station in ECEF coordinates
        satellite_coordinates = self.satellite_eci_to_ecef(satellite_position, timestamp)
        ground_station_coordinates = ground_station.to_ecef_position()

        """

        # compute observer ground station velocity
        omega_vec = np.array([0.0, 0.0, omega_earth])
        v_obs_ecef = np.cross(omega_vec, np.array(r_obs_ecef))

        # relative position and velocity (from observer to satellite)
        rel_r = r_sat_ecef - np.array(r_obs_ecef)
        rel_v = v_sat_ecef - np.array(v_obs_ecef)

        rho = np.linalg.norm(rel_r)
        if rho == 0:
            raise ValueError("Observer and satellite positions coincide (rho == 0).")
        u_los = rel_r / rho

        # radial velocity: projection of relative velocity on LOS
        v_radial = np.dot(rel_v,
                          u_los)  # positive => satellite moving away along LOS of observer? (we'll set convention below)
        # Convention: this dot product yields positive when rel_v has component in same direction as LOS:
        #   LOS points from observer -> satellite.
        #   if v_radial > 0, satellite moving away from observer along LOS (increasing range).
        # Many references want positive v for closing (approaching). To get that convention, flip sign:
        # For user-friendly convention (positive -> approaching), set:
        v_radial_approach = -v_radial

        # Doppler: f_d = (v_radial_approach / c) * f0  (positive -> frequency increase when approaching)
        doppler_hz = (v_radial_approach / c) * carrier_freq_hz
        """


        #TODO:Unsure currently how to calculate data rate and signal strength, currently returns 0
        return ContactQuality(elevation, azimuth, range, 0, 0, )



    def predict_contact_windows(
        self,
        satellite_elements: OrbitalElements,
        satellite_id: str,
        ground_station_name: str,
        start_time: float,
        duration_hours: float,
        time_step_seconds: float = 60,
    ) -> List[ContactWindow]:
        """
        Predict all contact windows between satellite and ground station

        Args:
            satellite_elements: Satellite orbital elements
            satellite_id: Unique satellite identifier
            ground_station_name: Name of ground station
            start_time: Start time for prediction (Unix timestamp)
            duration_hours: Prediction duration in hours
            time_step_seconds: Time step for calculations

        Returns:
            List of ContactWindow objects

        Steps:
        1. Loop through time with specified time step
        2. Propagate satellite orbit at each time step
        3. Check visibility from ground station
        4. Identify contact start/end times
        5. Calculate contact quality metrics
        6. Create ContactWindow objects
        """
        contact_windows = List[ContactWindow]
        time_step = start_time
        MU_EARTH = OrbitalMechanics.EARTH_MU * 1e9 #convert to meters

        #define initial satellite values in meters/radians
        a = satellite_elements.semi_major_axis * 1e3
        e = satellite_elements.eccentricity
        i = np.radians(satellite_elements.inclination)
        raan = np.radians(satellite_elements.raan)
        argp = np.radians(satellite_elements.arg_perigee)
        nu0 = np.radians(satellite_elements.true_anomaly)
        # Mean motion
        n = np.sqrt(MU_EARTH / a ** 3)

        # loop through each time step
        while time_step <= start_time + (duration_hours * 3600):
            #convert UNIX time to astropy Time
            date = datetime.fromtimestamp(time_step, UTC)
            astro_time = Time(date)


            #propogate satellite orbit
            # Initial eccentric anomaly
            E0 = 2 * np.arctan(np.tan(nu0 / 2) * np.sqrt((1 - e) / (1 + e)))
            M0 = E0 - e * np.sin(E0)
            M = M0 + n * dt

            # Solve Kepler’s equation
            E = M
            for _ in range(15):
                E = M + e * np.sin(E)

            # True anomaly and distance
            nu = 2 * np.arctan2(np.sqrt(1 + e) * np.sin(E / 2),
                                np.sqrt(1 - e) * np.cos(E / 2))
            r_mag = a * (1 - e * np.cos(E))

            # Perifocal frame position/velocity
            r_pf = np.array([r_mag * np.cos(nu), r_mag * np.sin(nu), 0])
            v_pf = np.sqrt(MU_EARTH / a) / (1 - e * np.cos(E)) * np.array(
                [-np.sin(E), np.sqrt(1 - e ** 2) * np.cos(E), 0])

            # Rotation matrix perifocal→ECI
            cosO, sinO = np.cos(raan), np.sin(raan)
            cosi, sini = np.cos(i), np.sin(i)
            cosw, sinw = np.cos(argp), np.sin(argp)

            R = np.array([
                [cosO * cosw - sinO * sinw * cosi, -cosO * sinw - sinO * cosw * cosi, sinO * sini],
                [sinO * cosw + cosO * sinw * cosi, -sinO * sinw + cosO * cosw * cosi, -cosO * sini],
                [sinw * sini, cosw * sini, cosi]
            ])

            r_eci = R @ r_pf
            v_eci = R @ v_pf

            satellite_position_eci = Position3D(r_eci[0], r_eci[1], r_eci[2], coordinate_system="ECI")

            #check visibility
            visible = self.is_visible(a, PRESET_GROUND_STATIONS[ground_station_name], astro_time)



        # TODO: Implement this function
        raise NotImplementedError("Pair 2: Implement contact window prediction")

    def predict_all_contacts(
        self,
        constellation: List[Tuple[OrbitalElements, str]],
        start_time: float,
        duration_hours: float,
    ) -> Dict[str, List[ContactWindow]]:
        """
        Predict contacts for entire constellation with all ground stations

        Args:
            constellation: List of (orbital_elements, satellite_id) tuples
            start_time: Start time for prediction
            duration_hours: Prediction duration in hours

        Returns:
            Dictionary mapping ground_station_name to list of ContactWindows

        TODO: Implement constellation-wide contact prediction
        Efficiently calculate contacts for all satellite-ground station pairs
        """
        # TODO: Implement this function
        raise NotImplementedError("Pair 2: Implement constellation contact prediction")

    def get_current_contacts(
        self, constellation: List[Tuple[OrbitalElements, str]], current_time: float
    ) -> Dict[str, List[str]]:
        """
        Get currently active contacts between satellites and ground stations

        Args:
            constellation: List of (orbital_elements, satellite_id) tuples
            current_time: Current time (Unix timestamp)

        Returns:
            Dictionary mapping ground_station_name to list of visible satellite_ids

        TODO: Implement real-time contact checking
        Quickly determine which satellites are currently visible from each station
        """
        # TODO: Implement this function
        raise NotImplementedError("Pair 2: Implement real-time contact checking")


class ContactScheduler:
    """Schedules and manages contact windows for DTN routing"""

    def __init__(self, contact_predictor: ContactPredictor):
        """Initialize contact scheduler"""
        self.contact_predictor = contact_predictor
        self.scheduled_contacts: Dict[str, List[ContactWindow]] = {}

    def schedule_contacts(
        self,
        constellation: List[Tuple[OrbitalElements, str]],
        start_time: float,
        duration_hours: float,
    ) -> None:
        """
        Schedule all contacts for constellation

        Args:
            constellation: List of (orbital_elements, satellite_id) tuples
            start_time: Schedule start time
            duration_hours: Schedule duration

        TODO: Implement contact scheduling
        Generate complete contact schedule for DTN routing algorithms
        """
        # TODO: Implement this function
        raise NotImplementedError("Pair 2: Implement contact scheduling")

    def get_next_contact(
        self, satellite_id: str, ground_station: str, after_time: float
    ) -> Optional[ContactWindow]:
        """
        Get next contact window for satellite-ground station pair

        Args:
            satellite_id: Satellite identifier
            ground_station: Ground station name
            after_time: Find contacts after this time

        Returns:
            Next ContactWindow or None if no contacts found

        TODO: Implement next contact lookup
        Efficiently find upcoming contact windows for routing decisions
        """
        # TODO: Implement this function
        raise NotImplementedError("Pair 2: Implement next contact lookup")

    def export_contact_plan_csv(self, filename: str) -> None:
        """
        Export contact plan to CSV format for external tools

        Args:
            filename: Output CSV filename

        TODO: Implement CSV export
        Create CSV with columns: start_time, end_time, satellite_id, ground_station,
                                 duration, max_elevation, data_rate
        """
        # TODO: Implement this function
        raise NotImplementedError("Pair 2: Implement CSV contact plan export")


# Preset ground station configurations
PRESET_GROUND_STATIONS = {
    "svalbard": GroundStation(
        name="Svalbard",
        latitude_deg=78.92,
        longitude_deg=11.93,
        altitude_m=78,
        min_elevation_deg=5.0,
        antenna_diameter_m=32,
        max_data_rate_mbps=150,
    ),
    "alaska": GroundStation(
        name="Alaska_Fairbanks",
        latitude_deg=64.86,
        longitude_deg=-147.85,
        altitude_m=200,
        min_elevation_deg=10.0,
        antenna_diameter_m=12,
        max_data_rate_mbps=50,
    ),
    "australia": GroundStation(
        name="Australia_Alice",
        latitude_deg=-23.70,
        longitude_deg=133.88,
        altitude_m=545,
        min_elevation_deg=10.0,
        antenna_diameter_m=15,
        max_data_rate_mbps=75,
    ),
    "chile": GroundStation(
        name="Chile_Santiago",
        latitude_deg=-33.45,
        longitude_deg=-70.67,
        altitude_m=520,
        min_elevation_deg=10.0,
        antenna_diameter_m=18,
        max_data_rate_mbps=80,
    ),
}
if __name__ == "__main__":
    unix_timestamp = 1678886400  # March 15, 2023, 00:00:00 UTC
    local_datetime_object = datetime.fromtimestamp(unix_timestamp, UTC)
    t = Time(local_datetime_object)
    print(f"Local datetime: {t}  {local_datetime_object}")

# Example usage and test cases
if __name__ == "__min__":
    """
    Example usage for testing implementations
    Run this after implementing the TODO functions
    """

    # Initialize components
    orbital_calc = OrbitalMechanics()
    contact_pred = ContactPredictor(orbital_calc)

    # Add ground stations
    for station in PRESET_GROUND_STATIONS.values():
        contact_pred.add_ground_station(station)

    # Example satellite (ISS-like orbit)
    satellite_elements = OrbitalElements(
        semi_major_axis=6793.0,
        eccentricity=0.0003,
        inclination=51.6,
        raan=180.0,
        arg_perigee=90.0,
        true_anomaly=0.0,
        epoch=time.time(),
    )

    try:
        # Test contact window prediction
        current_time = time.time()
        contacts = contact_pred.predict_contact_windows(
            satellite_elements,
            "ISS_TEST",
            "svalbard",
            current_time,
            24.0,  # 24 hours
        )
        print(f"Predicted {len(contacts)} contact windows with Svalbard station")

        # Test visibility check
        state = orbital_calc.propagate_orbit(satellite_elements, current_time)
        visible = contact_pred.is_visible(
            state.position, PRESET_GROUND_STATIONS["svalbard"], current_time
        )
        print(f"ISS currently visible from Svalbard: {visible}")

    except NotImplementedError as e:
        print(f"Function not yet implemented: {e}")
