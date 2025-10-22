from typing import Dict, List, Set, Any
from ..core.bundle import Bundle, Contact, BufferManager
import time


class EpidemicRouter:
    """
    Epidemic Routing implementation for DTN.
    Floods bundles to all available contacts with duplicate suppression.
    """

    def __init__(self, node_id: str, buffer_manager: BufferManager):
        self.node_id = node_id
        self.buffer_manager = buffer_manager
        self.seen_bundles: Set[str] = set()
        self.delivery_count = 0
        self.transmission_count = 0

    def route_bundle(self, bundle: Bundle, contacts: List[Contact], current_time: float) -> List[str]:
        """Flood the bundle to all available contacts."""
        if not bundle.validate() or bundle.id in self.seen_bundles:
            return []

        self.seen_bundles.add(bundle.id)
        transmitted_to = []
        
        for contact in contacts:
            if self._can_use_contact(contact, current_time):
                if contact.can_transmit(bundle, current_time):
                    if contact.transmit_bundle(bundle):
                        transmitted_to.append(contact.destination)
                        self.transmission_count += 1
                        
        return transmitted_to

    def _can_use_contact(self, contact: Contact, current_time: float) -> bool:
        """Check if contact is available for transmission."""
        return (contact.source == self.node_id and 
                contact.is_active(current_time) and
                contact.destination != self.node_id)
    
    def receive_bundle(self, bundle: Bundle) -> bool:
        """Receive and store a bundle."""
        if bundle.destination == self.node_id:
            self.delivery_count += 1
            return True
        return self.buffer_manager.add_bundle(bundle)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return {
            "algorithm": "Epidemic",
            "node_id": self.node_id,
            "seen_bundles": len(self.seen_bundles),
            "delivery_count": self.delivery_count,
            "transmission_count": self.transmission_count,
            "buffer_stats": self.buffer_manager.get_stats()
        }

    def exchange_summary_vector(self, peer_id: str) -> Dict[str, Any]:
        """
        Generate summary vector for anti-entropy exchange.
        Returns list of bundle IDs this node has.
        """
        owned = [b.id for b in self.buffer_manager.bundles.values() if b.id is not None]
        return {"node_id": self.node_id, "owned_bundles": owned}

    def calculate_transmission_priority(self, bundle: Bundle) -> int:
        """Prioritize bundles based on TTL and priority level."""
        ttl = bundle.remaining_ttl()
        base_priority = bundle.priority.value
        return base_priority * 1000 + ttl
