"""
Epidemic Routing Algorithm

Implements the epidemic routing protocol for DTN where bundles are
replicated to all encountered nodes to maximize delivery probability.
"""

from typing import List, Dict
from datetime import datetime, timedelta
import random

from .base_router import BaseRouter, RoutingDecision
from ...core.bundle import Bundle
from ...orbital.contact_prediction import ContactWindow


class EpidemicRouter(BaseRouter):
    """
    Epidemic routing implementation.
    
    In epidemic routing, each node maintains a summary vector of bundles
    it has seen and exchanges this information with encountered nodes.
    Bundles are replicated to nodes that haven't seen them before.
    """
    
    def __init__(self, node_id: str, buffer_size: int = 10 * 1024 * 1024):
        super().__init__(node_id, buffer_size)
        
        # Epidemic-specific state
        self.summary_vector: Dict[str, datetime] = {}  # bundle_id -> timestamp
        self.anti_entropy_interval = timedelta(minutes=5)
        self.last_anti_entropy = datetime.now()
        
        # Performance tuning parameters
        self.max_replications_per_bundle = 50  # Limit replication spread
        self.replication_counts: Dict[str, int] = {}  # Track replications per bundle
    
    def should_forward(
        self, 
        bundle: Bundle, 
        available_contacts: List[ContactWindow],
        current_time: datetime
    ) -> RoutingDecision:
        """
        Epidemic forwarding decision: replicate to all available neighbors
        that haven't seen the bundle.
        """
        if not available_contacts:
            return RoutingDecision(
                action="store",
                reason="No contacts available"
            )
        
        # Check if bundle has reached replication limit
        replication_count = self.replication_counts.get(bundle.bundle_id, 0)
        if replication_count >= self.max_replications_per_bundle:
            return RoutingDecision(
                action="store",
                reason=f"Replication limit reached ({replication_count})"
            )
        
        # Find the best contact for forwarding
        best_contact = None
        best_priority = -1
        
        for contact in available_contacts:
            # Determine target node
            target_node = None
            if contact.source_id == self.node_id:
                target_node = contact.target_id
            elif contact.target_id == self.node_id:
                target_node = contact.source_id
            else:
                continue  # Contact doesn't involve this node
            
            # Calculate forwarding priority
            priority = self._calculate_forwarding_priority(
                bundle, contact, target_node, current_time
            )
            
            if priority > best_priority:
                best_priority = priority
                best_contact = contact
        
        if best_contact and best_priority > 0:
            target_node = (best_contact.target_id if best_contact.source_id == self.node_id 
                          else best_contact.source_id)
            
            return RoutingDecision(
                action="forward",
                next_hop=target_node,
                reason=f"Epidemic replication (priority: {best_priority:.2f})",
                priority=best_priority,
                contact_window=best_contact
            )
        
        return RoutingDecision(
            action="store",
            reason="No suitable forwarding opportunities"
        )
    
    def _calculate_forwarding_priority(
        self,
        bundle: Bundle,
        contact: ContactWindow,
        target_node: str,
        current_time: datetime
    ) -> float:
        """Calculate priority for forwarding to a specific node."""
        
        # Base priority on contact quality
        priority = contact.data_rate / 100.0  # Normalize data rate
        
        # Boost priority if target is the destination
        if target_node == bundle.destination.ssp:
            priority += 10.0  # High priority for direct delivery
        
        # Boost priority for ground stations (assuming they have better connectivity)
        if target_node.startswith('gs_'):
            priority += 2.0
        
        # Reduce priority if bundle is old (to prioritize fresh bundles)
        age_hours = bundle.age.total_seconds() / 3600
        if age_hours > 1:
            priority *= (1.0 / (1.0 + age_hours))
        
        # Reduce priority if contact duration is very short
        contact_duration = contact.duration_seconds
        if contact_duration < 60:  # Less than 1 minute
            priority *= 0.5
        
        # Add small random factor to break ties
        priority += random.uniform(0, 0.1)
        
        return max(0.0, priority)
    
    def update_routing_info(
        self, 
        contact_plan: List[ContactWindow],
        current_time: datetime
    ):
        """
        Update epidemic routing state with new contact information.
        """
        # Update summary vector with current bundles
        for bundle in self.get_stored_bundles():
            self.summary_vector[bundle.bundle_id] = bundle.creation_timestamp
        
        # Perform anti-entropy session if needed
        if current_time - self.last_anti_entropy >= self.anti_entropy_interval:
            self._perform_anti_entropy_session(current_time)
            self.last_anti_entropy = current_time
        
        # Update replication tracking
        self._update_replication_tracking()
    
    def _perform_anti_entropy_session(self, current_time: datetime):
        """
        Perform anti-entropy session to synchronize bundle information
        with neighboring nodes.
        """
        # In a real implementation, this would exchange summary vectors
        # with neighbors and identify missing bundles
        
        # For simulation, we'll just clean up old summary entries
        cutoff_time = current_time - timedelta(hours=24)
        
        old_entries = [
            bundle_id for bundle_id, timestamp in self.summary_vector.items()
            if timestamp < cutoff_time
        ]
        
        for bundle_id in old_entries:
            del self.summary_vector[bundle_id]
            if bundle_id in self.replication_counts:
                del self.replication_counts[bundle_id]
        
        self.logger.debug(f"Anti-entropy cleanup: removed {len(old_entries)} old entries")
    
    def _update_replication_tracking(self):
        """Update tracking of bundle replications."""
        # Clean up replication counts for bundles no longer in storage
        stored_bundle_ids = {bundle.bundle_id for bundle in self.get_stored_bundles()}
        
        old_replications = [
            bundle_id for bundle_id in self.replication_counts.keys()
            if bundle_id not in stored_bundle_ids
        ]
        
        for bundle_id in old_replications:
            del self.replication_counts[bundle_id]
    
    def forward_bundle(self, bundle: Bundle, next_hop: str) -> bool:
        """
        Forward a bundle to the next hop and update replication tracking.
        """
        # Update replication count
        self.replication_counts[bundle.bundle_id] = (
            self.replication_counts.get(bundle.bundle_id, 0) + 1
        )
        
        # Update metrics
        self.metrics.update_forward()
        
        # Log the forwarding action
        self.logger.info(
            f"Forwarding bundle {bundle.bundle_id} to {next_hop} "
            f"(replication #{self.replication_counts[bundle.bundle_id]})"
        )
        
        return True
    
    def receive_bundle(self, bundle: Bundle, from_node: str = None) -> bool:
        """
        Receive a bundle and update epidemic state.
        """
        # Call parent method for standard bundle handling
        accepted = super().receive_bundle(bundle, from_node)
        
        if accepted:
            # Update summary vector
            self.summary_vector[bundle.bundle_id] = bundle.creation_timestamp
            
            # Initialize replication count if this is a new bundle
            if bundle.bundle_id not in self.replication_counts:
                self.replication_counts[bundle.bundle_id] = 0
        
        return accepted
    
    def get_algorithm_specific_metrics(self) -> Dict[str, any]:
        """Get epidemic-specific performance metrics."""
        base_metrics = self.get_metrics()
        
        epidemic_metrics = {
            'algorithm': 'epidemic',
            'summary_vector_size': len(self.summary_vector),
            'average_replications': 0.0,
            'max_replications': 0,
            'total_replications': sum(self.replication_counts.values())
        }
        
        if self.replication_counts:
            epidemic_metrics['average_replications'] = (
                sum(self.replication_counts.values()) / len(self.replication_counts)
            )
            epidemic_metrics['max_replications'] = max(self.replication_counts.values())
        
        return {**base_metrics, **epidemic_metrics}
    
    def optimize_buffer(self, current_time: datetime):
        """
        Optimize buffer usage by removing less useful bundles.
        In epidemic routing, this might involve removing bundles with
        high replication counts or old bundles.
        """
        if self.get_buffer_utilization() < 90:
            return  # No need to optimize yet
        
        bundles = self.get_stored_bundles()
        if not bundles:
            return
        
        # Sort bundles by "usefulness" (lower is less useful)
        def usefulness_score(bundle: Bundle) -> float:
            age_penalty = bundle.age.total_seconds() / 3600  # Hours
            replication_penalty = self.replication_counts.get(bundle.bundle_id, 0)
            remaining_lifetime = bundle.remaining_lifetime.total_seconds() / 3600
            
            # Lower score = less useful
            score = remaining_lifetime - age_penalty - replication_penalty
            return score
        
        bundles.sort(key=usefulness_score)
        
        # Remove least useful bundles (bottom 20%)
        to_remove = max(1, len(bundles) // 5)
        
        for bundle in bundles[:to_remove]:
            self.remove_bundle(bundle.bundle_id)
            self.logger.debug(f"Removed low-utility bundle {bundle.bundle_id}")
    
    def __str__(self) -> str:
        return f"EpidemicRouter({self.node_id}, summary_size={len(self.summary_vector)})"