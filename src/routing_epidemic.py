import time
from typing import List, Dict, Set
from src.bundle import Bundle, BundlePriority


class EpidemicRouter:
    """
    Implements the foundational Epidemic Routing algorithm for DTN networks.

    Features:
    - Flooding-based bundle dissemination.
    - Duplicate suppression via summary vectors.
    - Anti-entropy synchronization.
    - TTL and priority-aware transmission ordering.
    """

    def __init__(self, node_id: str, buffer_manager):
        self.node_id = node_id
        self.buffer_manager = buffer_manager
        self.known_bundles: Set[str] = set()  # for duplicate suppression
        self.neighbor_summaries: Dict[str, Dict[str, any]] = {}

    # ----------------------------------------------------------------------
    # ROUTE BUNDLE (Flooding)
    # ----------------------------------------------------------------------
    def route_bundle(self, bundle: Bundle, contacts: List, timestamp: float):
        """
        Flood a bundle to all available contacts unless duplicate suppression applies.
        Returns list of peer_ids the bundle was sent to.
        """
        sent_to = []
        if bundle.id in self.known_bundles:
            # Already sent/received before
            return sent_to

        # Mark as known
        self.known_bundles.add(bundle.id)

        for contact in contacts:
            # Check contact window and link quality before sending
            if self._can_transmit(contact, bundle, timestamp):
                sent_to.append(contact.peer_id)

        return sent_to

   
    # ----------------------------------------------------------------------
    # ANTI-ENTROPY (Summary Vector Exchange)
    # ----------------------------------------------------------------------
    def exchange_summary_vector(self, peer_id: str, contact):
        """
        Perform anti-entropy synchronization between nodes.
        Includes all locally buffered bundles, even if not yet routed.
        Returns a summary vector describing this node's known bundles.
        """
        # Collect all bundle IDs from both buffer manager and known_bundles
        all_known_ids = set(self.known_bundles)

        # Include all stored bundle IDs from buffer manager
        if hasattr(self.buffer_manager, "get_all_bundles"):
            try:
                for bundle in self.buffer_manager.get_all_bundles():
                    all_known_ids.add(bundle.id)
            except Exception:
                pass  # If buffer manager isn't ready, skip safely

        summary_vector = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "owned_bundles": list(all_known_ids),
        }

        self.neighbor_summaries[peer_id] = summary_vector
        return summary_vector


    # ----------------------------------------------------------------------
    # DUPLICATE SUPPRESSION / FLOODING CONTROL
    # ----------------------------------------------------------------------
    def has_seen_bundle(self, bundle_id: str) -> bool:
        """Check if bundle was previously received or forwarded."""
        return bundle_id in self.known_bundles

    # ----------------------------------------------------------------------
    # TRANSMISSION PRIORITY CALCULATION
    # ----------------------------------------------------------------------
    def calculate_transmission_priority(self, bundles: List[Bundle], contact_duration: float):
        """
        Order bundles for transmission based on:
        - Priority (CRITICAL > HIGH > NORMAL > LOW)
        - TTL (lower TTL → higher urgency)
        - Creation time (older first, tie-breaker)
        """
        now = time.time()

        def bundle_sort_key(b: Bundle):
            remaining_ttl = b.remaining_ttl()
            # Lower TTL = higher urgency, so inverse TTL
            return (
                -b.priority.value,     # higher priority first
                remaining_ttl,         # smaller remaining TTL first
                b.creation_time or now
            )

        ordered = sorted(bundles, key=bundle_sort_key)
        return ordered

    # ----------------------------------------------------------------------
    # CONTACT WINDOW / QUALITY CHECK (stub for later)
    # ----------------------------------------------------------------------
    def _can_transmit(self, contact, bundle, timestamp: float) -> bool:
        """
        Determine if we can transmit over a contact window.
        For now: always allow, later integrate link quality + duration.
        """
        if bundle.is_expired():
            return False
        # Could add rate-limiting or capacity control here
        return True
