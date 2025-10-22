"""
DTN Node Implementation

Complete DTN node with routing, buffer management, and contact handling.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .bundle import Bundle, BundlePriority, BufferManager, Contact
from ..routing.routing_epidemic import EpidemicRouter
from ..routing.routing_prophet import PROPHETRouter

logger = logging.getLogger(__name__)


@dataclass
class NodeStats:
    """Statistics for a DTN node."""
    bundles_created: int = 0
    bundles_received: int = 0
    bundles_delivered: int = 0
    bundles_forwarded: int = 0
    bundles_dropped: int = 0
    contacts_established: int = 0
    
    
class DTNNode:
    """
    Complete DTN node implementation with routing and buffer management.
    """
    
    def __init__(self, node_id: str, routing_algorithm: str = "epidemic", 
                 buffer_size_mb: int = 20):
        self.node_id = node_id
        self.buffer_manager = BufferManager(buffer_size_mb)
        self.contacts: Dict[str, Contact] = {}
        self.stats = NodeStats()
        
        # Initialize router based on algorithm
        if routing_algorithm.lower() == "prophet":
            self.router = PROPHETRouter(node_id, self.buffer_manager)
        else:
            self.router = EpidemicRouter(node_id, self.buffer_manager)
            
        logger.info(f"DTN Node {node_id} initialized with {routing_algorithm} routing")
        
    def create_bundle(self, destination: str, payload: bytes, 
                     ttl_seconds: int = 3600, priority: BundlePriority = BundlePriority.NORMAL) -> Bundle:
        """Create a new bundle for transmission."""
        bundle = Bundle(
            source=self.node_id,
            destination=destination,
            payload=payload,
            ttl_seconds=ttl_seconds,
            priority=priority
        )
        
        self.buffer_manager.add_bundle(bundle)
        self.stats.bundles_created += 1
        logger.debug(f"Node {self.node_id} created bundle {bundle.id} for {destination}")
        return bundle
        
    def receive_bundle(self, bundle: Bundle) -> bool:
        """Receive a bundle from another node."""
        self.stats.bundles_received += 1
        
        if bundle.destination == self.node_id:
            # Bundle delivered to final destination
            self.stats.bundles_delivered += 1
            logger.info(f"Node {self.node_id} delivered bundle {bundle.id}")
            return True
        else:
            # Store for forwarding
            if self.buffer_manager.add_bundle(bundle):
                logger.debug(f"Node {self.node_id} stored bundle {bundle.id} for forwarding")
                return True
            else:
                self.stats.bundles_dropped += 1
                logger.warning(f"Node {self.node_id} dropped bundle {bundle.id} - buffer full")
                return False
                
    def add_contact(self, contact: Contact):
        """Add a contact opportunity."""
        contact_key = f"{contact.source}_{contact.destination}_{contact.start_time}"
        self.contacts[contact_key] = contact
        self.stats.contacts_established += 1
        
    def process_contacts(self, current_time: float) -> Dict[str, List[str]]:
        """Process all active contacts and forward bundles."""
        active_contacts = [c for c in self.contacts.values() if c.is_active(current_time)]
        forwarding_results = {}
        
        for bundle in list(self.buffer_manager.bundles.values()):
            if bundle.is_expired():
                self.buffer_manager.remove_bundle(bundle.id)
                self.stats.bundles_dropped += 1
                continue
                
            # Try to forward bundle using routing algorithm
            transmitted_to = self.router.route_bundle(bundle, active_contacts, current_time)
            if transmitted_to:
                forwarding_results[bundle.id] = transmitted_to
                self.stats.bundles_forwarded += len(transmitted_to)
                
        # Clean up expired bundles
        expired_count = self.buffer_manager.cleanup_expired()
        self.stats.bundles_dropped += expired_count
        
        return forwarding_results
        
    def get_status(self) -> Dict[str, Any]:
        """Get current node status."""
        return {
            "node_id": self.node_id,
            "router_type": type(self.router).__name__,
            "buffer_stats": self.buffer_manager.get_stats(),
            "router_stats": self.router.get_stats(),
            "node_stats": {
                "bundles_created": self.stats.bundles_created,
                "bundles_received": self.stats.bundles_received,
                "bundles_delivered": self.stats.bundles_delivered,
                "bundles_forwarded": self.stats.bundles_forwarded,
                "bundles_dropped": self.stats.bundles_dropped,
                "contacts_established": self.stats.contacts_established,
            },
            "active_contacts": len([c for c in self.contacts.values() 
                                  if c.is_active(time.time())]),
            "timestamp": time.time()
        }
        
    def simulate_step(self, current_time: float) -> Dict[str, Any]:
        """Execute one simulation step."""
        results = self.process_contacts(current_time)
        
        # Update router-specific logic
        if isinstance(self.router, PROPHETRouter):
            # Age predictabilities for PRoPHET
            if hasattr(self.router, 'last_update'):
                time_elapsed = current_time - self.router.last_update
                self.router.age_delivery_predictabilities(time_elapsed)
                self.router.last_update = current_time
                
        return {
            "node_id": self.node_id,
            "forwarding_results": results,
            "status": self.get_status(),
            "timestamp": current_time
        }