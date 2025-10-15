"""
Spray-and-Wait Router (P2-001-A3)
---------------------------------
Implements a copy-limited DTN routing algorithm designed for resource-constrained
satellite networks.

Phases:
- Spray Phase: distribute bundle copies among encountered peers
- Wait Phase: forward only to the destination once copies are reduced to 1

Reference: Spyropoulos et al., “Spray and Wait: An Efficient Routing Scheme
for Intermittently Connected Mobile Networks”.
"""

from typing import Dict, List, Any
from src.routing_epidemic import EpidemicRouter
from src.bundle import Bundle


class SprayAndWaitRouter(EpidemicRouter):
    """
    A DTN router that implements the Spray-and-Wait routing strategy.
    """

    def __init__(self, node_id: str, buffer_manager, initial_copies: int = 10, spray_threshold: int = 1):
        """
        Initialize the router.
        :param node_id: Unique node identifier
        :param buffer_manager: Reference to buffer manager
        :param initial_copies: Initial number of copies assigned to each new bundle
        :param spray_threshold: Copies remaining before switching to Wait phase
        """
        super().__init__(node_id, buffer_manager)
        self.initial_copies = int(initial_copies)
        self.spray_threshold = int(spray_threshold)
        self.copy_table: Dict[str, int] = {}

    # ----------------------------------------------------------------------
    # Core routing interface
    # ----------------------------------------------------------------------
    def route_bundle(self, bundle: Bundle, contacts: List[Any], timestamp: float) -> List[str]:
        """
        Main routing decision logic.
        Determines whether the bundle is in the Spray or Wait phase.
        Returns the list of peer IDs to forward to.
        """
        bundle_id = bundle.id

        # If this is the first time seeing the bundle, initialize copy count
        if bundle_id not in self.copy_table:
            self.copy_table[bundle_id] = self.initial_copies

        remaining = self.copy_table[bundle_id]

        # Spray phase
        if remaining > self.spray_threshold:
            allocation = self.spray_phase_routing(bundle_id, contacts)
            return list(allocation.keys())

        # Wait phase
        return self.wait_phase_routing(bundle, contacts)

    # ----------------------------------------------------------------------
    # Spray phase
    # ----------------------------------------------------------------------
    def spray_phase_routing(self, bundle_id: str, contacts: List[Any], strategy: str = "binary") -> Dict[str, int]:
        """
        Distribute bundle copies among available contacts.
        Supported strategies:
          - "binary": give half the copies to one peer
          - "equal": distribute evenly across all peers
        Returns: {peer_id: copies_allocated}
        """
        peers = [getattr(c, "peer_id", None) for c in contacts if getattr(c, "peer_id", None)]
        if not peers:
            return {}

        remaining = self.copy_table.get(bundle_id, 0)
        if remaining <= self.spray_threshold:
            return {}

        allocation: Dict[str, int] = {}

        # Binary spray (classic)
        if strategy == "binary":
            give = remaining // 2
            if give <= 0:
                return {}
            allocation[peers[0]] = give
            self.copy_table[bundle_id] = remaining - give
            return allocation

        # Equal spray
        if strategy == "equal":
            per_peer = remaining // len(peers)
            if per_peer <= 0:
                # Not enough copies to divide evenly
                for i, peer in enumerate(peers):
                    if i < remaining:
                        allocation[peer] = 1
                self.copy_table[bundle_id] = 0
                return allocation

            for peer in peers:
                allocation[peer] = per_peer
            self.copy_table[bundle_id] = remaining - per_peer * len(peers)
            return allocation

        # Unknown strategy fallback
        return {}

    # ----------------------------------------------------------------------
    # Wait phase
    # ----------------------------------------------------------------------
    def wait_phase_routing(self, bundle: Bundle, contacts: List[Any]) -> List[str]:
        """
        Wait phase: forward only to destination node.
        Returns [destination] if contact is available, else [].
        """
        for contact in contacts:
            peer_id = getattr(contact, "peer_id", None)
            if peer_id and peer_id == getattr(bundle, "destination", None):
                # Transfer custody
                self.copy_table[bundle.id] = 0
                return [peer_id]
        return []

    # ----------------------------------------------------------------------
    # Utility methods
    # ----------------------------------------------------------------------
    def get_remaining_copies(self, bundle_id: str) -> int:
        """Return remaining copies for the given bundle."""
        return int(self.copy_table.get(bundle_id, 0))


__all__ = ["SprayAndWaitRouter"]
