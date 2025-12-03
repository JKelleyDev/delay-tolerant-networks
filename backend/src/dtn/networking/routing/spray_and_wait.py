"""
Spray and Wait Routing Algorithm

Implements the Spray and Wait protocol where a limited number of copies
of each bundle are initially distributed (spray phase), followed by
direct delivery only (wait phase).
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import math

from .base_router import BaseRouter, RoutingDecision
from ...core.bundle import Bundle
from ...orbital.contact_prediction import ContactWindow


class SprayAndWaitRouter(BaseRouter):
    """
    Spray and Wait routing implementation.
    
    The algorithm operates in two phases:
    1. Spray Phase: Distribute L copies of each bundle to L distinct nodes
    2. Wait Phase: Each node carrying a copy performs direct delivery only
    
    This provides a good trade-off between delivery probability and overhead.
    """
    
    def __init__(self, node_id: str, buffer_size: int = 10 * 1024 * 1024, spray_copies: int = 6, drop_strategy: str = "oldest"):
        super().__init__(node_id, buffer_size, drop_strategy)
        
        # Spray and Wait parameters
        self.L = spray_copies  # Initial number of copies to spray
        self.binary_spray = True  # Use binary spray variant for better performance
        
        # State tracking
        self.bundle_copies: Dict[str, int] = {}  # bundle_id -> copies remaining
        self.spray_phase: Dict[str, bool] = {}  # bundle_id -> in spray phase
        self.bundle_hop_counts: Dict[str, int] = {}  # bundle_id -> hops taken
        
        # Performance tracking
        self.total_sprayed_bundles = 0
        self.total_wait_deliveries = 0
    
    def should_forward(
        self, 
        bundle: Bundle, 
        available_contacts: List[ContactWindow],
        current_time: datetime
    ) -> RoutingDecision:
        """
        Spray and Wait forwarding decision based on current phase.
        """
        if not available_contacts:
            return RoutingDecision(
                action="store",
                reason="No contacts available"
            )
        
        bundle_id = bundle.bundle_id
        destination = bundle.destination.ssp
        
        # Initialize bundle state if not seen before
        if bundle_id not in self.bundle_copies:
            self.bundle_copies[bundle_id] = self.L
            self.spray_phase[bundle_id] = True
            self.bundle_hop_counts[bundle_id] = bundle.hop_count
        
        copies_remaining = self.bundle_copies[bundle_id]
        in_spray_phase = self.spray_phase[bundle_id]
        
        # Check for direct delivery opportunity
        direct_contact = self._find_direct_contact(destination, available_contacts)
        if direct_contact:
            return RoutingDecision(
                action="forward",
                next_hop=destination,
                reason="Direct delivery to destination",
                priority=10.0,  # Highest priority
                contact_window=direct_contact
            )
        
        # Spray phase: distribute copies
        if in_spray_phase and copies_remaining > 1:
            best_contact = self._select_spray_target(
                bundle, available_contacts, current_time
            )
            
            if best_contact:
                target_node = (best_contact.target_id if best_contact.source_id == self.node_id 
                              else best_contact.source_id)
                
                # Calculate copies to give based on spray strategy
                copies_to_give = self._calculate_copies_to_give(copies_remaining)
                
                return RoutingDecision(
                    action="forward",
                    next_hop=target_node,
                    reason=f"Spray phase: giving {copies_to_give} copies ({copies_remaining-copies_to_give} remaining)",
                    priority=5.0 + (copies_remaining / self.L),  # Higher priority for more copies
                    contact_window=best_contact
                )
        
        # Wait phase: only direct delivery
        return RoutingDecision(
            action="store",
            reason=f"Wait phase: holding {copies_remaining} copies, waiting for direct contact"
        )
    
    def _find_direct_contact(
        self, 
        destination: str, 
        available_contacts: List[ContactWindow]
    ) -> ContactWindow:
        """Find direct contact to destination."""
        for contact in available_contacts:
            if ((contact.source_id == self.node_id and contact.target_id == destination) or
                (contact.target_id == self.node_id and contact.source_id == destination)):
                return contact
        return None
    
    def _select_spray_target(
        self,
        bundle: Bundle,
        available_contacts: List[ContactWindow],
        current_time: datetime
    ) -> ContactWindow:
        """Select best target for spraying copies."""
        
        best_contact = None
        best_score = -1
        
        for contact in available_contacts:
            # Determine target node
            target_node = None
            if contact.source_id == self.node_id:
                target_node = contact.target_id
            elif contact.target_id == self.node_id:
                target_node = contact.source_id
            else:
                continue
            
            # Score potential targets
            score = self._calculate_spray_score(bundle, target_node, contact, current_time)
            
            if score > best_score:
                best_score = score
                best_contact = contact
        
        return best_contact
    
    def _calculate_spray_score(
        self,
        bundle: Bundle,
        target_node: str,
        contact: ContactWindow,
        current_time: datetime
    ) -> float:
        """Calculate score for spraying to a target node."""
        
        score = 0.0
        
        # Prefer nodes we haven't given copies to recently
        # (In a real implementation, would track this properly)
        score += 1.0
        
        # Prefer ground stations (better connectivity)
        if target_node.startswith('gs_'):
            score += 2.0
        
        # Prefer longer contact windows (more reliable transfer)
        contact_duration = contact.duration_seconds
        if contact_duration > 300:  # > 5 minutes
            score += 1.0
        elif contact_duration < 60:  # < 1 minute
            score -= 0.5
        
        # Prefer higher data rate contacts
        score += contact.data_rate / 100.0  # Normalize data rate
        
        # Avoid spraying to nodes that are likely to be encountered again soon
        # (In satellite networks, this could use orbital prediction)
        # For now, use simple heuristic
        if target_node.startswith('sat_'):
            # Satellites in LEO are encountered frequently
            score += 0.5
        
        return max(0.0, score)
    
    def _calculate_copies_to_give(self, copies_remaining: int) -> int:
        """Calculate how many copies to give in spray phase."""
        if self.binary_spray:
            # Binary spray: give half the copies
            return max(1, copies_remaining // 2)
        else:
            # Normal spray: give one copy
            return 1
    
    def forward_bundle(self, bundle: Bundle, next_hop: str, copies_given: int = None) -> bool:
        """
        Forward bundle and update spray state.
        """
        bundle_id = bundle.bundle_id
        
        if bundle_id in self.bundle_copies:
            if copies_given is None:
                copies_given = self._calculate_copies_to_give(self.bundle_copies[bundle_id])
            
            # Update copy count
            self.bundle_copies[bundle_id] -= copies_given
            
            # Check if we should enter wait phase
            if self.bundle_copies[bundle_id] <= 1:
                self.spray_phase[bundle_id] = False
            
            # Update statistics
            if self.spray_phase[bundle_id]:
                self.total_sprayed_bundles += 1
            
            self.logger.info(
                f"Forwarded bundle {bundle_id} to {next_hop}, "
                f"gave {copies_given} copies, {self.bundle_copies[bundle_id]} remaining"
            )
        
        # Update parent metrics
        self.metrics.update_forward()
        return True
    
    def receive_bundle(self, bundle: Bundle, from_node: str = None) -> bool:
        """
        Receive bundle and initialize spray state.
        """
        # Call parent method
        accepted = super().receive_bundle(bundle, from_node)
        
        if accepted and bundle.destination.ssp != self.node_id:
            bundle_id = bundle.bundle_id
            
            # For received bundles, we get 1 copy in wait phase unless specified
            if bundle_id not in self.bundle_copies:
                # This is likely a sprayed copy
                self.bundle_copies[bundle_id] = 1
                self.spray_phase[bundle_id] = False  # Received copies start in wait phase
                self.bundle_hop_counts[bundle_id] = bundle.hop_count
        
        return accepted
    
    def update_routing_info(
        self, 
        contact_plan: List[ContactWindow],
        current_time: datetime
    ):
        """
        Update Spray and Wait routing information.
        """
        # Clean up state for old bundles
        self._cleanup_old_bundle_state()
        
        # Update wait phase statistics
        wait_bundles = sum(
            1 for bundle_id, in_spray in self.spray_phase.items()
            if not in_spray
        )
        
        self.logger.debug(
            f"Spray and Wait state: {len(self.bundle_copies)} tracked bundles, "
            f"{wait_bundles} in wait phase"
        )
    
    def _cleanup_old_bundle_state(self):
        """Clean up state for bundles no longer in storage."""
        stored_bundle_ids = {bundle.bundle_id for bundle in self.get_stored_bundles()}
        
        old_bundles = [
            bundle_id for bundle_id in self.bundle_copies.keys()
            if bundle_id not in stored_bundle_ids
        ]
        
        for bundle_id in old_bundles:
            if bundle_id in self.bundle_copies:
                del self.bundle_copies[bundle_id]
            if bundle_id in self.spray_phase:
                del self.spray_phase[bundle_id]
            if bundle_id in self.bundle_hop_counts:
                del self.bundle_hop_counts[bundle_id]
    
    def get_algorithm_specific_metrics(self) -> Dict[str, any]:
        """Get Spray and Wait specific metrics."""
        base_metrics = self.get_metrics()
        
        spray_bundles = sum(1 for in_spray in self.spray_phase.values() if in_spray)
        wait_bundles = sum(1 for in_spray in self.spray_phase.values() if not in_spray)
        
        total_copies = sum(self.bundle_copies.values())
        avg_copies = total_copies / len(self.bundle_copies) if self.bundle_copies else 0
        
        spray_metrics = {
            'algorithm': 'spray_and_wait',
            'spray_copies_L': self.L,
            'binary_spray': self.binary_spray,
            'bundles_in_spray_phase': spray_bundles,
            'bundles_in_wait_phase': wait_bundles,
            'total_copies_held': total_copies,
            'average_copies_per_bundle': avg_copies,
            'total_sprayed_bundles': self.total_sprayed_bundles,
            'total_wait_deliveries': self.total_wait_deliveries
        }
        
        return {**base_metrics, **spray_metrics}
    
    def get_bundle_copy_info(self) -> Dict[str, Dict[str, any]]:
        """Get detailed information about bundle copies."""
        info = {}
        for bundle_id, copies in self.bundle_copies.items():
            info[bundle_id] = {
                'copies_remaining': copies,
                'in_spray_phase': self.spray_phase.get(bundle_id, False),
                'hop_count': self.bundle_hop_counts.get(bundle_id, 0)
            }
        return info
    
    def optimize_buffer(self, current_time: datetime):
        """
        Optimize buffer by prioritizing bundles in spray phase.
        """
        if self.get_buffer_utilization() < 90:
            return
        
        bundles = self.get_stored_bundles()
        if not bundles:
            return
        
        # Sort bundles by priority (lower score = more likely to drop)
        def priority_score(bundle: Bundle) -> float:
            bundle_id = bundle.bundle_id
            
            # Expired bundles have lowest priority
            if bundle.is_expired:
                return -1.0
            
            # Bundles in spray phase have higher priority
            if self.spray_phase.get(bundle_id, False):
                copies = self.bundle_copies.get(bundle_id, 1)
                return 10.0 + copies  # Higher priority for more copies
            
            # Wait phase bundles
            remaining_lifetime = bundle.remaining_lifetime.total_seconds() / 3600
            return remaining_lifetime
        
        bundles.sort(key=priority_score)
        
        # Remove lowest priority bundles (bottom 20%)
        to_remove = max(1, len(bundles) // 5)
        
        for bundle in bundles[:to_remove]:
            bundle_id = bundle.bundle_id
            phase = "spray" if self.spray_phase.get(bundle_id, False) else "wait"
            copies = self.bundle_copies.get(bundle_id, 1)
            
            self.remove_bundle(bundle_id)
            self.logger.debug(
                f"Removed buffer-pressure bundle {bundle_id} "
                f"(phase: {phase}, copies: {copies})"
            )
    
    def __str__(self) -> str:
        spray_count = sum(1 for in_spray in self.spray_phase.values() if in_spray)
        wait_count = len(self.spray_phase) - spray_count
        return f"SprayAndWaitRouter({self.node_id}, L={self.L}, spray={spray_count}, wait={wait_count})"