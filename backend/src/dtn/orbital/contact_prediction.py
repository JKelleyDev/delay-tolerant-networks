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

from datetime import datetime, timezone
from astropy import units as u  # type: ignore
from astropy import coordinates as coord  # type: ignore
from astropy.time import Time  # type: ignore
import numpy as np
from typing import List, Dict, Tuple, Optional, NamedTuple
from dataclasses import dataclass
import time

try:
    from .orbital_mechanics import (
        OrbitalElements,
        Position3D,
        OrbitalMechanics,
        Velocity3D,
    )
except ImportError:
    # Handle case when module is imported directly
    from orbital_mechanics import (  # type: ignore
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
    e2: float = 6.6943799901377997e-3  # WGS-84 eccentricity squared

    def to_ecef_position(self) -> Position3D:
        """
        Convert ground station location to ECEF coordinates

        Returns:
            Position3D in ECEF coordinate system

        Use WGS84 ellipsoid parameters for accurate conversion
        """
        a = OrbitalMechanics.EARTH_RADIUS * 1000  # convert to meters
        n = a / np.sqrt(1 - (self.e2 * np.sin(np.deg2rad(self.latitude_deg)) ** 2))

        x = (
            (n + self.altitude_m)
            * np.cos(np.deg2rad(self.latitude_deg))
            * np.cos(np.deg2rad(self.longitude_deg))
        )
        y = (
            (n + self.altitude_m)
            * np.cos(np.deg2rad(self.latitude_deg))
            * np.sin(np.deg2rad(self.longitude_deg))
        )
        z = ((n + self.altitude_m) * (1 - self.e2)) * np.sin(
            np.deg2rad(self.latitude_deg)
        )

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
        self.ground_stations: Dict[str, GroundStation] = {
            "hawaii": GroundStation("hawaii", 19.8968, -155.5828, 0),
            "alaska": GroundStation("alaska", 64.2008, -149.4937, 0),
            "svalbard": GroundStation("svalbard", 78.2298, 15.4078, 0),
        }

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
        """
        # Normalize timestamp to Unix float
        if isinstance(timestamp, Time):
            t_unix = timestamp.unix
        else:
            t_unix = float(timestamp)

        # Get satellite ECEF in meters. Prefer fast internal conversion when we have ECI
        # and an OrbitalMechanics instance (avoids heavy astropy transforms).
        if getattr(
            satellite_position, "coordinate_system", ""
        ).upper() == "ECI" and hasattr(self.orbital_mechanics, "eci_to_ecef"):
            # Detect whether satellite_position values are in meters or km by magnitude.
            coords_abs_max = max(
                abs(satellite_position.x),
                abs(satellite_position.y),
                abs(satellite_position.z),
            )
            try:
                ecef_pos = self.orbital_mechanics.eci_to_ecef(
                    satellite_position, t_unix
                )
                # If input coords are large (>1e5), assume meters and don't scale;
                # otherwise treat as km -> m
                if coords_abs_max > 1e5:
                    sat_ecef_arr = np.array([ecef_pos.x, ecef_pos.y, ecef_pos.z])
                else:
                    sat_ecef_arr = (
                        np.array([ecef_pos.x, ecef_pos.y, ecef_pos.z]) * 1000.0
                    )
            except Exception:
                # fallback to astropy-based conversion (returns meters)
                sat_ecef = self.satellite_eci_to_ecef(
                    satellite_position, Time(t_unix, format="unix")
                )
                sat_ecef_arr = np.array([sat_ecef.x, sat_ecef.y, sat_ecef.z])
        else:
            # use astropy-based ECI->ECEF which handles units heuristically
            sat_ecef = self.satellite_eci_to_ecef(
                satellite_position, Time(t_unix, format="unix")
            )
            sat_ecef_arr = np.array([sat_ecef.x, sat_ecef.y, sat_ecef.z])

        # Ground station ECEF in meters
        gs_ecef = ground_station.to_ecef_position()
        gs_ecef_arr = np.array([gs_ecef.x, gs_ecef.y, gs_ecef.z])

        # Topocentric vector from ground station to satellite (meters)
        topo = sat_ecef_arr - gs_ecef_arr
        rng = np.linalg.norm(topo)
        if rng == 0:
            return -90.0, 0.0

        # Convert station lat/lon to radians
        lat = np.deg2rad(ground_station.latitude_deg)
        lon = np.deg2rad(ground_station.longitude_deg)

        # ECEF -> ENU (east, north, up) for the topocentric vector
        dx, dy, dz = topo
        east = -np.sin(lon) * dx + np.cos(lon) * dy
        north = (
            -np.sin(lat) * np.cos(lon) * dx
            - np.sin(lat) * np.sin(lon) * dy
            + np.cos(lat) * dz
        )
        up = (
            np.cos(lat) * np.cos(lon) * dx
            + np.cos(lat) * np.sin(lon) * dy
            + np.sin(lat) * dz
        )

        # Elevation using required formula: elevation = arcsin(up / range)
        elevation_rad = np.arcsin(np.clip(up / rng, -1.0, 1.0))
        elevation = float(np.degrees(elevation_rad))

        # Azimuth using required formula: arctan2(east, north) -> range 0-360
        az_rad = np.arctan2(east, north)
        azimuth = float(np.degrees(az_rad)) % 360.0

        return elevation, azimuth

    def satellite_eci_to_ecef(
        self,
        satellite_position: Position3D,
        timestamp: Time,
    ) -> Position3D:
        """
        Convert satellite ECI to ECEF coordinates in meters.

        Returns:
            Position3D with x, y, z in meters (ECEF)
        """
        # Handle units: OrbitalMechanics returns positions in km (ECI).
        # If coordinate system indicates ECI/GCRS we treat values as km.
        # Heuristic: if coordinates are large (>> Earth's radius) they're likely meters,
        # otherwise treat them as km. This handles tests that construct
        # ECEF-like vectors
        # but label them as ECI.
        coords_abs_max = max(
            abs(satellite_position.x),
            abs(satellite_position.y),
            abs(satellite_position.z),
        )
        if getattr(satellite_position, "coordinate_system", "").upper() in (
            "ECI",
            "GCRS",
        ):
            if coords_abs_max > 1e5:
                unit = u.m
            else:
                unit = u.km
        else:
            unit = u.m

        # Create CartesianRepresentation in GCRS (ECI) frame with correct units
        cartrep = coord.CartesianRepresentation(
            x=satellite_position.x * unit,
            y=satellite_position.y * unit,
            z=satellite_position.z * unit,
        )
        gcrs = coord.GCRS(cartrep, obstime=timestamp)

        # Transform to ITRS (ECEF)
        itrs = gcrs.transform_to(coord.ITRS(obstime=timestamp))

        # Convert to meters for consistency
        x = itrs.x.to(u.m).value
        y = itrs.y.to(u.m).value
        z = itrs.z.to(u.m).value

        # Return ECEF Cartesian coordinates (meters)
        return Position3D(x, y, z, coordinate_system="ECEF")

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
        satellite_coordinates = self.satellite_eci_to_ecef(
            satellite_position, timestamp
        )

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
        # get elevation and azimuth
        elevation, azimuth = self.calculate_elevation_azimuth(
            satellite_position, ground_station, timestamp
        )

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
            ContactQuality with elevation, azimuth, range, data rate,
            signal strength, and Doppler shift.
        """

        # Constants
        c = 3e8  # Speed of light (m/s)
        frequency_hz = 2.2e9  # S-band (example)
        omega_earth = 7.2921159e-5  # Earth's rotation rate (rad/s)

        # Elevation & Azimuth
        elevation, azimuth = self.calculate_elevation_azimuth(
            satellite_position, ground_station, timestamp
        )

        # Range (in meters)
        slant_range_m = self.calculate_range(
            satellite_position, ground_station, timestamp
        )
        slant_range_km = slant_range_m / 1000.0

        # Convert to ECEF for Doppler calculations
        sat_ecef = self.satellite_eci_to_ecef(satellite_position, timestamp)
        gs_ecef = ground_station.to_ecef_position()

        # Convert Position3D objects to numeric arrays (meters)
        sat_ecef_arr = np.array([sat_ecef.x, sat_ecef.y, sat_ecef.z])
        gs_ecef_arr = np.array([gs_ecef.x, gs_ecef.y, gs_ecef.z])

        # Ground station rotational velocity in ECEF
        omega_vec = np.array([0.0, 0.0, omega_earth])
        v_gs_ecef = np.cross(omega_vec, gs_ecef_arr)

        # Satellite ECI → ECEF velocity transformation (approximate)
        # (assume provided velocity is in ECI km/s or m/s depending on source)
        v_sat_eci = np.array(
            [satellite_velocity.vx, satellite_velocity.vy, satellite_velocity.vz]
        )
        # If velocity likely in km/s (orbital mechanics), convert to m/s
        # when positions are in meters
        if abs(v_sat_eci).max() < 1000:
            # assume km/s -> convert to m/s
            v_sat_eci = v_sat_eci * 1000.0

        v_sat_ecef = v_sat_eci - np.cross(omega_vec, sat_ecef_arr)

        # Relative position and velocity
        rel_pos = sat_ecef_arr - gs_ecef_arr
        rel_vel = v_sat_ecef - v_gs_ecef

        # Line-of-sight unit vector
        los_unit = rel_pos / np.linalg.norm(rel_pos)

        # Radial velocity (positive if moving away)
        v_radial = np.dot(rel_vel, los_unit)
        v_radial_approach = -v_radial  # positive = approaching

        # Doppler shift
        doppler_shift_hz = (v_radial_approach / c) * frequency_hz

        # Signal strength estimation (Free-space path loss)
        # FSPL(dB) = 20*log10(d_km) + 20*log10(f_MHz) + 32.44
        d_km = max(slant_range_km, 1e-3)  # prevent log(0)
        f_mhz = frequency_hz / 1e6
        fspl_db = 20 * np.log10(d_km) + 20 * np.log10(f_mhz) + 32.44

        # Normalize to approximate signal level (arbitrary but bounded)
        signal_strength_db = -fspl_db + 200 * np.cos(np.radians(90 - elevation))

        #  Data rate model — proportional to elevation and signal strength
        if elevation > 0:
            data_rate_mbps = max(
                0.0, min(100.0, (signal_strength_db + 50) * (elevation / 90))
            )
        else:
            data_rate_mbps = 0.0

        return ContactQuality(
            elevation_deg=elevation,
            azimuth_deg=azimuth,
            range_km=slant_range_km,
            data_rate_mbps=data_rate_mbps,
            signal_strength_db=signal_strength_db,
            doppler_shift_hz=doppler_shift_hz,
        )

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
        contact_windows: List[ContactWindow] = []
        t = start_time
        end_time = start_time + duration_hours * 3600
        in_contact = False
        contact_start: Optional[float] = None
        max_elevation = 0.0
        total_range = 0.0
        num_steps = 0

        # constants (use km units consistent with OrbitalMechanics)
        MU_EARTH = OrbitalMechanics.EARTH_MU  # km^3/s^2

        # unpack orbital elements (keep km)
        a = satellite_elements.semi_major_axis  # km
        e = satellite_elements.eccentricity
        i = np.radians(satellite_elements.inclination)
        raan = np.radians(satellite_elements.raan)
        argp = np.radians(satellite_elements.arg_perigee)
        nu0 = np.radians(satellite_elements.true_anomaly)

        # ground station object
        gs = self.ground_stations[ground_station_name]

        # mean motion
        n = np.sqrt(MU_EARTH / a**3)

        while t <= end_time:

            # Reduce time step for polar stations
            step = time_step_seconds
            if abs(gs.latitude_deg) > 70:
                step = min(10, time_step_seconds)  # fine steps for high latitude

            timestamp = Time(t, format="unix")  # convert float to astropy Time

            dt = t - start_time  # seconds since start

            # --- Kepler propagation ---
            E0 = 2 * np.arctan(np.tan(nu0 / 2) * np.sqrt((1 - e) / (1 + e)))
            M0 = E0 - e * np.sin(E0)
            M = M0 + n * dt

            # solve Kepler's equation iteratively
            E = M
            for _ in range(15):
                E = M + e * np.sin(E)

            # true anomaly and radius
            nu = 2 * np.arctan2(
                np.sqrt(1 + e) * np.sin(E / 2), np.sqrt(1 - e) * np.cos(E / 2)
            )
            r_mag = a * (1 - e * np.cos(E))

            # perifocal frame (positions in km)
            r_pf = np.array([r_mag * np.cos(nu), r_mag * np.sin(nu), 0])
            v_pf = (
                np.sqrt(MU_EARTH / a)
                / (1 - e * np.cos(E))
                * np.array([-np.sin(E), np.sqrt(1 - e**2) * np.cos(E), 0])
            )

            # rotation to ECI
            cosO, sinO = np.cos(raan), np.sin(raan)
            cosi, sini = np.cos(i), np.sin(i)
            cosw, sinw = np.cos(argp), np.sin(argp)

            R = np.array(
                [
                    [
                        cosO * cosw - sinO * sinw * cosi,
                        -cosO * sinw - sinO * cosw * cosi,
                        sinO * sini,
                    ],
                    [
                        sinO * cosw + cosO * sinw * cosi,
                        -sinO * sinw + cosO * cosw * cosi,
                        -cosO * sini,
                    ],
                    [sinw * sini, cosw * sini, cosi],
                ]
            )

            r_eci = R @ r_pf
            v_eci = R @ v_pf

            # r_eci and v_eci are in km and km/s respectively
            satellite_position = Position3D(
                r_eci[0], r_eci[1], r_eci[2], coordinate_system="ECI"
            )
            satellite_velocity = Velocity3D(
                v_eci[0], v_eci[1], v_eci[2], coordinate_system="ECI"
            )

            # --- Visibility check ---
            elevation, _ = self.calculate_elevation_azimuth(
                satellite_position, gs, timestamp
            )

            # Check for contact start
            if not in_contact and elevation >= gs.min_elevation_deg:
                in_contact = True
                contact_start = t
                max_elevation = elevation
                total_range = (
                    self.calculate_range(satellite_position, gs, timestamp) / 1e3
                )
                num_steps = 1

            # Update contact while visible
            elif in_contact and elevation >= gs.min_elevation_deg:
                max_elevation = max(max_elevation, elevation)
                total_range += (
                    self.calculate_range(satellite_position, gs, timestamp) / 1e3
                )
                num_steps += 1

            # Contact ended
            elif in_contact and elevation < gs.min_elevation_deg:
                if contact_start is not None:
                    contact_end = t
                    avg_range = total_range / num_steps if num_steps > 0 else 0
                    duration_sec = contact_end - contact_start
                    mid_time = contact_start + duration_sec / 2
                    mid_timestamp = Time(mid_time, format="unix")

                    quality = self.calculate_contact_quality(
                        satellite_position, satellite_velocity, gs, mid_timestamp
                    )

                    contact_windows.append(
                        ContactWindow(
                            satellite_id=satellite_id,
                            ground_station=ground_station_name,
                            start_time=contact_start,
                            end_time=contact_end,
                            duration_seconds=duration_sec,
                            max_elevation_deg=max_elevation,
                            max_data_rate_mbps=quality.data_rate_mbps,
                            average_range_km=avg_range,
                        )
                    )

                    in_contact = False

            t += step

        # If loop ended while still in contact, close the window at end_time
        if in_contact and contact_start is not None:
            contact_end = end_time
            avg_range = total_range / num_steps if num_steps > 0 else 0
            duration_sec = contact_end - contact_start
            mid_time = contact_start + duration_sec / 2
            mid_timestamp = Time(mid_time, format="unix")

            quality = self.calculate_contact_quality(
                satellite_position,
                satellite_velocity,
                gs,
                mid_timestamp,
            )

            contact_windows.append(
                ContactWindow(
                    satellite_id=satellite_id,
                    ground_station=ground_station_name,
                    start_time=contact_start,
                    end_time=contact_end,
                    duration_seconds=duration_sec,
                    max_elevation_deg=max_elevation,
                    max_data_rate_mbps=quality.data_rate_mbps,
                    average_range_km=avg_range,
                )
            )

        return contact_windows

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
    local_datetime_object = datetime.fromtimestamp(unix_timestamp, timezone.utc)
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
