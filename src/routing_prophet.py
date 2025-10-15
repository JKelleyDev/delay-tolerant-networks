"""
PRoPHET (Probabilistic Routing Protocol using History of Encounters and Transitivity)
Implements RFC 6693-compliant delivery predictability updates.
"""

import time
import math
from typing import Dict, Any, List
from src.bundle import Bundle
from src.routing_epidemic import EpidemicRouter


class PROPHETRouter(EpidemicRouter):
    def __init__(
        self,
        node_id: str,
        buffer_manager,
        p_encounter_max: float = 0.75,
        beta: float = 0.25,
        gamma: float = 0.98,
        delta: float = 0.01,
    ):
        super().__init__(node_id, buffer_manager)
        self.p_encounter_max = float(p_encounter_max)
        self.beta = float(beta)
        self.gamma = float(gamma)
        self.delta = float(delta)
        self.delivery_predictability: Dict[str, float] = {}
        self.last_update_time: float = time.time()

    # ---------------------------
    # Delivery Predictability Updates
    # ---------------------------
    def update_delivery_predictability(self, peer_id: str):
        """Update predictability when encountering a peer."""
        old_p = self.delivery_predictability.get(peer_id, 0.0)
        new_p = old_p + (1 - old_p) * self.p_encounter_max
        self.delivery_predictability[peer_id] = self._clamp_probability(new_p)

    def age_delivery_predictabilities(self):
        """Apply time-based aging to all predictabilities."""
        current_time = time.time()
        delta_t = max(1, current_time - self.last_update_time)
        self.last_update_time = current_time

        for peer in list(self.delivery_predictability.keys()):
            old_p = self.delivery_predictability[peer]
            aged_p = old_p * (self.gamma ** delta_t)
            self.delivery_predictability[peer] = self._clamp_probability(aged_p)

    def transitivity_update(self, peer_id: str, peer_table: Dict[str, float]):
        """Apply transitivity: update delivery predictabilities via a peer."""
        if peer_id not in self.delivery_predictability:
            self.delivery_predictability[peer_id] = self.delta

        p_ab = self.delivery_predictability[peer_id]

        for c, p_bc in peer_table.items():
            if c == self.node_id:
                continue

            old_p_ac = self.delivery_predictability.get(c, 0.0)
            new_p_ac = old_p_ac + (1 - old_p_ac) * p_ab * p_bc * self.beta
            self.delivery_predictability[c] = self._clamp_probability(new_p_ac)

    # ---------------------------
    # Routing Logic
    # ---------------------------
    def route_bundle(self, bundle: Bundle, contacts: List[Any], timestamp: float) -> List[str]:
        """
        Select next hop based on highest delivery predictability.
        Returns a list of peer IDs (even if only one) for consistency with test expectations.
        """
        best_peer = None
        best_p = self.delta

        for contact in contacts:
            peer_id = getattr(contact, "peer_id", None)
            if not peer_id:
                continue
            p = self.delivery_predictability.get(peer_id, self.delta)
            if p > best_p:
                best_peer = peer_id
                best_p = p

        # Return list for compatibility with test
        return [best_peer] if best_peer else []

    # ---------------------------
    # Helper Methods
    # ---------------------------
    def get_predictability(self, peer_id: str) -> float:
        """Return predictability (clamped) for a peer."""
        return self._clamp_probability(self.delivery_predictability.get(peer_id, 0.0))

    def _clamp_probability(self, value: float) -> float:
        """Ensure probability stays within [0, 1]."""
        return max(0.0, min(1.0, value))
