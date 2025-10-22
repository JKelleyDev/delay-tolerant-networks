"""
DTN Simulation Engine

Main simulation coordinator that brings together orbital mechanics,
DTN routing, and contact prediction for complete system simulation.
"""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from .core.dtn_node import DTNNode
from .core.bundle import Bundle, BundlePriority, Contact
from .orbital.orbital_mechanics import OrbitalMechanics, OrbitalElements
from .orbital.contact_predictor import ContactPredictor

logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """Configuration for DTN simulation."""
    simulation_duration_hours: float = 24.0
    time_step_minutes: float = 1.0
    contact_prediction_interval_hours: float = 6.0
    bundle_generation_rate_per_hour: int = 10
    default_ttl_hours: int = 48
    default_buffer_size_mb: int = 20
    

@dataclass 
class SimulationResults:
    """Results from a DTN simulation run."""
    total_bundles_created: int = 0
    total_bundles_delivered: int = 0
    total_bundles_dropped: int = 0
    total_contacts_established: int = 0
    delivery_ratio: float = 0.0
    average_delivery_delay: float = 0.0
    network_overhead: float = 0.0
    simulation_duration: float = 0.0
    node_stats: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DTNSimulation:
    """Complete DTN simulation engine."""
    
    def __init__(self, config: SimulationConfig = None):
        self.config = config or SimulationConfig()
        self.orbital_calc = OrbitalMechanics()
        self.contact_predictor = ContactPredictor(self.orbital_calc)
        
        self.nodes: Dict[str, DTNNode] = {}
        self.satellite_orbits: Dict[str, OrbitalElements] = {}
        self.active_contacts: Dict[str, Contact] = {}
        self.bundle_delivery_times: Dict[str, float] = {}
        
        self.start_time = time.time()
        self.current_time = self.start_time
        
    def add_satellite(self, sat_id: str, orbital_elements: OrbitalElements, 
                     routing_algorithm: str = "epidemic") -> DTNNode:
        """Add a satellite to the simulation."""
        node = DTNNode(sat_id, routing_algorithm, self.config.default_buffer_size_mb)
        self.nodes[sat_id] = node
        self.satellite_orbits[sat_id] = orbital_elements
        
        logger.info(f"Added satellite {sat_id} with {routing_algorithm} routing")
        return node
        
    def create_default_constellation(self):
        """Create a basic satellite constellation for testing."""
        # ISS-like LEO satellite
        iss_orbit = OrbitalElements(
            semi_major_axis=6793.0,
            eccentricity=0.0003,
            inclination=51.6,
            raan=180.0,
            arg_perigee=90.0,
            true_anomaly=0.0,
            epoch=self.start_time
        )
        self.add_satellite("ISS", iss_orbit, "epidemic")
        
        # GPS-like MEO satellites
        for i in range(3):
            gps_orbit = OrbitalElements(
                semi_major_axis=26560.0,
                eccentricity=0.01,
                inclination=55.0,
                raan=90.0 + i * 120,  # Spread RAAN
                arg_perigee=45.0,
                true_anomaly=i * 120.0,  # Spread true anomaly
                epoch=self.start_time
            )
            self.add_satellite(f"GPS-{i+1}", gps_orbit, "prophet")
            
        # Low Earth Orbit constellation
        for i in range(4):
            leo_orbit = OrbitalElements(
                semi_major_axis=7000.0 + i * 100,  # Slightly different altitudes
                eccentricity=0.001,
                inclination=98.0,  # Sun-synchronous
                raan=i * 90,
                arg_perigee=0.0,
                true_anomaly=i * 90.0,
                epoch=self.start_time
            )
            self.add_satellite(f"LEO-{i+1}", leo_orbit, "epidemic")
            
    def generate_test_traffic(self, bundles_per_hour: int = None):
        """Generate test message traffic between satellites."""
        if bundles_per_hour is None:
            bundles_per_hour = self.config.bundle_generation_rate_per_hour
            
        node_ids = list(self.nodes.keys())
        if len(node_ids) < 2:
            return
            
        bundles_per_step = max(1, bundles_per_hour // (60 // self.config.time_step_minutes))
        
        for _ in range(bundles_per_step):
            # Create bundles between nodes that are likely to have contact
            import random
            source_id = random.choice(node_ids)
            
            # Create bundles with high delivery probability
            # Strategy: ensure some bundles go to nodes that will definitely have contacts
            if len(node_ids) >= 2:
                # 50% chance: send to immediate neighbor, 50% chance: random destination
                if random.random() < 0.5:
                    # Send to next node (circular)
                    source_idx = node_ids.index(source_id)
                    dest_idx = (source_idx + 1) % len(node_ids)
                    dest_id = node_ids[dest_idx]
                else:
                    # Random destination for DTN challenge
                    dest_id = random.choice([n for n in node_ids if n != source_id])
            else:
                dest_id = random.choice([n for n in node_ids if n != source_id])
            
            # Create test payload
            payload = f"Test message from {source_id} to {dest_id} at {self.current_time}".encode()
            ttl_seconds = self.config.default_ttl_hours * 3600
            
            bundle = self.nodes[source_id].create_bundle(
                destination=dest_id,
                payload=payload,
                ttl_seconds=ttl_seconds,
                priority=BundlePriority.NORMAL
            )
            
            # Track for delivery time calculation
            self.bundle_delivery_times[bundle.id] = self.current_time
            
    def update_contacts(self):
        """Update contact opportunities based on current satellite positions."""
        # Clear existing contacts
        for node in self.nodes.values():
            node.contacts.clear()
        
        # Add simplified satellite-to-satellite contacts based on distance
        contact_count = 0
        satellite_positions = {}
        
        # Get current positions of all satellites
        for sat_id, orbit in self.satellite_orbits.items():
            if sat_id in self.nodes:
                state = self.orbital_calc.propagate_orbit(orbit, self.current_time)
                satellite_positions[sat_id] = state.position
        
        # Create contacts between satellites within communication range
        max_range_km = 10000  # Maximum communication range (increased for better connectivity)
        contact_duration = self.config.time_step_minutes * 60  # Duration in seconds
        
        sat_ids = list(satellite_positions.keys())
        for i, sat1 in enumerate(sat_ids):
            for j, sat2 in enumerate(sat_ids[i+1:], i+1):
                if sat1 != sat2:
                    pos1 = satellite_positions[sat1]
                    pos2 = satellite_positions[sat2]
                    
                    # Calculate distance
                    dx = pos1.x - pos2.x
                    dy = pos1.y - pos2.y  
                    dz = pos1.z - pos2.z
                    distance = (dx*dx + dy*dy + dz*dz) ** 0.5
                    
                    if distance <= max_range_km:
                        # Create bidirectional contacts
                        start_time = self.current_time
                        end_time = start_time + contact_duration
                        data_rate = 1000000  # 1 Mbps
                        
                        # Contact from sat1 to sat2
                        contact_1_2 = Contact(sat1, sat2, start_time, end_time, data_rate)
                        self.nodes[sat1].add_contact(contact_1_2)
                        
                        # Contact from sat2 to sat1  
                        contact_2_1 = Contact(sat2, sat1, start_time, end_time, data_rate)
                        self.nodes[sat2].add_contact(contact_2_1)
                        
                        contact_count += 2
        
        # Also predict ground station contacts using the original predictor
        try:
            contact_windows = self.contact_predictor.predict_contacts(
                self.satellite_orbits,
                self.current_time,
                duration_hours=self.config.contact_prediction_interval_hours,
                time_step_minutes=self.config.time_step_minutes
            )
            
            # Add ground station contacts to nodes
            for window in contact_windows:
                contact = window.to_contact()
                if contact.source in self.nodes:
                    self.nodes[contact.source].add_contact(contact)
                    contact_count += 1
        except Exception as e:
            logger.warning(f"Ground station contact prediction failed: {e}")
                
        logger.info(f"Updated contacts: {contact_count} contacts created")
        
    def simulate_step(self) -> Dict[str, Any]:
        """Execute one simulation time step."""
        step_results = {}
        
        # Generate traffic
        self.generate_test_traffic()
        
        # Update satellite positions and contacts
        self.update_contacts()
        
        # Process DTN routing for each node and collect transmissions
        all_transmissions = {}
        
        for node_id, node in self.nodes.items():
            result = node.simulate_step(self.current_time)
            step_results[node_id] = result
            
            # Check for forwarding results (bundles transmitted to other nodes)
            forwarding_results = result.get('forwarding_results', {})
            for bundle_id, destinations in forwarding_results.items():
                if bundle_id not in all_transmissions:
                    all_transmissions[bundle_id] = {
                        'bundle': None,
                        'source': node_id,
                        'destinations': destinations
                    }
                    # Get the bundle from the source node's buffer
                    bundle = node.buffer_manager.get_bundle(bundle_id)
                    if bundle:
                        all_transmissions[bundle_id]['bundle'] = bundle
        
        # Process bundle transmissions (deliver bundles to destination nodes)
        for bundle_id, transmission in all_transmissions.items():
            bundle = transmission['bundle']
            if bundle:
                for dest_node_id in transmission['destinations']:
                    if dest_node_id in self.nodes:
                        # Deliver bundle to destination node
                        success = self.nodes[dest_node_id].receive_bundle(bundle)
                        if success:
                            logger.debug(f"Bundle {bundle_id} transmitted from {transmission['source']} to {dest_node_id}")
                            
                            # Remove bundle from source node if it was successfully delivered to final destination
                            if bundle.destination == dest_node_id:
                                self.nodes[transmission['source']].buffer_manager.remove_bundle(bundle_id)
            
        # Advance time
        self.current_time += self.config.time_step_minutes * 60
        
        return {
            "timestamp": self.current_time,
            "node_results": step_results,
            "elapsed_hours": (self.current_time - self.start_time) / 3600
        }
        
    def run_simulation(self) -> SimulationResults:
        """Run complete simulation and return results."""
        logger.info(f"Starting DTN simulation for {self.config.simulation_duration_hours} hours")
        
        end_time = self.start_time + (self.config.simulation_duration_hours * 3600)
        step_count = 0
        
        while self.current_time < end_time:
            step_results = self.simulate_step()
            step_count += 1
            
            if step_count % 60 == 0:  # Log every hour
                elapsed_hours = (self.current_time - self.start_time) / 3600
                logger.info(f"Simulation progress: {elapsed_hours:.1f} hours completed")
                
        # Calculate final results
        return self._calculate_results()
        
    def _calculate_results(self) -> SimulationResults:
        """Calculate simulation results and statistics."""
        total_created = sum(node.stats.bundles_created for node in self.nodes.values())
        total_delivered = sum(node.stats.bundles_delivered for node in self.nodes.values())
        total_dropped = sum(node.stats.bundles_dropped for node in self.nodes.values())
        total_contacts = sum(node.stats.contacts_established for node in self.nodes.values())
        
        delivery_ratio = total_delivered / max(1, total_created)
        
        # Calculate average delivery delay (simplified)
        delivered_bundles = []
        for node in self.nodes.values():
            delivered_bundles.extend([b for b in node.buffer_manager.bundles.values() 
                                    if b.destination == node.node_id])
        
        avg_delay = 0.0
        if delivered_bundles:
            delays = [(self.current_time - b.creation_time) for b in delivered_bundles]
            avg_delay = sum(delays) / len(delays)
            
        # Network overhead (transmissions vs deliveries)
        total_transmissions = sum(node.stats.bundles_forwarded for node in self.nodes.values())
        overhead = total_transmissions / max(1, total_delivered)
        
        node_stats = {node_id: node.get_status() for node_id, node in self.nodes.items()}
        
        return SimulationResults(
            total_bundles_created=total_created,
            total_bundles_delivered=total_delivered,
            total_bundles_dropped=total_dropped,
            total_contacts_established=total_contacts,
            delivery_ratio=delivery_ratio,
            average_delivery_delay=avg_delay,
            network_overhead=overhead,
            simulation_duration=(self.current_time - self.start_time) / 3600,
            node_stats=node_stats
        )
        
    def get_current_status(self) -> Dict[str, Any]:
        """Get current simulation status."""
        return {
            "current_time": self.current_time,
            "elapsed_hours": (self.current_time - self.start_time) / 3600,
            "total_nodes": len(self.nodes),
            "node_status": {node_id: node.get_status() for node_id, node in self.nodes.items()}
        }