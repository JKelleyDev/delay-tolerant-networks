"""
Real-time Simulation Data Router

Provides realistic simulation data for the frontend visualization.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel
import json
import logging
import math
import random
from datetime import datetime, timedelta

from ..models.base_models import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Global simulation state storage
active_simulations: Dict[str, Dict[str, Any]] = {}

class SimulationDataGenerator:
    """Generates realistic simulation data for DTN networks."""
    
    def __init__(self, simulation_id: str):
        self.simulation_id = simulation_id
        self.start_time = datetime.now()
        self.current_sim_time = 0.0  # Simulation seconds
        self.time_acceleration = 1  # Start at real-time (1x)
        
        # Initialize satellite constellation
        self.satellites = self._generate_satellite_constellation()
        self.ground_stations = self._generate_ground_stations()
        self.contacts = []
        self.bundles = {
            'active': 0,
            'delivered': 0,
            'expired': 0,
            'total_generated': 0
        }
        
        # Network metrics
        self.metrics = {
            'deliveryRatio': 0.85,
            'avgDelay': 120.0,
            'overhead': 1.2,
            'avgBufferUtilization': 0.35,
            'throughput': 125.6,
            'avgSNR': 45.0,
            'linkQuality': 98.5,
            'avgContactDuration': 320.5,
            'dataTransferred': 45600  # bytes
        }
    
    def _generate_satellite_constellation(self) -> Dict[str, Any]:
        """Generate a realistic satellite constellation."""
        satellites = {}
        
        # Generate Starlink-like constellation with proper Walker Star distribution
        num_planes = 8  # Number of orbital planes
        sats_per_plane = 8  # Satellites per plane
        total_sats = num_planes * sats_per_plane
        
        for plane in range(num_planes):
            # Orbital plane parameters
            inclination = 53.0  # Starlink inclination
            raan = (plane / num_planes) * 360.0  # Right Ascension of Ascending Node
            altitude = 550 + random.uniform(-20, 20)  # km with some variation
            
            for sat_in_plane in range(sats_per_plane):
                sat_index = plane * sats_per_plane + sat_in_plane
                if sat_index >= 64:  # Limit total satellites for performance
                    break
                    
                sat_id = f"starlink_sat_{sat_index:03d}"
                
                # Phase satellites within each plane
                mean_anomaly = (sat_in_plane / sats_per_plane) * 360.0
                # Add orbital progression based on time
                orbital_period = 2 * math.pi * math.sqrt((6371 + altitude)**3 / 398600.4418)  # seconds
                time_progression = (self.current_sim_time + plane * 300) * 360.0 / orbital_period  # degrees
                current_anomaly = (mean_anomaly + time_progression) % 360.0
                
                # Convert to radians
                anomaly_rad = math.radians(current_anomaly)
                inclination_rad = math.radians(inclination)
                raan_rad = math.radians(raan)
                
                # Calculate position using proper orbital mechanics
                radius = 6371 + altitude
                
                # Position in orbital plane
                x_orbital = radius * math.cos(anomaly_rad)
                y_orbital = radius * math.sin(anomaly_rad)
                z_orbital = 0
                
                # Transform to ECI coordinates using rotation matrices
                cos_raan = math.cos(raan_rad)
                sin_raan = math.sin(raan_rad)
                cos_inc = math.cos(inclination_rad)
                sin_inc = math.sin(inclination_rad)
                
                # Apply rotations: first about z-axis (RAAN), then about x-axis (inclination)
                x = x_orbital * cos_raan - y_orbital * sin_raan * cos_inc
                y = x_orbital * sin_raan + y_orbital * cos_raan * cos_inc
                z = y_orbital * sin_inc
                
                # Validate coordinates to prevent NaN
                if not all(math.isfinite(coord) for coord in [x, y, z]):
                    # Fallback to distributed positions if calculation fails
                    angle = (sat_index / total_sats) * 2 * math.pi
                    x = 7000 * math.cos(angle)
                    y = 7000 * math.sin(angle) * math.cos(inclination_rad)
                    z = 7000 * math.sin(angle) * math.sin(inclination_rad)
                
                # Calculate orbital velocity (perpendicular to radius vector)
                v_mag = math.sqrt(398600.4418 / radius)  # Circular velocity
                vel_x = -v_mag * math.sin(anomaly_rad) * cos_raan - v_mag * math.cos(anomaly_rad) * sin_raan * cos_inc
                vel_y = -v_mag * math.sin(anomaly_rad) * sin_raan + v_mag * math.cos(anomaly_rad) * cos_raan * cos_inc
                vel_z = v_mag * math.cos(anomaly_rad) * sin_inc
                
                # Buffer utilization (varies by satellite)
                buffer_util = random.uniform(0.1, 0.8)
                bundles_stored = int(buffer_util * 10)  # Max 10 bundles per satellite
                
                satellites[sat_id] = {
                    'position': {'x': x, 'y': y, 'z': z},
                    'velocity': {'x': vel_x, 'y': vel_y, 'z': vel_z},
                    'status': 'active',
                    'buffer_utilization': buffer_util,
                    'bundles_stored': bundles_stored,
                    'contacts': random.randint(0, 3),
                    'altitude': altitude,
                    'inclination': inclination,
                    'raan': raan,
                    'mean_anomaly': current_anomaly,
                    'plane_id': plane,
                    'sat_in_plane': sat_in_plane,
                    'buffer_drop_strategy': random.choice(['oldest', 'largest', 'random', 'shortest_ttl']),
                    'bundles_dropped': random.randint(0, 5)
                }
        
        return satellites
    
    def _generate_ground_stations(self) -> Dict[str, Any]:
        """Generate ground stations."""
        stations = {
            'gs_los_angeles': {
                'name': 'Los Angeles',
                'lat': 34.0522,
                'lon': -118.2437,
                'elevation': 71,
                'antenna_diameter': 3.7,
                'status': 'active'
            },
            'gs_tokyo': {
                'name': 'Tokyo', 
                'lat': 35.6762,
                'lon': 139.6503,
                'elevation': 40,
                'antenna_diameter': 3.7,
                'status': 'active'
            },
            'gs_london': {
                'name': 'London',
                'lat': 51.5074,
                'lon': -0.1278,
                'elevation': 35,
                'antenna_diameter': 3.7,
                'status': 'active'
            }
        }
        return stations
    
    def _generate_contacts(self) -> List[Dict[str, Any]]:
        """Generate realistic contact windows."""
        contacts = []
        current_time = datetime.now()
        
        # Generate contacts between satellites and ground stations
        for sat_id, sat_data in self.satellites.items():
            for gs_id, gs_data in self.ground_stations.items():
                # Calculate if satellite is visible from ground station
                sat_pos = sat_data['position']
                distance = math.sqrt(sat_pos['x']**2 + sat_pos['y']**2 + sat_pos['z']**2)
                
                # Simplified visibility check - increase contact probability for more packet movement
                if distance < 2000 and random.random() < 0.5:  # 50% chance of contact
                    contact_duration = random.uniform(180, 600)  # 3-10 minutes
                    data_rate = random.uniform(50e6, 500e6)  # 50-500 Mbps
                    
                    contact = {
                        'contact_id': f"{sat_id}_{gs_id}_{int(self.current_sim_time)}",
                        'source_id': sat_id,
                        'target_id': gs_id,
                        'start_time': current_time,
                        'end_time': current_time + timedelta(seconds=contact_duration),
                        'duration_seconds': contact_duration,
                        'data_rate': data_rate,
                        'isActive': True,
                        'hasData': random.random() < 0.6,  # 60% chance of data transfer
                        'elevation_angle': random.uniform(10, 80),
                        'distance_km': distance
                    }
                    contacts.append(contact)
        
        # Generate inter-satellite links
        sat_ids = list(self.satellites.keys())
        for i in range(len(sat_ids)):
            for j in range(i+1, min(i+3, len(sat_ids))):  # Connect to 2 nearest satellites
                sat1_id = sat_ids[i]
                sat2_id = sat_ids[j]
                
                if random.random() < 0.6:  # 60% chance of ISL for more inter-satellite traffic
                    contact = {
                        'contact_id': f"{sat1_id}_{sat2_id}_isl",
                        'source_id': sat1_id,
                        'target_id': sat2_id,
                        'start_time': current_time - timedelta(minutes=5),
                        'end_time': current_time + timedelta(minutes=10),
                        'duration_seconds': 900,
                        'data_rate': 100e6,  # 100 Mbps ISL
                        'isActive': random.random() < 0.8, # More active connections
                        'hasData': random.random() < 0.7,  # More data transfers
                        'distance_km': random.uniform(800, 1200)
                    }
                    contacts.append(contact)
        
        return contacts
    
    def update_simulation(self, elapsed_time: float) -> Dict[str, Any]:
        """Update simulation state."""
        self.current_sim_time += elapsed_time * self.time_acceleration
        
        # Update satellite positions using proper orbital mechanics
        for sat_id, sat_data in self.satellites.items():
            altitude = sat_data['altitude']
            inclination = sat_data['inclination']
            raan = sat_data['raan']
            plane_id = sat_data['plane_id']
            
            # Calculate orbital period
            radius = 6371 + altitude
            orbital_period = 2 * math.pi * math.sqrt(radius**3 / 398600.4418)
            
            # Update mean anomaly based on orbital motion
            time_progression = (elapsed_time * self.time_acceleration + plane_id * 300) * 360.0 / orbital_period
            sat_data['mean_anomaly'] = (sat_data['mean_anomaly'] + time_progression) % 360.0
            
            # Convert to radians
            anomaly_rad = math.radians(sat_data['mean_anomaly'])
            inclination_rad = math.radians(inclination)
            raan_rad = math.radians(raan)
            
            # Position in orbital plane
            x_orbital = radius * math.cos(anomaly_rad)
            y_orbital = radius * math.sin(anomaly_rad)
            
            # Transform to ECI coordinates
            cos_raan = math.cos(raan_rad)
            sin_raan = math.sin(raan_rad)
            cos_inc = math.cos(inclination_rad)
            sin_inc = math.sin(inclination_rad)
            
            x = x_orbital * cos_raan - y_orbital * sin_raan * cos_inc
            y = x_orbital * sin_raan + y_orbital * cos_raan * cos_inc
            z = y_orbital * sin_inc
            
            # Validate coordinates to prevent NaN
            if not all(math.isfinite(coord) for coord in [x, y, z]):
                # Fallback to simple circular motion if calculation fails
                fallback_angle = (int(sat_id.split('_')[-1]) / 64.0) * 2 * math.pi
                x = 7000 * math.cos(fallback_angle + self.current_sim_time * 0.001)
                y = 7000 * math.sin(fallback_angle + self.current_sim_time * 0.001) * math.cos(inclination_rad)
                z = 7000 * math.sin(fallback_angle + self.current_sim_time * 0.001) * math.sin(inclination_rad)
            
            sat_data['position'] = {'x': x, 'y': y, 'z': z}
            
            # Update velocity vector
            v_mag = math.sqrt(398600.4418 / radius)
            vel_x = -v_mag * math.sin(anomaly_rad) * cos_raan - v_mag * math.cos(anomaly_rad) * sin_raan * cos_inc
            vel_y = -v_mag * math.sin(anomaly_rad) * sin_raan + v_mag * math.cos(anomaly_rad) * cos_raan * cos_inc
            vel_z = v_mag * math.cos(anomaly_rad) * sin_inc
            sat_data['velocity'] = {'x': vel_x, 'y': vel_y, 'z': vel_z}
            
            # Slowly vary buffer utilization
            sat_data['buffer_utilization'] += random.uniform(-0.05, 0.05)
            sat_data['buffer_utilization'] = max(0.1, min(0.9, sat_data['buffer_utilization']))
            sat_data['bundles_stored'] = int(sat_data['buffer_utilization'] * 10)
        
        # Update contacts
        self.contacts = self._generate_contacts()
        
        # Update bundle statistics
        self.bundles['active'] = sum(1 for contact in self.contacts if contact['hasData'])
        self.bundles['total_generated'] += random.randint(0, 2)
        
        # Simulate some deliveries
        if random.random() < 0.1:  # 10% chance of delivery
            self.bundles['delivered'] += random.randint(1, 3)
            self.bundles['active'] = max(0, self.bundles['active'] - random.randint(1, 2))
        
        # Update metrics with some variation
        self.metrics['deliveryRatio'] += random.uniform(-0.02, 0.02)
        self.metrics['deliveryRatio'] = max(0.7, min(1.0, self.metrics['deliveryRatio']))
        
        self.metrics['avgDelay'] += random.uniform(-5, 5)
        self.metrics['avgDelay'] = max(30, min(300, self.metrics['avgDelay']))
        
        self.metrics['avgBufferUtilization'] = sum(
            sat['buffer_utilization'] for sat in self.satellites.values()
        ) / len(self.satellites)
        
        self.metrics['throughput'] += random.uniform(-10, 10)
        self.metrics['throughput'] = max(50, min(200, self.metrics['throughput']))
        
        self.metrics['dataTransferred'] += random.randint(1000, 5000)
        
        return self.get_current_state()
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current simulation state."""
        # Generate timeline contacts with proper timestamps for the ContactGanttChart
        timeline_contacts = []
        current_time = datetime.now()
        
        # Current contacts with proper timestamps
        for contact in self.contacts:
            timeline_contacts.append({
                **contact,
                'start_time': current_time.isoformat(),
                'end_time': (current_time + timedelta(seconds=contact.get('duration_seconds', 300))).isoformat(),
                'status': 'active' if contact.get('isActive', False) else 'scheduled'
            })
        
        # Add future predicted contacts
        for i in range(15):  # Generate 15 future contacts
            start_time = current_time + timedelta(minutes=random.randint(1, 60))
            duration = random.uniform(180, 600)  # 3-10 minutes
            end_time = start_time + timedelta(seconds=duration)
            
            sat_ids = list(self.satellites.keys())
            if len(sat_ids) >= 2:
                source_sat = random.choice(sat_ids)
                target_sat = random.choice([s for s in sat_ids if s != source_sat])
                
                timeline_contacts.append({
                    'contact_id': f"future_{i}_{int(start_time.timestamp())}",
                    'source_id': source_sat,
                    'target_id': target_sat,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration,
                    'status': 'scheduled',
                    'isActive': False,
                    'hasData': random.random() < 0.4,
                    'elevation_angle': random.uniform(15, 70),
                    'data_rate': random.uniform(50e6, 200e6)
                })
        
        return {
            'simulation_id': self.simulation_id,
            'satellites': self.satellites,
            'ground_stations': self.ground_stations,
            'contacts': self.contacts,  # Current contacts for 3D visualization
            'timelineContacts': timeline_contacts,  # Timeline contacts for ContactGanttChart
            'bundles': self.bundles,
            'metrics': self.metrics,
            'simTime': self._format_sim_time(),
            'timeAcceleration': self.time_acceleration,
            'networkStatus': 'operational',
            'currentSimTime': self.current_sim_time,
            'timestamp': datetime.now().isoformat()
        }
    
    def _format_sim_time(self) -> str:
        """Format simulation time as HH:MM:SS."""
        hours = int(self.current_sim_time // 3600)
        minutes = int((self.current_sim_time % 3600) // 60)
        seconds = int(self.current_sim_time % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def set_time_acceleration(self, acceleration: float) -> bool:
        """Set the time acceleration factor."""
        if acceleration <= 0:
            return False
        
        self.time_acceleration = acceleration
        logger.info(f"Time acceleration changed to {acceleration}x for simulation {self.simulation_id}")
        return True


@router.get("/simulation/{simulation_id}")
async def get_real_time_data(simulation_id: str):
    """Get real-time simulation data."""
    try:
        # Try to get real data from running simulation engine
        try:
            from dtn.api.app import simulation_engines

            if simulation_id in simulation_engines:
                engine = simulation_engines[simulation_id]

                # Check if engine is ready
                if engine.is_running and hasattr(engine, 'satellite_states') and engine.satellite_states:
                    status = engine.get_current_status()

                    # Calculate GMST for ECI to ECEF conversion
                    import math
                    from datetime import datetime as dt
                    j2000_epoch = dt(2000, 1, 1, 12, 0, 0)
                    days_since_j2000 = (engine.current_sim_time - j2000_epoch).total_seconds() / 86400.0
                    gmst = 18.697374558 + 24.06570982441908 * days_since_j2000
                    gmst = (gmst % 24) * 15  # Convert to degrees
                    gmst_rad = math.radians(gmst)
                    cos_gmst, sin_gmst = math.cos(gmst_rad), math.sin(gmst_rad)

                    # Get satellite positions from engine safely - convert ECI to ECEF for visualization
                    satellites = {}
                    for sat_id, sat_state in engine.satellite_states.items():
                        try:
                            # Convert ECI to ECEF for proper Earth-relative visualization
                            eci_x, eci_y, eci_z = sat_state.position
                            ecef_x = cos_gmst * eci_x + sin_gmst * eci_y
                            ecef_y = -sin_gmst * eci_x + cos_gmst * eci_y
                            ecef_z = eci_z

                            # Convert ECEF to Three.js coordinate system:
                            # ECEF: X=prime meridian, Y=90°E, Z=North Pole
                            # Three.js (with Earth texture): Y=North Pole (up), uses lon+180° offset
                            # Frontend formula: x = -(R*sin(phi)*cos(theta)), y = R*cos(phi), z = R*sin(phi)*sin(theta)
                            # where theta = lon + 180°, which negates sin(lon) term
                            three_x = ecef_x
                            three_y = ecef_z   # Z (north pole) becomes Y (up)
                            three_z = -ecef_y  # Y becomes Z, negated to match lon+180° offset

                            satellites[sat_id] = {
                                'position': {'x': three_x, 'y': three_y, 'z': three_z},
                                'velocity': {'x': sat_state.velocity[0], 'y': sat_state.velocity[2], 'z': sat_state.velocity[1]},
                                'status': 'active',
                                'buffer_utilization': len(sat_state.stored_bundles) / 100.0 if sat_state.stored_bundles else 0,
                                'bundles_stored': len(sat_state.stored_bundles) if sat_state.stored_bundles else 0,
                                'contacts': len(sat_state.active_contacts) if sat_state.active_contacts else 0
                            }
                        except Exception as e:
                            logger.warning(f"Error processing satellite {sat_id}: {e}")
                            continue

                    # Get active contacts from engine safely - GROUND STATION CONTACTS ONLY
                    contacts = []
                    if hasattr(engine, 'active_contacts') and engine.active_contacts:
                        for contact_key, contact in engine.active_contacts.items():
                            try:
                                sat_id = getattr(contact, 'satellite_id', 'unknown')
                                gs_id = getattr(contact, 'ground_station_id', 'unknown')
                                # Check if satellite has bundles - this determines hasData
                                sat_has_bundles = False
                                if sat_id in engine.satellite_states:
                                    sat_has_bundles = len(engine.satellite_states[sat_id].stored_bundles) > 0
                                contacts.append({
                                    'contact_id': contact_key,
                                    'source_id': sat_id,
                                    'target_id': gs_id,
                                    'isActive': True,
                                    'hasData': sat_has_bundles,  # True only if satellite has bundles
                                    'data_rate': getattr(contact, 'data_rate_mbps', 100.0),
                                    'type': 'ground_station'  # Mark as ground station contact
                                })
                                logger.debug(f"Ground station contact: {sat_id} -> {gs_id}, hasData={sat_has_bundles}")
                            except Exception as e:
                                logger.warning(f"Error processing contact {contact_key}: {e}")
                                continue

                    # Track satellites with bundles for metrics
                    sat_ids_with_bundles = [
                        sat_id for sat_id, sat_state in engine.satellite_states.items()
                        if sat_state.stored_bundles
                    ]

                    # Log debug info about contacts
                    if len(contacts) > 0:
                        logger.info(f"Active ground station contacts: {len(contacts)}, Satellites with bundles: {len(sat_ids_with_bundles)}")

                    # Calculate total bundles in satellite buffers
                    total_bundles_in_buffers = sum(
                        len(sat_state.stored_bundles) for sat_state in engine.satellite_states.values()
                    )

                    # Get ground stations from engine for visualization
                    ground_stations_data = {}
                    if hasattr(engine, 'ground_stations') and engine.ground_stations:
                        for gs_id, gs in engine.ground_stations.items():
                            try:
                                ground_stations_data[gs_id] = {
                                    'name': getattr(gs, 'name', gs_id),
                                    'lat': gs.position.latitude if hasattr(gs, 'position') else 0,
                                    'lon': gs.position.longitude if hasattr(gs, 'position') else 0,
                                    'elevation': gs.position.altitude * 1000 if hasattr(gs, 'position') else 0,  # Convert km to m
                                    'isSource': gs_id == list(engine.ground_stations.keys())[0],
                                    'isDestination': gs_id == list(engine.ground_stations.keys())[1] if len(engine.ground_stations) > 1 else False
                                }
                            except Exception as e:
                                logger.warning(f"Error processing ground station {gs_id}: {e}")

                    # Build response with real data
                    state = {
                        'satellites': satellites,
                        'ground_stations': ground_stations_data,
                        'contacts': contacts,
                        'bundles': {
                            'generated': status.get('bundles_generated', 0),
                            'active': status.get('bundles_in_transit', 0),
                            'in_buffers': total_bundles_in_buffers,
                            'delivered': status.get('bundles_delivered', 0),
                            'expired': 0
                        },
                        'metrics': {
                            'throughput': status.get('throughput_bundles_per_hour', 0),
                            'avgSNR': 45.0,
                            'linkQuality': 98.0,
                            'deliveryRatio': status.get('delivery_ratio', 0),
                            'avgDelay': status.get('average_delay_seconds', 0),
                            'overhead': status.get('network_overhead_ratio', 1.0),
                            'avgBufferUtilization': status.get('avg_buffer_utilization', 0),
                            'activeContacts': len(engine.active_contacts) if hasattr(engine, 'active_contacts') else 0,
                            'satellitesWithBundles': len(sat_ids_with_bundles)
                        },
                        'simTime': status.get('current_sim_time', '00:00:00'),
                        'timeAcceleration': status.get('time_acceleration', 1),
                        'currentSimTime': status.get('runtime_seconds', 0)
                    }

                    return APIResponse(
                        success=True,
                        message="Real-time data from simulation engine",
                        data=state
                    )
        except ImportError as e:
            logger.warning(f"Could not import simulation_engines: {e}")
        except Exception as e:
            logger.warning(f"Error getting real simulation data: {e}")

        # Fall back to mock visualization data if no running engine or error
        if simulation_id not in active_simulations:
            generator = SimulationDataGenerator(simulation_id)
            active_simulations[simulation_id] = {
                'generator': generator,
                'last_update': datetime.now()
            }
            logger.info(f"Initialized mock real-time data for simulation {simulation_id}")

        # Update simulation state
        sim_data = active_simulations[simulation_id]
        generator = sim_data['generator']
        last_update = sim_data['last_update']

        # Calculate elapsed time
        now = datetime.now()
        elapsed = (now - last_update).total_seconds()

        # Update simulation
        state = generator.update_simulation(elapsed)
        sim_data['last_update'] = now

        return APIResponse(
            success=True,
            message="Real-time data retrieved successfully",
            data=state
        )

    except Exception as e:
        logger.error(f"Error getting real-time data for {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulation/{simulation_id}/contacts")
async def get_contacts_data(simulation_id: str):
    """Get detailed contact information for timeline visualization."""
    try:
        if simulation_id not in active_simulations:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        generator = active_simulations[simulation_id]['generator']
        current_time = datetime.now()
        
        # Generate extended contact plan for timeline
        extended_contacts = []
        
        # Current contacts
        for contact in generator.contacts:
            extended_contacts.append({
                **contact,
                'status': 'active' if contact['isActive'] else 'scheduled',
                'progress': 0.5 if contact['isActive'] else 0.0
            })
        
        # Generate future contacts (next 2 hours)
        for i in range(10):  # 10 future contact windows
            future_time = current_time + timedelta(minutes=random.randint(10, 120))
            duration = random.uniform(300, 900)  # 5-15 minutes
            
            # Pick random satellite and ground station
            sat_ids = list(generator.satellites.keys())
            gs_ids = list(generator.ground_stations.keys())
            
            sat_id = random.choice(sat_ids)
            gs_id = random.choice(gs_ids)
            
            future_contact = {
                'contact_id': f"future_{sat_id}_{gs_id}_{i}",
                'source_id': sat_id,
                'target_id': gs_id,
                'start_time': future_time,
                'end_time': future_time + timedelta(seconds=duration),
                'duration_seconds': duration,
                'data_rate': random.uniform(50e6, 300e6),
                'isActive': False,
                'hasData': random.random() < 0.4,
                'status': 'scheduled',
                'progress': 0.0,
                'elevation_angle': random.uniform(15, 70)
            }
            extended_contacts.append(future_contact)
        
        # Add some potential contacts (opportunities)
        for i in range(5):
            potential_time = current_time + timedelta(minutes=random.randint(30, 180))
            
            sat_id = random.choice(sat_ids)
            gs_id = random.choice(gs_ids)
            
            potential_contact = {
                'contact_id': f"potential_{sat_id}_{gs_id}_{i}",
                'source_id': sat_id,
                'target_id': gs_id,
                'start_time': potential_time,
                'end_time': potential_time + timedelta(seconds=random.uniform(120, 600)),
                'duration_seconds': random.uniform(120, 600),
                'data_rate': random.uniform(10e6, 100e6),
                'isActive': False,
                'hasData': False,
                'status': 'potential',
                'progress': 0.0,
                'elevation_angle': random.uniform(5, 25)  # Lower elevation for potential
            }
            extended_contacts.append(potential_contact)
        
        return APIResponse(
            success=True,
            message="Contact data retrieved successfully", 
            data={
                'contacts': extended_contacts,
                'satellites': generator.satellites,
                'current_time': current_time.isoformat(),
                'time_window_hours': 2
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contacts for {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulation/{simulation_id}/initialize")
async def initialize_simulation(simulation_id: str, config: Optional[Dict[str, Any]] = None):
    """Initialize a new simulation with real data."""
    try:
        if simulation_id in active_simulations:
            return APIResponse(
                success=True,
                message="Simulation already initialized",
                data={"simulation_id": simulation_id}
            )
        
        # Create new simulation
        generator = SimulationDataGenerator(simulation_id)
        active_simulations[simulation_id] = {
            'generator': generator,
            'last_update': datetime.now(),
            'config': config or {}
        }
        
        logger.info(f"Initialized new simulation {simulation_id}")
        
        return APIResponse(
            success=True,
            message="Simulation initialized successfully",
            data={
                "simulation_id": simulation_id,
                "satellites_count": len(generator.satellites),
                "ground_stations_count": len(generator.ground_stations),
                "initial_state": generator.get_current_state()
            }
        )
        
    except Exception as e:
        logger.error(f"Error initializing simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/simulation/{simulation_id}")
async def cleanup_simulation(simulation_id: str):
    """Clean up simulation data."""
    try:
        if simulation_id in active_simulations:
            del active_simulations[simulation_id]
            logger.info(f"Cleaned up simulation {simulation_id}")
        
        return APIResponse(
            success=True,
            message="Simulation cleaned up successfully",
            data={"simulation_id": simulation_id}
        )
        
    except Exception as e:
        logger.error(f"Error cleaning up simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulations/active")
async def list_active_simulations():
    """List all active simulations."""
    try:
        active_list = []
        
        for sim_id, sim_data in active_simulations.items():
            generator = sim_data['generator']
            active_list.append({
                'simulation_id': sim_id,
                'start_time': generator.start_time.isoformat(),
                'current_sim_time': generator.current_sim_time,
                'satellites_count': len(generator.satellites),
                'active_contacts': len([c for c in generator.contacts if c['isActive']])
            })
        
        return APIResponse(
            success=True,
            message="Active simulations retrieved",
            data={
                'active_simulations': active_list,
                'total_count': len(active_list)
            }
        )
        
    except Exception as e:
        logger.error(f"Error listing active simulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AccelerationRequest(BaseModel):
    acceleration: Union[int, float]

@router.post("/simulation/{simulation_id}/acceleration")
async def set_time_acceleration(simulation_id: str, request: AccelerationRequest):
    """Set time acceleration for a simulation."""
    try:
        acceleration = request.acceleration

        if acceleration <= 0:
            raise HTTPException(status_code=400, detail="Acceleration must be a positive number")

        engine_updated = False
        previous_acceleration = 1

        # Try to update real simulation engine if available
        try:
            from dtn.api.app import simulation_engines

            if simulation_id in simulation_engines:
                engine = simulation_engines[simulation_id]
                previous_acceleration = getattr(engine, 'time_acceleration', 1)
                if hasattr(engine, 'set_time_acceleration'):
                    success = engine.set_time_acceleration(float(acceleration))
                    if success:
                        engine_updated = True
                        logger.info(f"Updated real simulation engine acceleration to {acceleration}x")
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Could not update simulation engine: {e}")

        # Also update the visualization generator if it exists
        if simulation_id in active_simulations:
            generator = active_simulations[simulation_id]['generator']
            previous_acceleration = getattr(generator, 'time_acceleration', 1)
            generator.set_time_acceleration(float(acceleration))

        if engine_updated or simulation_id in active_simulations:
            return APIResponse(
                success=True,
                message=f"Time acceleration set to {acceleration}x",
                data={
                    'simulation_id': simulation_id,
                    'acceleration': acceleration,
                    'previous_acceleration': previous_acceleration,
                    'engine_updated': engine_updated
                }
            )
        else:
            # Create a new generator for this simulation if neither exists
            generator = SimulationDataGenerator(simulation_id)
            generator.set_time_acceleration(float(acceleration))
            active_simulations[simulation_id] = {
                'generator': generator,
                'last_update': datetime.now()
            }
            return APIResponse(
                success=True,
                message=f"Time acceleration set to {acceleration}x (new visualization created)",
                data={
                    'simulation_id': simulation_id,
                    'acceleration': acceleration,
                    'previous_acceleration': 1,
                    'engine_updated': False
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting time acceleration for {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))