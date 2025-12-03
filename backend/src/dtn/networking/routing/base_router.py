"""
Base Router Interface

Abstract base class for DTN routing algorithms with common functionality
and interfaces for bundle forwarding decisions.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timedelta
import logging

from ...core.bundle import Bundle, BundleStore, BundleDropStrategy
from ...orbital.contact_prediction import ContactWindow

logger = logging.getLogger(__name__)


class RoutingMetrics:
    """Routing algorithm performance metrics."""
    
    def __init__(self):
        self.bundles_forwarded = 0
        self.bundles_delivered = 0
        self.bundles_dropped = 0
        self.total_hops = 0
        self.total_delay = 0.0
        self.delivery_ratio = 0.0
        self.overhead_ratio = 0.0
        self.last_updated = datetime.now()
    
    def update_delivery(self, bundle: Bundle, hops: int, delay_seconds: float):
        """Update metrics when a bundle is delivered."""
        self.bundles_delivered += 1
        self.total_hops += hops
        self.total_delay += delay_seconds
        self._recalculate_ratios()
    
    def update_forward(self):
        """Update metrics when a bundle is forwarded."""
        self.bundles_forwarded += 1
        self._recalculate_ratios()
    
    def update_drop(self):
        """Update metrics when a bundle is dropped."""
        self.bundles_dropped += 1
        self._recalculate_ratios()
    
    def _recalculate_ratios(self):
        """Recalculate derived metrics."""
        total_bundles = self.bundles_delivered + self.bundles_dropped
        if total_bundles > 0:
            self.delivery_ratio = self.bundles_delivered / total_bundles
        
        if self.bundles_delivered > 0:
            self.overhead_ratio = (self.bundles_forwarded - self.bundles_delivered) / self.bundles_delivered
        
        self.last_updated = datetime.now()
    
    def get_average_delay(self) -> float:
        """Get average end-to-end delay."""
        if self.bundles_delivered > 0:
            return self.total_delay / self.bundles_delivered
        return 0.0
    
    def get_average_hops(self) -> float:
        """Get average hop count."""
        if self.bundles_delivered > 0:
            return self.total_hops / self.bundles_delivered
        return 0.0


class RoutingDecision:
    """Routing decision for a bundle."""
    
    def __init__(
        self,
        action: str,  # "forward", "store", "drop", "deliver"
        next_hop: Optional[str] = None,
        reason: str = "",
        priority: float = 0.0,
        contact_window: Optional[ContactWindow] = None
    ):
        self.action = action
        self.next_hop = next_hop
        self.reason = reason
        self.priority = priority
        self.contact_window = contact_window
        self.timestamp = datetime.now()


class BaseRouter(ABC):
    """Abstract base class for DTN routing algorithms."""
    
    def __init__(
        self, 
        node_id: str, 
        buffer_size: int = 10 * 1024 * 1024,
        drop_strategy: str = "oldest"
    ):
        self.node_id = node_id
        
        # Convert string to enum
        strategy_map = {
            "oldest": BundleDropStrategy.OLDEST_FIRST,
            "largest": BundleDropStrategy.LARGEST_FIRST,
            "random": BundleDropStrategy.RANDOM,
            "shortest_ttl": BundleDropStrategy.SHORTEST_TTL
        }
        
        bundle_drop_strategy = strategy_map.get(drop_strategy, BundleDropStrategy.OLDEST_FIRST)
        self.bundle_store = BundleStore(max_size=buffer_size, drop_strategy=bundle_drop_strategy)
        self.metrics = RoutingMetrics()
        self.routing_table: Dict[str, Any] = {}
        self.neighbor_nodes: Set[str] = set()
        self.active_contacts: Dict[str, ContactWindow] = {}
        self.contact_history: List[ContactWindow] = []
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{node_id}")
    
    @abstractmethod
    def should_forward(
        self, 
        bundle: Bundle, 
        available_contacts: List[ContactWindow],
        current_time: datetime
    ) -> RoutingDecision:
        """
        Decide whether and where to forward a bundle.
        
        Args:
            bundle: The bundle to route
            available_contacts: Currently available contact windows
            current_time: Current simulation time
            
        Returns:
            RoutingDecision with action and next hop
        """
        pass
    
    @abstractmethod
    def update_routing_info(
        self, 
        contact_plan: List[ContactWindow],
        current_time: datetime
    ):
        """
        Update routing information based on contact plan.
        
        Args:
            contact_plan: List of predicted contact windows
            current_time: Current simulation time
        """
        pass
    
    def receive_bundle(self, bundle: Bundle, from_node: str = None) -> bool:
        """
        Receive a bundle from another node.
        
        Args:
            bundle: The received bundle
            from_node: Node that sent the bundle
            
        Returns:
            True if bundle was accepted, False otherwise
        """
        # Check if bundle is for this node
        if bundle.destination.ssp == self.node_id:
            self.logger.info(f"Bundle {bundle.bundle_id} delivered to {self.node_id}")
            self.metrics.update_delivery(
                bundle, 
                bundle.hop_count, 
                bundle.age.total_seconds()
            )
            return True
        
        # Check if we already have this bundle
        if self.bundle_store.retrieve(bundle.bundle_id):
            self.logger.debug(f"Bundle {bundle.bundle_id} already stored")
            return False
        
        # Try to store the bundle
        if self.bundle_store.store(bundle):
            bundle.add_hop(self.node_id)
            self.logger.debug(f"Stored bundle {bundle.bundle_id} from {from_node}")
            return True
        else:
            self.logger.warning(f"Failed to store bundle {bundle.bundle_id} - buffer full")
            self.metrics.update_drop()
            return False
    
    def get_stored_bundles(self) -> List[Bundle]:
        """Get all stored bundles."""
        return self.bundle_store.get_all_bundles()
    
    def remove_bundle(self, bundle_id: str) -> bool:
        """Remove a bundle from storage."""
        return self.bundle_store.remove(bundle_id)
    
    def cleanup_expired_bundles(self) -> int:
        """Remove expired bundles and return count."""
        expired_count = self.bundle_store.cleanup_expired()
        self.metrics.bundles_dropped += expired_count
        return expired_count
    
    def update_contacts(
        self, 
        active_contacts: List[ContactWindow],
        current_time: datetime
    ):
        """Update active contact information."""
        # Update active contacts
        self.active_contacts = {
            contact.contact_id: contact 
            for contact in active_contacts
            if (contact.source_id == self.node_id or contact.target_id == self.node_id)
        }
        
        # Update neighbor list
        self.neighbor_nodes = set()
        for contact in self.active_contacts.values():
            if contact.source_id == self.node_id:
                self.neighbor_nodes.add(contact.target_id)
            elif contact.target_id == self.node_id:
                self.neighbor_nodes.add(contact.source_id)
        
        # Update contact history
        for contact in active_contacts:
            if contact.end_time <= current_time and contact not in self.contact_history:
                self.contact_history.append(contact)
    
    def get_contact_to_node(self, target_node: str) -> Optional[ContactWindow]:
        """Get active contact to a specific node."""
        for contact in self.active_contacts.values():
            if ((contact.source_id == self.node_id and contact.target_id == target_node) or
                (contact.target_id == self.node_id and contact.source_id == target_node)):
                return contact
        return None
    
    def calculate_delivery_probability(
        self, 
        destination: str,
        current_time: datetime
    ) -> float:
        """Calculate probability of successful delivery to destination."""
        # Base implementation - can be overridden by specific algorithms
        if destination in self.neighbor_nodes:
            return 1.0
        
        # Look at historical contact patterns
        recent_contacts = [
            c for c in self.contact_history
            if (current_time - c.end_time).total_seconds() < 3600  # Last hour
        ]
        
        destination_contacts = [
            c for c in recent_contacts
            if destination in [c.source_id, c.target_id]
        ]
        
        if destination_contacts:
            return min(1.0, len(destination_contacts) / 10.0)  # Simple heuristic
        
        return 0.1  # Default low probability
    
    def get_buffer_utilization(self) -> float:
        """Get current buffer utilization percentage."""
        return self.bundle_store.utilization
    
    def get_buffer_info(self) -> Dict[str, Any]:
        """Get detailed buffer information including drop strategy."""
        return self.bundle_store.get_drop_strategy_info()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get routing performance metrics."""
        return {
            'node_id': self.node_id,
            'bundles_forwarded': self.metrics.bundles_forwarded,
            'bundles_delivered': self.metrics.bundles_delivered,
            'bundles_dropped': self.metrics.bundles_dropped,
            'delivery_ratio': self.metrics.delivery_ratio,
            'overhead_ratio': self.metrics.overhead_ratio,
            'average_delay': self.metrics.get_average_delay(),
            'average_hops': self.metrics.get_average_hops(),
            'buffer_utilization': self.get_buffer_utilization(),
            'active_contacts': len(self.active_contacts),
            'neighbor_count': len(self.neighbor_nodes)
        }
    
    def reset_metrics(self):
        """Reset all routing metrics."""
        self.metrics = RoutingMetrics()
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.node_id})"