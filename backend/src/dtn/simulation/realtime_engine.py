"""
Real-time DTN Simulation Engine

This module implements accelerated real-time satellite orbital propagation
for DTN simulations with actual moving satellites and dynamic contact windows.
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from threading import Lock

from dtn.orbital.mechanics import KeplerianElements, OrbitalMechanics, SatelliteState as OrbitalSatelliteState
from dtn.orbital.contact_prediction import ContactPredictor, GroundStation
from dtn.networking.routing.base_router import BaseRouter
from dtn.networking.routing.epidemic import EpidemicRouter
from dtn.networking.routing.prophet import ProphetRouter
from dtn.networking.routing.spray_and_wait import SprayAndWaitRouter

@dataclass
class SimBundle:
    """Simplified bundle for simulation purposes."""
    bundle_id: str
    source: str
    destination: str
    payload_size: int
    creation_time: datetime
    ttl: int  # Time to live in seconds
    current_carrier: Optional[str] = None  # Current satellite carrying the bundle
    hop_count: int = 0

logger = logging.getLogger(__name__)

def calculate_distance(pos1: Tuple[float, float, float], pos2: Tuple[float, float, float]) -> float:
    """Calculate Euclidean distance between two 3D positions."""
    dx = pos1[0] - pos2[0]
    dy = pos1[1] - pos2[1]
    dz = pos1[2] - pos2[2]
    return (dx*dx + dy*dy + dz*dz) ** 0.5

@dataclass
class SatelliteState:
    """Current state of a satellite in the simulation."""
    satellite_id: str
    position: Tuple[float, float, float]  # ECEF coordinates (x, y, z) in km
    velocity: Tuple[float, float, float]  # ECEF velocity (vx, vy, vz) in km/s
    orbital_elements: KeplerianElements
    last_update: datetime
    active_contacts: Set[str] = field(default_factory=set)  # Ground station IDs
    stored_bundles: List[str] = field(default_factory=list)  # Bundle IDs
    routing_state: Dict = field(default_factory=dict)

@dataclass
class SimContactWindow:
    """Active contact window between satellite and ground station for simulation."""
    satellite_id: str
    ground_station_id: str
    start_time: datetime
    end_time: datetime
    max_elevation: float
    data_rate_mbps: float
    is_active: bool = True

@dataclass
class SimulationMetrics:
    """Comprehensive simulation metrics."""
    simulation_id: str
    start_time: datetime
    current_sim_time: datetime
    time_acceleration: float  # Simulation time / real time ratio
    total_bundles_generated: int = 0
    bundles_delivered: int = 0
    bundles_in_transit: int = 0
    active_contact_windows: int = 0
    total_contact_windows: int = 0
    average_delivery_delay: float = 0.0
    network_overhead_ratio: float = 0.0
    throughput_bundles_per_hour: float = 0.0

class RealTimeSimulationEngine:
    """
    Real-time DTN simulation engine with accelerated orbital propagation.
    
    Simulates actual satellite movement through orbits with proper DTN bundle
    routing, contact prediction, and performance metrics.
    """
    
    def __init__(self, 
                 simulation_id: str,
                 constellation_elements: Dict[str, KeplerianElements],
                 ground_stations: Dict[str, GroundStation],
                 routing_algorithm: str = "epidemic",
                 time_acceleration: float = 3600.0,  # 1 hour sim time per 1 second real time
                 bundle_generation_rate: float = 0.2):  # bundles per simulation second
        
        self.simulation_id = simulation_id
        self.constellation_elements = constellation_elements
        self.ground_stations = ground_stations
        self.time_acceleration = time_acceleration
        self.bundle_generation_rate = bundle_generation_rate
        
        # Simulation state
        self.is_running = False
        self.is_paused = False
        self.start_time = datetime.now()
        self.current_sim_time = self.start_time
        self.last_update = time.time()
        
        # Satellite states
        self.satellite_states: Dict[str, SatelliteState] = {}
        self.active_contacts: Dict[str, SimContactWindow] = {}
        self.completed_contacts: List[SimContactWindow] = []
        
        # Bundle management
        self.bundles: Dict[str, SimBundle] = {}
        self.delivered_bundles: Set[str] = set()
        self.bundle_counter = 0
        
        # Routing algorithm
        self.routing_algorithm = self._create_routing_algorithm(routing_algorithm)
        
        # Contact prediction
        self.contact_predictor = ContactPredictor()
        
        # Orbital mechanics calculator
        self.orbital_mechanics = OrbitalMechanics()
        
        # Metrics
        self.metrics = SimulationMetrics(
            simulation_id=simulation_id,
            start_time=self.start_time,
            current_sim_time=self.current_sim_time,
            time_acceleration=time_acceleration
        )
        
        # Thread safety
        self._state_lock = Lock()
        
        # Initialize satellite states
        self._initialize_satellite_states()
        
        logger.info(f"Initialized real-time simulation engine for {simulation_id} with {len(self.constellation_elements)} satellites and {len(self.ground_stations)} ground stations")
    
    def _create_routing_algorithm(self, algorithm_name: str) -> BaseRouter:
        """Create the specified routing algorithm instance."""
        node_id = f"sim_engine_{self.simulation_id}"
        
        if algorithm_name == "epidemic":
            return EpidemicRouter(node_id)
        elif algorithm_name == "prophet":
            return ProphetRouter(node_id)
        elif algorithm_name == "spray_and_wait":
            return SprayAndWaitRouter(node_id)
        else:
            logger.warning(f"Unknown routing algorithm '{algorithm_name}', defaulting to epidemic")
            return EpidemicRouter(node_id)
    
    def _initialize_satellite_states(self):
        """Initialize the current state of all satellites."""
        current_time = self.start_time
        
        for sat_id, elements in self.constellation_elements.items():
            # Propagate to current time to get initial position
            orbital_state = self.orbital_mechanics.propagate_orbit(elements, current_time)
            
            self.satellite_states[sat_id] = SatelliteState(
                satellite_id=sat_id,
                position=(orbital_state.position.x, orbital_state.position.y, orbital_state.position.z),
                velocity=(orbital_state.velocity.x, orbital_state.velocity.y, orbital_state.velocity.z),
                orbital_elements=elements,
                last_update=current_time
            )
    
    async def start_simulation(self):
        """Start the real-time simulation loop."""
        self.is_running = True
        self.is_paused = False
        logger.info(f"Starting real-time simulation {self.simulation_id}")
        
        # Start the main simulation loop
        await self._simulation_loop()
    
    def pause_simulation(self):
        """Pause the simulation."""
        self.is_paused = True
        logger.info(f"Paused simulation {self.simulation_id}")
    
    def resume_simulation(self):
        """Resume the simulation."""
        self.is_paused = False
        self.last_update = time.time()
        logger.info(f"Resumed simulation {self.simulation_id}")
    
    def stop_simulation(self):
        """Stop the simulation."""
        self.is_running = False
        self.is_paused = False
        logger.info(f"Stopped simulation {self.simulation_id}")
    
    async def _simulation_loop(self):
        """Main simulation loop with time-stepped updates."""
        time_step = 1.0  # 1 second simulation time steps
        
        while self.is_running:
            if not self.is_paused:
                # Calculate time advancement
                current_real_time = time.time()
                real_time_delta = current_real_time - self.last_update
                sim_time_delta = real_time_delta * self.time_acceleration
                
                # Update simulation time
                self.current_sim_time += timedelta(seconds=sim_time_delta)
                self.last_update = current_real_time
                
                # Update simulation state
                with self._state_lock:
                    await self._update_satellite_positions()
                    await self._update_contact_windows()
                    await self._generate_bundles()
                    await self._route_bundles()
                    await self._update_metrics()
                
            # Sleep to maintain reasonable update rate (10 Hz)
            await asyncio.sleep(0.1)
    
    async def _update_satellite_positions(self):
        """Update positions of all satellites based on orbital mechanics."""
        for sat_id, sat_state in self.satellite_states.items():
            # Propagate orbit to current simulation time
            orbital_state = self.orbital_mechanics.propagate_orbit(sat_state.orbital_elements, self.current_sim_time)
            
            # Update satellite state
            sat_state.position = (orbital_state.position.x, orbital_state.position.y, orbital_state.position.z)
            sat_state.velocity = (orbital_state.velocity.x, orbital_state.velocity.y, orbital_state.velocity.z)
            sat_state.last_update = self.current_sim_time
    
    async def _update_contact_windows(self):
        """Update active contact windows between satellites and ground stations."""
        new_contacts = []
        expired_contacts = []
        
        # Debug: Log contact checking
        contact_checks = 0
        visible_checks = 0
        
        # Check all satellite-ground station pairs for contact opportunities
        for sat_id, sat_state in self.satellite_states.items():
            for gs_id, ground_station in self.ground_stations.items():
                contact_key = f"{sat_id}_{gs_id}"
                contact_checks += 1
                
                # Check if contact is possible (simplified visibility check)
                is_visible = self._check_satellite_visibility(sat_state, ground_station)
                if is_visible:
                    visible_checks += 1
                
                if is_visible and contact_key not in self.active_contacts:
                    # Start new contact window
                    contact_window = SimContactWindow(
                        satellite_id=sat_id,
                        ground_station_id=gs_id,
                        start_time=self.current_sim_time,
                        end_time=self.current_sim_time + timedelta(minutes=15),  # Estimated duration
                        max_elevation=45.0,  # Simplified
                        data_rate_mbps=10.0  # Simplified data rate
                    )
                    
                    self.active_contacts[contact_key] = contact_window
                    sat_state.active_contacts.add(gs_id)
                    new_contacts.append(contact_key)
                    
                    logger.info(f"Started contact: {sat_id} -> {gs_id}")
                    
                elif not is_visible and contact_key in self.active_contacts:
                    # End contact window
                    contact_window = self.active_contacts[contact_key]
                    contact_window.is_active = False
                    contact_window.end_time = self.current_sim_time
                    
                    self.completed_contacts.append(contact_window)
                    sat_state.active_contacts.discard(gs_id)
                    expired_contacts.append(contact_key)
                    
                    logger.info(f"Ended contact: {sat_id} -> {gs_id}")
        
        # Clean up expired contacts
        for contact_key in expired_contacts:
            del self.active_contacts[contact_key]
        
        # Debug log every 10 seconds of sim time
        if int(self.current_sim_time.timestamp()) % 10 == 0:
            logger.info(f"Contact update: {contact_checks} checks, {visible_checks} visible, {len(self.active_contacts)} active")
        
        # Update metrics
        self.metrics.active_contact_windows = len(self.active_contacts)
        self.metrics.total_contact_windows = len(self.completed_contacts) + len(self.active_contacts)
    
    def _check_satellite_visibility(self, sat_state: SatelliteState, ground_station: GroundStation) -> bool:
        """Simplified visibility check between satellite and ground station."""
        # Calculate distance between satellite and ground station (ECEF coordinates)
        sat_pos = sat_state.position  # Already in ECEF from orbital mechanics
        
        # Convert ground station lat/lon to approximate ECEF (simplified)
        import math
        lat_rad = math.radians(ground_station.position.latitude)
        lon_rad = math.radians(ground_station.position.longitude)
        earth_radius = 6371.0  # km
        
        gs_x = (earth_radius + ground_station.position.altitude) * math.cos(lat_rad) * math.cos(lon_rad)
        gs_y = (earth_radius + ground_station.position.altitude) * math.cos(lat_rad) * math.sin(lon_rad)
        gs_z = (earth_radius + ground_station.position.altitude) * math.sin(lat_rad)
        
        gs_pos = (gs_x, gs_y, gs_z)
        distance = calculate_distance(sat_pos, gs_pos)
        
        # More generous visibility check for simulation
        # Check if satellite is above horizon (distance from earth center > earth radius)
        sat_distance_from_earth = calculate_distance(sat_pos, (0, 0, 0))
        if sat_distance_from_earth < earth_radius + 100:  # At least 100km altitude
            return False
            
        # Generous range check - satellites in LEO should be visible
        max_range = max(ground_station.max_range, 3000.0)  # At least 3000km range
        is_visible = distance <= max_range
        
        if is_visible:
            logger.debug(f"Satellite at {sat_pos} visible from {ground_station.name} at distance {distance:.1f}km")
        
        return is_visible
    
    async def _generate_bundles(self):
        """Generate new bundles for the DTN network."""
        # Generate bundles based on configured rate
        time_since_last = (self.current_sim_time - self.start_time).total_seconds()
        expected_bundles = int(time_since_last * self.bundle_generation_rate)
        
        while len(self.bundles) < expected_bundles:
            self.bundle_counter += 1
            bundle_id = f"bundle_{self.simulation_id}_{self.bundle_counter:06d}"
            
            # Use the first two ground stations as source and destination
            gs_ids = list(self.ground_stations.keys())
            if len(gs_ids) >= 2:
                source_gs = gs_ids[0]  # First station is source
                dest_gs = gs_ids[1]    # Second station is destination
                
                bundle = SimBundle(
                    bundle_id=bundle_id,
                    source=source_gs,
                    destination=dest_gs,
                    payload_size=1024,  # 1KB payload
                    creation_time=self.current_sim_time,
                    ttl=3600  # 1 hour TTL
                )
                
                self.bundles[bundle_id] = bundle
                self.metrics.total_bundles_generated += 1
                
                logger.debug(f"Generated bundle {bundle_id} from {source_gs} to {dest_gs}")
    
    async def _route_bundles(self):
        """Route bundles through the DTN network using the selected algorithm."""
        # Step 1: Inject new bundles at source ground station
        await self._inject_bundles_at_source()
        
        # Step 2: Route bundles between satellites using DTN routing
        await self._perform_dtn_routing()
        
        # Step 3: Deliver bundles at destination ground station
        await self._deliver_bundles_at_destination()
        
        # Update bundles in transit
        self.metrics.bundles_in_transit = len(self.bundles) - len(self.delivered_bundles)
    
    async def _inject_bundles_at_source(self):
        """Inject bundles into the network via satellites in contact with source ground station."""
        source_gs = list(self.ground_stations.keys())[0]  # Source station
        
        # Find satellites in contact with source ground station
        for contact_key, contact_window in self.active_contacts.items():
            if contact_window.ground_station_id == source_gs:
                satellite_id = contact_window.satellite_id
                satellite = self.satellite_states[satellite_id]
                
                # Transfer pending bundles to this satellite
                for bundle_id, bundle in self.bundles.items():
                    if bundle_id not in self.delivered_bundles and bundle.source == source_gs:
                        # Check if bundle is not already on a satellite
                        bundle_on_satellite = any(
                            bundle_id in sat.stored_bundles for sat in self.satellite_states.values()
                        )
                        
                        if not bundle_on_satellite:
                            # Add bundle to satellite's storage
                            bundle.current_carrier = satellite_id
                            satellite.stored_bundles.append(bundle_id)
                            logger.debug(f"Bundle {bundle_id} injected onto satellite {satellite_id} via {source_gs}")
    
    async def _perform_dtn_routing(self):
        """Perform DTN routing between satellites using the configured algorithm."""
        # For each active inter-satellite contact, perform routing
        inter_satellite_contacts = []
        
        # Identify potential inter-satellite contacts (simplified - satellites close to each other)
        satellite_ids = list(self.satellite_states.keys())
        for i, sat1_id in enumerate(satellite_ids):
            for sat2_id in satellite_ids[i+1:]:
                sat1 = self.satellite_states[sat1_id]
                sat2 = self.satellite_states[sat2_id]
                
                # Calculate distance between satellites
                distance = calculate_distance(sat1.position, sat2.position)
                
                # If satellites are within communication range (simplified: < 1000 km)
                if distance < 1000.0:
                    inter_satellite_contacts.append((sat1_id, sat2_id, distance))
        
        # Perform routing decisions for each contact
        for sat1_id, sat2_id, distance in inter_satellite_contacts:
            await self._exchange_bundles_between_satellites(sat1_id, sat2_id)
    
    async def _exchange_bundles_between_satellites(self, sat1_id: str, sat2_id: str):
        """Exchange bundles between two satellites based on routing algorithm."""
        sat1 = self.satellite_states[sat1_id]
        sat2 = self.satellite_states[sat2_id]
        
        # Get routing algorithm decisions
        if isinstance(self.routing_algorithm, EpidemicRouter):
            # Epidemic: replicate all bundles to both satellites
            await self._epidemic_exchange(sat1, sat2)
        elif isinstance(self.routing_algorithm, ProphetRouter):
            # PRoPHET: use delivery predictability 
            await self._prophet_exchange(sat1, sat2)
        elif isinstance(self.routing_algorithm, SprayAndWaitRouter):
            # Spray-and-Wait: distribute copies based on remaining spray count
            await self._spray_and_wait_exchange(sat1, sat2)
    
    async def _epidemic_exchange(self, sat1: SatelliteState, sat2: SatelliteState):
        """Epidemic routing: replicate all unique bundles to both satellites."""
        all_bundles = set(sat1.stored_bundles + sat2.stored_bundles)
        
        for bundle_id in all_bundles:
            if bundle_id not in sat1.stored_bundles:
                sat1.stored_bundles.append(bundle_id)
                # Update bundle carrier info
                if bundle_id in self.bundles:
                    self.bundles[bundle_id].current_carrier = sat1.satellite_id
            
            if bundle_id not in sat2.stored_bundles:
                sat2.stored_bundles.append(bundle_id)
                if bundle_id in self.bundles:
                    self.bundles[bundle_id].current_carrier = sat2.satellite_id
    
    async def _prophet_exchange(self, sat1: SatelliteState, sat2: SatelliteState):
        """PRoPHET routing: exchange based on delivery predictability."""
        # Simplified PRoPHET: forward bundles to satellite with better connectivity
        dest_gs = list(self.ground_stations.keys())[1]  # Destination station
        
        # Simple heuristic: satellite closer to destination gets the bundle
        for bundle_id in list(sat1.stored_bundles):
            if bundle_id in self.bundles:
                bundle = self.bundles[bundle_id]
                if bundle.destination == dest_gs:
                    # Calculate which satellite is "better" for delivery (simplified)
                    sat1_score = len(sat1.active_contacts)
                    sat2_score = len(sat2.active_contacts)
                    
                    if sat2_score > sat1_score and bundle_id not in sat2.stored_bundles:
                        sat2.stored_bundles.append(bundle_id)
                        bundle.current_carrier = sat2.satellite_id
    
    async def _spray_and_wait_exchange(self, sat1: SatelliteState, sat2: SatelliteState):
        """Spray-and-Wait: limit the number of copies in the network."""
        # Simplified spray-and-wait: only create one additional copy per bundle
        for bundle_id in list(sat1.stored_bundles):
            if bundle_id not in sat2.stored_bundles and len(sat2.stored_bundles) < 5:  # Limit copies
                sat2.stored_bundles.append(bundle_id)
                if bundle_id in self.bundles:
                    self.bundles[bundle_id].current_carrier = sat2.satellite_id
    
    async def _deliver_bundles_at_destination(self):
        """Deliver bundles from satellites to destination ground station."""
        dest_gs = list(self.ground_stations.keys())[1]  # Destination station
        
        # Find satellites in contact with destination ground station
        for contact_key, contact_window in self.active_contacts.items():
            if contact_window.ground_station_id == dest_gs:
                satellite_id = contact_window.satellite_id
                satellite = self.satellite_states[satellite_id]
                
                # Deliver bundles stored on this satellite
                for bundle_id in list(satellite.stored_bundles):
                    if bundle_id in self.bundles and bundle_id not in self.delivered_bundles:
                        bundle = self.bundles[bundle_id]
                        if bundle.destination == dest_gs:
                            # Deliver the bundle
                            self.delivered_bundles.add(bundle_id)
                            self.metrics.bundles_delivered += 1
                            satellite.stored_bundles.remove(bundle_id)
                            
                            # Calculate delivery delay
                            delivery_delay = (self.current_sim_time - bundle.creation_time).total_seconds()
                            if self.metrics.bundles_delivered > 0:
                                # Update average delay
                                current_avg = self.metrics.average_delivery_delay
                                n = self.metrics.bundles_delivered
                                self.metrics.average_delivery_delay = (current_avg * (n-1) + delivery_delay) / n
                            
                            logger.debug(f"Bundle {bundle_id} delivered to {dest_gs} from satellite {satellite_id} after {delivery_delay:.1f}s")
    
    async def _update_metrics(self):
        """Update comprehensive simulation metrics."""
        # Calculate runtime
        runtime_seconds = (self.current_sim_time - self.start_time).total_seconds()
        
        # Calculate throughput
        if runtime_seconds > 0:
            self.metrics.throughput_bundles_per_hour = (self.metrics.bundles_delivered / runtime_seconds) * 3600
        
        # Calculate network overhead (simplified)
        if self.metrics.bundles_delivered > 0:
            self.metrics.network_overhead_ratio = self.metrics.total_bundles_generated / self.metrics.bundles_delivered
        
        # Update simulation time
        self.metrics.current_sim_time = self.current_sim_time
    
    def get_current_status(self) -> Dict:
        """Get current simulation status and metrics."""
        with self._state_lock:
            runtime_seconds = (self.current_sim_time - self.start_time).total_seconds()
            
            return {
                "simulation_id": self.simulation_id,
                "status": "running" if self.is_running and not self.is_paused else "paused" if self.is_paused else "stopped",
                "runtime_seconds": runtime_seconds,
                "current_sim_time": self.current_sim_time.isoformat(),
                "time_acceleration": self.time_acceleration,
                "bundles_generated": self.metrics.total_bundles_generated,
                "bundles_delivered": self.metrics.bundles_delivered,
                "bundles_in_transit": self.metrics.bundles_in_transit,
                "active_contacts": len(self.active_contacts),
                "total_contacts": self.metrics.total_contact_windows,
                "satellites_active": len(self.satellite_states),
                "current_activity": f"Routing bundles through {len(self.active_contacts)} active contacts",
                "delivery_ratio": self.metrics.bundles_delivered / max(1, self.metrics.total_bundles_generated),
                "average_delay_seconds": self.metrics.average_delivery_delay,
                "throughput_bundles_per_hour": self.metrics.throughput_bundles_per_hour,
                "network_overhead_ratio": self.metrics.network_overhead_ratio
            }
    
    def get_detailed_metrics(self) -> Dict:
        """Get detailed simulation metrics for analysis."""
        return {
            "simulation_id": self.simulation_id,
            "metrics": {
                "total_runtime_seconds": (self.current_sim_time - self.start_time).total_seconds(),
                "bundles_generated": self.metrics.total_bundles_generated,
                "bundles_delivered": self.metrics.bundles_delivered,
                "bundles_in_transit": self.metrics.bundles_in_transit,
                "delivery_ratio": self.metrics.bundles_delivered / max(1, self.metrics.total_bundles_generated),
                "average_delivery_delay_seconds": self.metrics.average_delivery_delay,
                "throughput_bundles_per_hour": self.metrics.throughput_bundles_per_hour,
                "network_overhead_ratio": self.metrics.network_overhead_ratio,
                "total_contact_windows": self.metrics.total_contact_windows,
                "active_contact_windows": len(self.active_contacts),
                "satellites_tracked": len(self.satellite_states),
                "ground_stations": len(self.ground_stations)
            },
            "contact_summary": {
                "completed_contacts": len(self.completed_contacts),
                "active_contacts": len(self.active_contacts),
                "total_contact_time_minutes": sum(
                    (contact.end_time - contact.start_time).total_seconds() / 60 
                    for contact in self.completed_contacts
                )
            }
        }