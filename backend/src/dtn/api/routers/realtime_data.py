"""
Real-time Simulation Data Router

Provides realistic simulation data for the frontend visualization.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
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
        self.time_acceleration = 3600  # 1 real second = 1 hour sim time
        
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
        return {
            'simulation_id': self.simulation_id,
            'satellites': self.satellites,
            'ground_stations': self.ground_stations,
            'contacts': self.contacts,
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


@router.get("/simulation/{simulation_id}")
async def get_real_time_data(simulation_id: str):
    """Get real-time simulation data."""
    try:
        # Initialize simulation if not exists
        if simulation_id not in active_simulations:
            generator = SimulationDataGenerator(simulation_id)
            active_simulations[simulation_id] = {
                'generator': generator,
                'last_update': datetime.now()
            }
            logger.info(f"Initialized real-time data for simulation {simulation_id}")
        
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