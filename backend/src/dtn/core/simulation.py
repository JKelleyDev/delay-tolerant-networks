"""
Core Simulation Engine

Manages DTN simulation lifecycle, coordinates components, and provides
real-time status updates.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .bundle import Bundle, BundleStore
from ..api.models.base_models import SimulationConfig, SimulationStatus, NetworkMetrics

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
        """Initialize satellite constellation (placeholder)."""
        # This will be implemented when we have orbital mechanics
        self.stats.total_satellites = 10  # Placeholder
        for i in range(self.stats.total_satellites):
            sat_id = f"sat_{i:03d}"
            self.satellites[sat_id] = {
                "id": sat_id,
                "name": f"Satellite {i}",
                "position": {"x": 0, "y": 0, "z": 0},
                "velocity": {"x": 0, "y": 0, "z": 0}
            }
            self.bundle_stores[sat_id] = BundleStore(max_size=10*1024*1024)  # 10MB
    
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
        """Update satellite positions (placeholder)."""
        # This will use orbital mechanics when implemented
        pass
    
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