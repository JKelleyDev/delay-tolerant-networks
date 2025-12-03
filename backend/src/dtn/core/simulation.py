"""
Core Simulation Engine

Manages DTN simulation lifecycle, coordinates components, and provides
real-time status updates.
"""

import asyncio
import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .bundle import Bundle, BundleStore
from ..api.models.base_models import SimulationConfig, SimulationStatus, NetworkMetrics
try:
    from ..orbital.mechanics import OrbitalMechanics, create_constellation_elements, KeplerianElements
    ORBITAL_MECHANICS_AVAILABLE = True
except ImportError:
    ORBITAL_MECHANICS_AVAILABLE = False
    logger.warning("Orbital mechanics module not available - using simplified positioning")

logger = logging.getLogger(__name__)


class SimulationState(Enum):
    """Internal simulation states."""
    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SimulationStats:
    """Simulation statistics."""
    simulation_id: str
    name: str
    status: SimulationState
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_sim_time: float = 0.0  # Simulation time in seconds
    real_time_elapsed: float = 0.0  # Real time elapsed in seconds
    time_acceleration: float = 1.0
    bundles_generated: int = 0
    bundles_delivered: int = 0
    bundles_expired: int = 0
    active_contacts: int = 0
    total_satellites: int = 0
    total_ground_stations: int = 0


class Simulation:
    """Individual simulation instance."""
    
    def __init__(self, config: SimulationConfig):
        self.id = str(uuid.uuid4())
        self.config = config
        self.state = SimulationState.CREATED
        self.stats = SimulationStats(
            simulation_id=self.id,
            name=config.name,
            status=self.state
        )
        
        # Simulation components
        self.satellites: Dict[str, Any] = {}
        self.ground_stations: Dict[str, Any] = {}
        self.bundle_stores: Dict[str, BundleStore] = {}
        self.contact_windows: List[Any] = []
        
        # Orbital mechanics (if available)
        if ORBITAL_MECHANICS_AVAILABLE:
            self.orbital_mechanics = OrbitalMechanics()
            self.satellite_elements: Dict[str, Any] = {}
        else:
            self.orbital_mechanics = None
            self.satellite_elements: Dict[str, Any] = {}
        
        # Simulation control
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._start_time: Optional[datetime] = None
        
        logger.info(f"Created simulation {self.id}: {config.name}")
    
    async def initialize(self) -> bool:
        """Initialize simulation components."""
        try:
            self.state = SimulationState.INITIALIZING
            logger.info(f"Initializing simulation {self.id}")
            
            # Initialize constellation (placeholder for now)
            await self._initialize_constellation()
            
            # Initialize ground stations
            await self._initialize_ground_stations()
            
            # Initialize routing
            await self._initialize_routing()
            
            # Initialize traffic generation
            await self._initialize_traffic()
            
            self.state = SimulationState.CREATED
            logger.info(f"Simulation {self.id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize simulation {self.id}: {e}")
            self.state = SimulationState.ERROR
            return False
    
    async def start(self) -> bool:
        """Start the simulation."""
        if self.state not in [SimulationState.CREATED, SimulationState.PAUSED]:
            return False
        
        try:
            self.state = SimulationState.RUNNING
            self._running = True
            self._start_time = datetime.now()
            self.stats.start_time = self._start_time
            
            # Start simulation loop
            self._task = asyncio.create_task(self._simulation_loop())
            
            logger.info(f"Started simulation {self.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start simulation {self.id}: {e}")
            self.state = SimulationState.ERROR
            return False
    
    async def pause(self) -> bool:
        """Pause the simulation."""
        if self.state != SimulationState.RUNNING:
            return False
        
        self._running = False
        self.state = SimulationState.PAUSED
        logger.info(f"Paused simulation {self.id}")
        return True
    
    async def stop(self) -> bool:
        """Stop the simulation."""
        if self.state in [SimulationState.STOPPED, SimulationState.COMPLETED]:
            return False
        
        self._running = False
        self.state = SimulationState.STOPPING
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self.state = SimulationState.STOPPED
        self.stats.end_time = datetime.now()
        
        logger.info(f"Stopped simulation {self.id}")
        return True
    
    async def _simulation_loop(self):
        """Main simulation loop."""
        try:
            sim_time = 0.0
            time_step = self.config.time_step
            duration_seconds = self.config.duration * 3600  # Convert hours to seconds
            
            while self._running and sim_time < duration_seconds:
                loop_start = datetime.now()
                
                # Update simulation time
                sim_time += time_step
                self.stats.current_sim_time = sim_time
                
                # Update satellite positions
                await self._update_satellite_positions(sim_time)
                
                # Update contact windows
                await self._update_contacts(sim_time)
                
                # Process routing
                await self._process_routing(sim_time)
                
                # Generate traffic
                await self._generate_traffic(sim_time)
                
                # Update statistics
                await self._update_statistics()
                
                # Sleep for time step (with time acceleration)
                loop_duration = (datetime.now() - loop_start).total_seconds()
                sleep_time = max(0, time_step / self.stats.time_acceleration - loop_duration)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
                # Update real time elapsed
                if self._start_time:
                    self.stats.real_time_elapsed = (datetime.now() - self._start_time).total_seconds()
            
            # Simulation completed
            if sim_time >= duration_seconds:
                self.state = SimulationState.COMPLETED
                logger.info(f"Simulation {self.id} completed")
            
        except asyncio.CancelledError:
            logger.info(f"Simulation {self.id} cancelled")
        except Exception as e:
            logger.error(f"Simulation {self.id} error: {e}")
            self.state = SimulationState.ERROR
    
    async def _initialize_constellation(self):
        """Initialize satellite constellation with proper orbital mechanics."""
        try:
            constellation_id = self.config.constellation_id
            
            if ORBITAL_MECHANICS_AVAILABLE:
                # Create orbital elements for the constellation
                if constellation_id == "starlink":
                    # Starlink constellation parameters
                    num_satellites = 60  # Reduced for performance, represents one shell
                    altitude = 550.0  # km
                    inclination = 53.0  # degrees
                    elements_list = create_constellation_elements(
                        "walker_star", num_satellites, altitude, inclination
                    )
                elif constellation_id == "kuiper":
                    # Project Kuiper constellation
                    num_satellites = 48
                    altitude = 630.0  # km
                    inclination = 51.9  # degrees
                    elements_list = create_constellation_elements(
                        "walker_star", num_satellites, altitude, inclination
                    )
                elif constellation_id == "gps":
                    # GPS constellation
                    num_satellites = 31
                    altitude = 20200.0  # km
                    inclination = 55.0  # degrees
                    elements_list = create_constellation_elements(
                        "walker_star", num_satellites, altitude, inclination
                    )
                else:
                    # Default LEO constellation
                    num_satellites = 20
                    altitude = 400.0  # km
                    inclination = 51.6  # degrees
                    elements_list = create_constellation_elements(
                        "single_plane", num_satellites, altitude, inclination
                    )
                
                self.stats.total_satellites = len(elements_list)
                
                # Initialize satellites with orbital elements
                for i, elements in enumerate(elements_list):
                    sat_id = f"{constellation_id}_sat_{i:03d}"
                    
                    # Calculate initial position
                    initial_state = self.orbital_mechanics.propagate_orbit(elements, datetime.now())
                    
                    self.satellites[sat_id] = {
                        "id": sat_id,
                        "name": f"{constellation_id.title()} {i+1}",
                        "position": {
                            "x": initial_state.position.x,
                            "y": initial_state.position.y,
                            "z": initial_state.position.z
                        },
                        "velocity": {
                            "x": initial_state.velocity.x,
                            "y": initial_state.velocity.y,
                            "z": initial_state.velocity.z
                        },
                        "geodetic": {
                            "latitude": initial_state.geodetic.latitude,
                            "longitude": initial_state.geodetic.longitude,
                            "altitude": initial_state.geodetic.altitude
                        },
                        "status": "active",
                        "contacts": 0,
                        "bundles_stored": 0,
                        "buffer_utilization": 0.0,
                        "buffer_drop_strategy": self.config.buffer_drop_strategy,
                        "bundles_dropped": 0,
                        "in_eclipse": initial_state.in_eclipse
                    }
                    
                    # Store orbital elements for propagation
                    self.satellite_elements[sat_id] = elements
                    
                    # Create bundle store with configured buffer size
                    buffer_size_bytes = self.config.satellite_buffer_size_kb * 1024
                    self.bundle_stores[sat_id] = BundleStore(max_size=buffer_size_bytes)
                    
                logger.info(f"Initialized constellation {constellation_id} with {len(elements_list)} satellites")
            else:
                # Fallback constellation initialization without orbital mechanics
                raise Exception("Using fallback constellation initialization")
            
        except Exception as e:
            logger.warning(f"Using fallback constellation initialization: {e}")
            # Fallback to distributed positioning
            constellation_id = self.config.constellation_id
            num_satellites = 20 if constellation_id == "starlink" else 10
            self.stats.total_satellites = num_satellites
            
            # Create distributed satellite positions using proper orbital distribution
            num_planes = 4
            sats_per_plane = num_satellites // num_planes
            
            for plane in range(num_planes):
                inclination = 53.0  # Starlink-like
                raan = (plane / num_planes) * 360.0
                
                for sat_in_plane in range(sats_per_plane):
                    sat_index = plane * sats_per_plane + sat_in_plane
                    if sat_index >= num_satellites:
                        break
                        
                    sat_id = f"{constellation_id}_sat_{sat_index:03d}"
                    
                    # Distribute satellites properly in orbital planes
                    mean_anomaly = (sat_in_plane / sats_per_plane) * 360.0
                    angle_rad = math.radians(mean_anomaly)
                    inclination_rad = math.radians(inclination)
                    raan_rad = math.radians(raan)
                    
                    radius = 7000  # km
                    
                    # Position in orbital plane
                    x_orbital = radius * math.cos(angle_rad)
                    y_orbital = radius * math.sin(angle_rad)
                    
                    # Transform to ECI coordinates
                    cos_raan = math.cos(raan_rad)
                    sin_raan = math.sin(raan_rad)
                    cos_inc = math.cos(inclination_rad)
                    sin_inc = math.sin(inclination_rad)
                    
                    x = x_orbital * cos_raan - y_orbital * sin_raan * cos_inc
                    y = x_orbital * sin_raan + y_orbital * cos_raan * cos_inc
                    z = y_orbital * sin_inc
                    
                    self.satellites[sat_id] = {
                        "id": sat_id,
                        "name": f"{constellation_id.title()} {sat_index+1}",
                        "position": {"x": x, "y": y, "z": z},
                        "velocity": {"x": -5.0, "y": 5.0, "z": 0},
                        "status": "active",
                        "contacts": 0,
                        "bundles_stored": 0,
                        "buffer_utilization": 0.0,
                        "buffer_drop_strategy": self.config.buffer_drop_strategy or "oldest",
                        "bundles_dropped": 0
                    }
                    
                    buffer_size_bytes = (self.config.satellite_buffer_size_kb or 100) * 1024
                    self.bundle_stores[sat_id] = BundleStore(max_size=buffer_size_bytes)
    
    async def _initialize_ground_stations(self):
        """Initialize ground stations."""
        # Add Los Angeles and Tokyo ground stations as examples
        ground_stations = [
            {"id": "gs_la", "name": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "alt": 0.1},
            {"id": "gs_tokyo", "name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "alt": 0.04}
        ]
        
        for gs in ground_stations:
            self.ground_stations[gs["id"]] = gs
            self.bundle_stores[gs["id"]] = BundleStore(max_size=100*1024*1024)  # 100MB
        
        self.stats.total_ground_stations = len(ground_stations)
    
    async def _initialize_routing(self):
        """Initialize routing algorithm."""
        # Placeholder for routing initialization
        pass
    
    async def _initialize_traffic(self):
        """Initialize traffic generation."""
        # Placeholder for traffic initialization
        pass
    
    async def _update_satellite_positions(self, sim_time: float):
        """Update satellite positions using orbital mechanics."""
        try:
            if ORBITAL_MECHANICS_AVAILABLE and self.orbital_mechanics:
                current_time = datetime.now() + timedelta(seconds=sim_time)
                
                for sat_id, elements in self.satellite_elements.items():
                    if sat_id in self.satellites:
                        # Propagate orbit to current simulation time
                        state = self.orbital_mechanics.propagate_orbit(elements, current_time)
                        
                        # Update satellite position and velocity
                        self.satellites[sat_id]["position"] = {
                            "x": state.position.x,
                            "y": state.position.y,
                            "z": state.position.z
                        }
                        self.satellites[sat_id]["velocity"] = {
                            "x": state.velocity.x,
                            "y": state.velocity.y,
                            "z": state.velocity.z
                        }
                        self.satellites[sat_id]["geodetic"] = {
                            "latitude": state.geodetic.latitude,
                            "longitude": state.geodetic.longitude,
                            "altitude": state.geodetic.altitude
                        }
                        self.satellites[sat_id]["in_eclipse"] = state.in_eclipse
            else:
                # Fallback: simple but distributed orbital motion
                for sat_index, (sat_id, sat_data) in enumerate(self.satellites.items()):
                    if "position" in sat_data:
                        # Use orbital motion that maintains distribution
                        angle_increment = 0.0005 * (1 + sat_index * 0.1)  # Slightly different speeds
                        current_radius = math.sqrt(sat_data["position"]["x"]**2 + sat_data["position"]["y"]**2 + sat_data["position"]["z"]**2)
                        
                        # Preserve the orbital plane by rotating around the same inclination
                        current_angle = math.atan2(sat_data["position"]["z"], sat_data["position"]["x"])
                        new_angle = current_angle + angle_increment
                        
                        # Keep same Y component for inclination
                        y_ratio = sat_data["position"]["y"] / current_radius if current_radius > 0 else 0
                        new_radius = math.sqrt(current_radius**2 - sat_data["position"]["y"]**2) if current_radius > abs(sat_data["position"]["y"]) else current_radius
                        
                        sat_data["position"]["x"] = new_radius * math.cos(new_angle)
                        sat_data["position"]["z"] = new_radius * math.sin(new_angle)
                        # Keep Y component to maintain orbital plane
                        
        except Exception as e:
            logger.warning(f"Error updating satellite positions: {e}")
    
    async def _update_contacts(self, sim_time: float):
        """Update contact windows (placeholder)."""
        # This will use contact prediction when implemented
        pass
    
    async def _process_routing(self, sim_time: float):
        """Process DTN routing (placeholder)."""
        # This will implement actual routing algorithms
        pass
    
    async def _generate_traffic(self, sim_time: float):
        """Generate network traffic (placeholder)."""
        # Generate some test bundles
        if int(sim_time) % 10 == 0:  # Every 10 seconds
            self.stats.bundles_generated += 1
    
    async def _update_statistics(self):
        """Update simulation statistics."""
        # Calculate delivery ratio, cleanup expired bundles, etc.
        total_expired = 0
        for store in self.bundle_stores.values():
            total_expired += store.cleanup_expired()
        
        self.stats.bundles_expired += total_expired
    
    def get_metrics(self) -> NetworkMetrics:
        """Get current network metrics."""
        delivery_ratio = 0.0
        if self.stats.bundles_generated > 0:
            delivery_ratio = self.stats.bundles_delivered / self.stats.bundles_generated
        
        # Calculate average buffer utilization
        buffer_util = 0.0
        if self.bundle_stores:
            buffer_util = sum(store.utilization for store in self.bundle_stores.values()) / len(self.bundle_stores)
        
        return NetworkMetrics(
            delivery_ratio=delivery_ratio,
            average_delay=0.0,  # Placeholder
            hop_count_avg=0.0,  # Placeholder
            network_overhead=0.0,  # Placeholder
            buffer_utilization=buffer_util,
            bundles_generated=self.stats.bundles_generated,
            bundles_delivered=self.stats.bundles_delivered,
            bundles_expired=self.stats.bundles_expired
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert simulation to dictionary."""
        return {
            "id": self.id,
            "config": self.config.dict(),
            "stats": asdict(self.stats),
            "metrics": self.get_metrics().dict(),
            "satellite_count": len(self.satellites),
            "ground_station_count": len(self.ground_stations)
        }


class SimulationManager:
    """Manages multiple simulation instances."""
    
    def __init__(self):
        self.simulations: Dict[str, Simulation] = {}
        logger.info("Initialized simulation manager")
    
    async def create_simulation(self, config: SimulationConfig) -> str:
        """Create a new simulation."""
        simulation = Simulation(config)
        
        # Initialize the simulation
        success = await simulation.initialize()
        if not success:
            raise Exception("Failed to initialize simulation")
        
        self.simulations[simulation.id] = simulation
        return simulation.id
    
    async def get_simulation(self, simulation_id: str) -> Optional[Simulation]:
        """Get a simulation by ID."""
        return self.simulations.get(simulation_id)
    
    async def list_simulations(self) -> List[Dict[str, Any]]:
        """List all simulations."""
        return [sim.to_dict() for sim in self.simulations.values()]
    
    async def start_simulation(self, simulation_id: str) -> bool:
        """Start a simulation."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return False
        return await simulation.start()
    
    async def pause_simulation(self, simulation_id: str) -> bool:
        """Pause a simulation."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return False
        return await simulation.pause()
    
    async def stop_simulation(self, simulation_id: str) -> bool:
        """Stop a simulation."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return False
        return await simulation.stop()
    
    async def delete_simulation(self, simulation_id: str) -> bool:
        """Delete a simulation."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return False
        
        # Stop if running
        await simulation.stop()
        
        # Remove from manager
        del self.simulations[simulation_id]
        return True
    
    async def get_simulation_status(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get simulation status."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return None
        
        return {
            "id": simulation.id,
            "status": simulation.state.value,
            "stats": asdict(simulation.stats)
        }
    
    async def get_simulation_metrics(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get simulation metrics."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return None
        
        return simulation.get_metrics().dict()
    
    async def get_satellite_info(self, simulation_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get satellite information."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return None
        
        return list(simulation.satellites.values())
    
    async def get_ground_station_info(self, simulation_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get ground station information."""
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return None
        
        return list(simulation.ground_stations.values())
    
    async def get_status(self) -> Dict[str, Any]:
        """Get overall manager status."""
        return {
            "total_simulations": len(self.simulations),
            "running_simulations": len([
                s for s in self.simulations.values() 
                if s.state == SimulationState.RUNNING
            ]),
            "simulation_ids": list(self.simulations.keys())
        }
    
    async def cleanup(self):
        """Cleanup all simulations."""
        logger.info("Cleaning up simulation manager")
        for simulation in self.simulations.values():
            await simulation.stop()
        self.simulations.clear()