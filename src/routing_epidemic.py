from typing import Dict, List, Set, Any
from src.bundle import Bundle


class EpidemicRouter:
    """
    Basic Epidemic Routing implementation.
    Floods bundles to all available contacts with duplicate suppression
    and simple summary vector (anti-entropy) exchange.
    """

    def __init__(self, node_id: str, buffer_manager):
        self.node_id = node_id
        self.buffer_manager = buffer_manager
        self.seen_bundles: Set[str] = set()
        self.routing_table: Dict[str, List[Bundle]] = {}

    def route_bundle(
        self, bundle: Bundle, contacts: List["Contact"], timestamp: float = 0.0
    ):
        """Flood the bundle to all available contacts except duplicates."""
        if bundle.id is None:
            return []
        if bundle.id in self.seen_bundles:
            return []

        self.seen_bundles.add(bundle.id)
        sent = []
        for contact in contacts:
            if self._contact_available(contact):
                self._send_bundle(bundle, contact)
                sent.append(contact.peer_id)
        return sent

    def exchange_summary_vector(
        self, peer_id: str, contact: "Contact"
    ) -> Dict[str, Any]:
        """
        Simulate anti-entropy summary vector exchange.
        Returns local summary vector for testing.
        """
        owned = [b.id for b in self.buffer_manager.bundles if b.id is not None]
        return {"node_id": self.node_id, "owned_bundles": owned}

    def calculate_transmission_priority(self, bundle: Bundle) -> int:
        """Prioritize bundles based on TTL and priority level."""
        ttl = bundle.remaining_ttl()
        base_priority = bundle.priority.value
        return base_priority * 1000 + ttl

    def _send_bundle(self, bundle: Bundle, contact: "Contact"):
        """Placeholder for sending logic."""
        contact.receive_bundle(bundle)

    def _contact_available(self, contact: "Contact") -> bool:
        """Simulate contact availability."""
        return hasattr(contact, "peer_id")


# Dummy Contact for testing
class Contact:
    def __init__(self, peer_id: str):
        self.peer_id = peer_id
        self.received: List[Bundle] = []

    def receive_bundle(self, bundle: Bundle):
        self.received.append(bundle)
