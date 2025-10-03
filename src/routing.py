"""
DTN Routing Infrastructure for Delay-Tolerant Networks

This module provides the core routing infrastructure including:
- Base Router protocol/interface
- DTN Routing Manager
- Router factory pattern
- Bundle prioritization framework
- Common routing utilities

Implements routing algorithms: Epidemic, PRoPHET, Spray-and-Wait
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Protocol
from dataclasses import dataclass, field
from enum import Enum
import time
import logging
from collections import defaultdict, deque

try:
    from .bundle import Bundle, BundlePriority
    from .contact_prediction import ContactWindow, ContactPredictor
except ImportError:
    # Handle case when module is imported directly
    from bundle import Bundle, BundlePriority  # type: ignore
    from contact_prediction import ContactWindow, ContactPredictor  # type: ignore


class RoutingAlgorithm(Enum):
    """Supported DTN routing algorithms"""

    EPIDEMIC = "epidemic"
    PROPHET = "prophet"
    SPRAY_AND_WAIT = "spray_and_wait"


@dataclass
class RoutingConfig:
    """Configuration for routing algorithms"""

    algorithm: RoutingAlgorithm = RoutingAlgorithm.EPIDEMIC

    # Epidemic routing parameters
    epidemic_anti_entropy: bool = True
    epidemic_max_flood_rate: float = 10.0  # bundles per second

    # PRoPHET routing parameters
    prophet_p_encounter_max: float = 0.75
    prophet_beta: float = 0.25
    prophet_gamma: float = 0.98
    prophet_delta: float = 0.01

    # Spray-and-Wait parameters
    spray_initial_copies: int = 10
    spray_threshold: int = 1

    # Global routing parameters
    max_bundle_ttl_hours: float = 168.0  # 7 days
    priority_queue_enabled: bool = True
    contact_lookahead_hours: float = 24.0
    routing_decision_timeout_ms: float = 50.0


@dataclass
class RoutingMetrics:
    """Routing performance metrics"""

    bundles_forwarded: int = 0
    routing_decisions: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    total_delay_seconds: float = 0.0
    total_overhead_bytes: int = 0
    algorithm_switches: int = 0

    # Per-algorithm metrics
    algorithm_performance: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: defaultdict(dict)
    )
    delivery_ratios: Dict[str, float] = field(default_factory=dict)
    average_delays: Dict[str, float] = field(default_factory=dict)
    overhead_ratios: Dict[str, float] = field(default_factory=dict)


class BufferManager(Protocol):
    """Protocol for buffer management interface"""

    def store_bundle(self, bundle: Bundle) -> bool:
        """Store bundle in buffer, return True if successful"""
        ...

    def retrieve_bundle(self, bundle_id: str) -> Optional[Bundle]:
        """Retrieve bundle by ID"""
        ...

    def get_all_bundles(self) -> List[Bundle]:
        """Get all stored bundles"""
        ...

    def remove_bundle(self, bundle_id: str) -> bool:
        """Remove bundle from buffer"""
        ...

    def get_buffer_utilization(self) -> float:
        """Get buffer utilization as percentage (0.0-1.0)"""
        ...

    def get_available_space(self) -> int:
        """Get available buffer space in bytes"""
        ...


class Router(ABC):
    """Abstract base class for DTN routing algorithms"""

    def __init__(self, node_id: str, buffer_manager: BufferManager):
        self.node_id = node_id
        self.buffer_manager = buffer_manager
        self.metrics = RoutingMetrics()
        self.logger = logging.getLogger(f"Router-{self.__class__.__name__}-{node_id}")

    @abstractmethod
    def route_bundle(
        self, bundle: Bundle, available_contacts: List[ContactWindow], timestamp: float
    ) -> Optional[str]:
        """
        Route a bundle to next hop

        Args:
            bundle: Bundle to route
            available_contacts: Current available contact windows
            timestamp: Current timestamp

        Returns:
            Node ID of next hop, or None if no route available
        """
        pass

    @abstractmethod
    def update_state(
        self,
        encountered_node: str,
        timestamp: float,
        contact_window: Optional[ContactWindow] = None,
    ) -> None:
        """
        Update routing algorithm state on contact with another node

        Args:
            encountered_node: ID of encountered node
            timestamp: Contact timestamp
            contact_window: Optional contact window information
        """
        pass

    def validate_bundle(self, bundle: Bundle) -> bool:
        """Validate bundle for routing"""
        if not bundle.validate():
            return False
        if bundle.is_expired():
            self.logger.debug(f"Bundle {bundle.id} expired, TTL exceeded")
            return False
        return True

    def filter_contacts_by_destination(
        self, contacts: List[ContactWindow], destination: str
    ) -> List[ContactWindow]:
        """Filter contacts that can reach destination"""
        # For now, return all contacts as any satellite might be useful
        # In practice, this would use topology knowledge
        return contacts

    def calculate_contact_utility(
        self, contact: ContactWindow, bundle: Bundle
    ) -> float:
        """Calculate utility of a contact for bundle forwarding"""
        base_utility = contact.duration_seconds * contact.max_data_rate_mbps

        # Priority boost
        priority_multiplier = {
            BundlePriority.LOW: 0.5,
            BundlePriority.NORMAL: 1.0,
            BundlePriority.HIGH: 2.0,
            BundlePriority.CRITICAL: 5.0,
        }

        utility = base_utility * priority_multiplier.get(bundle.priority, 1.0)

        # TTL penalty
        remaining_ttl_ratio = bundle.remaining_ttl() / bundle.ttl_seconds
        utility *= remaining_ttl_ratio

        return utility


class PriorityQueue:
    """Priority-based bundle queue for transmission scheduling"""

    def __init__(self):
        self.queues = {
            BundlePriority.CRITICAL: deque(),
            BundlePriority.HIGH: deque(),
            BundlePriority.NORMAL: deque(),
            BundlePriority.LOW: deque(),
        }

    def enqueue(self, bundle: Bundle) -> None:
        """Add bundle to appropriate priority queue"""
        self.queues[bundle.priority].append(bundle)

    def dequeue(self) -> Optional[Bundle]:
        """Remove and return highest priority bundle"""
        for priority in [
            BundlePriority.CRITICAL,
            BundlePriority.HIGH,
            BundlePriority.NORMAL,
            BundlePriority.LOW,
        ]:
            if self.queues[priority]:
                return self.queues[priority].popleft()
        return None

    def peek(self, priority: BundlePriority) -> Optional[Bundle]:
        """Peek at next bundle in specific priority queue"""
        if self.queues[priority]:
            return self.queues[priority][0]
        return None

    def size(self) -> int:
        """Get total number of bundles in all queues"""
        return sum(len(queue) for queue in self.queues.values())

    def is_empty(self) -> bool:
        """Check if all queues are empty"""
        return self.size() == 0


class RoutingUtilities:
    """Common utility methods for routing algorithms"""

    @staticmethod
    def calculate_transmission_time(bundle: Bundle, data_rate_mbps: float) -> float:
        """Calculate bundle transmission time in seconds"""
        bundle_size_bits = len(bundle.payload) * 8
        data_rate_bps = data_rate_mbps * 1_000_000
        return bundle_size_bits / data_rate_bps

    @staticmethod
    def can_transmit_bundle(bundle: Bundle, contact: ContactWindow) -> bool:
        """Check if bundle can be transmitted within contact window"""
        transmission_time = RoutingUtilities.calculate_transmission_time(
            bundle, contact.max_data_rate_mbps
        )
        return transmission_time <= contact.duration_seconds

    @staticmethod
    def optimize_transmission_schedule(
        bundles: List[Bundle], contact: ContactWindow
    ) -> List[Bundle]:
        """Optimize bundle transmission order within contact window"""

        # Sort by priority first, then by size (smaller first to fit more)
        def sort_key(bundle):
            priority_value = bundle.priority.value
            size_penalty = len(bundle.payload) / 1000  # normalize size
            return (-priority_value, size_penalty)

        sorted_bundles = sorted(bundles, key=sort_key)

        # Select bundles that fit within contact window
        scheduled_bundles = []
        total_time = 0.0

        for bundle in sorted_bundles:
            transmission_time = RoutingUtilities.calculate_transmission_time(
                bundle, contact.max_data_rate_mbps
            )
            if total_time + transmission_time <= contact.duration_seconds:
                scheduled_bundles.append(bundle)
                total_time += transmission_time
            else:
                break

        return scheduled_bundles

    @staticmethod
    def calculate_delivery_probability(
        source: str,
        destination: str,
        intermediate_node: str,
        contact_history: Dict[str, List[float]],
    ) -> float:
        """Calculate probability of successful delivery through intermediate node"""
        # Simplified delivery probability calculation
        # In practice, this would use more sophisticated prediction models

        # Check contact frequency with intermediate node
        if intermediate_node not in contact_history:
            return 0.1  # Low probability for unknown nodes

        recent_contacts = [
            t for t in contact_history[intermediate_node] if time.time() - t < 86400
        ]  # Last 24 hours

        contact_frequency = len(recent_contacts) / 24.0  # contacts per hour

        # Simple probability model based on contact frequency
        base_probability = min(contact_frequency / 10.0, 0.9)  # Max 90%

        return base_probability


class DTNRoutingManager:
    """Centralized DTN routing manager with algorithm selection and configuration"""

    def __init__(
        self,
        node_id: str,
        buffer_manager: BufferManager,
        contact_predictor: Optional[ContactPredictor] = None,
    ):
        self.node_id = node_id
        self.buffer_manager = buffer_manager
        self.contact_predictor = contact_predictor
        self.config = RoutingConfig()
        self.metrics = RoutingMetrics()
        self.priority_queue = PriorityQueue()
        self.logger = logging.getLogger(f"DTNRoutingManager-{node_id}")

        # Router registry
        self.routers: Dict[RoutingAlgorithm, Router] = {}
        self.active_algorithm = RoutingAlgorithm.EPIDEMIC

        # Contact and state tracking
        self.contact_history: Dict[str, List[float]] = defaultdict(list)
        self.routing_state: Dict[str, Any] = {}

        # Initialize routers (implementations will be added separately)
        self._initialize_routers()

    def _initialize_routers(self) -> None:
        """Initialize all routing algorithm implementations"""
        # Routers will be registered here when implementations are complete
        pass

    def register_router(self, algorithm: RoutingAlgorithm, router: Router) -> None:
        """Register a routing algorithm implementation"""
        self.routers[algorithm] = router
        self.logger.info(f"Registered router: {algorithm.value}")

    def route_bundle(
        self, bundle: Bundle, available_contacts: List[ContactWindow], timestamp: float
    ) -> Optional[str]:
        """
        Route a bundle using the active routing algorithm

        Args:
            bundle: Bundle to route
            available_contacts: Available contact windows
            timestamp: Current timestamp

        Returns:
            Node ID of next hop or None
        """
        try:
            # Validate bundle
            if not self.validate_bundle(bundle):
                return None

            # Get active router
            if self.active_algorithm not in self.routers:
                self.logger.error(
                    f"Router not found for algorithm: {self.active_algorithm}"
                )
                return None

            router = self.routers[self.active_algorithm]

            # Make routing decision
            next_hop = router.route_bundle(bundle, available_contacts, timestamp)

            # Update metrics
            self.metrics.routing_decisions += 1

            if next_hop:
                self.metrics.bundles_forwarded += 1
                self.logger.debug(f"Routed bundle {bundle.id} to {next_hop}")

            return next_hop

        except Exception as e:
            self.logger.error(f"Routing error for bundle {bundle.id}: {e}")
            return None

    def switch_routing_algorithm(self, algorithm: RoutingAlgorithm) -> bool:
        """
        Switch to a different routing algorithm

        Args:
            algorithm: Target routing algorithm

        Returns:
            True if switch successful
        """
        if algorithm not in self.routers:
            self.logger.error(f"Router not available: {algorithm}")
            return False

        if algorithm == self.active_algorithm:
            self.logger.info(f"Already using algorithm: {algorithm}")
            return True

        # Preserve routing state if possible
        old_algorithm = self.active_algorithm
        self.routing_state[old_algorithm.value] = getattr(
            self.routers[old_algorithm], "state", {}
        )

        # Switch algorithm
        self.active_algorithm = algorithm
        self.metrics.algorithm_switches += 1

        # Restore state if available
        if algorithm.value in self.routing_state:
            router = self.routers[algorithm]
            if hasattr(router, "restore_state"):
                state_data = self.routing_state[algorithm.value]
                router.restore_state(state_data)  # type: ignore[attr-defined]

        self.logger.info(
            f"Switched routing algorithm from {old_algorithm} to {algorithm}"
        )
        return True

    def validate_bundle(self, bundle: Bundle) -> bool:
        """Validate bundle for routing"""
        return bundle.validate() and not bundle.is_expired()

    def update_contact_history(self, node_id: str, timestamp: float) -> None:
        """Update contact history for routing algorithms"""
        self.contact_history[node_id].append(timestamp)

        # Keep only recent history (last 7 days)
        cutoff_time = timestamp - (7 * 24 * 3600)
        self.contact_history[node_id] = [
            t for t in self.contact_history[node_id] if t > cutoff_time
        ]

    def get_routing_metrics(self) -> RoutingMetrics:
        """Get current routing performance metrics"""
        return self.metrics

    def configure_algorithm(
        self, algorithm: RoutingAlgorithm, parameters: Dict[str, Any]
    ) -> bool:
        """
        Configure parameters for a specific routing algorithm

        Args:
            algorithm: Routing algorithm to configure
            parameters: Algorithm-specific parameters

        Returns:
            True if configuration successful
        """
        if algorithm not in self.routers:
            return False

        try:
            router = self.routers[algorithm]
            if hasattr(router, "configure"):
                router.configure(parameters)
            self.logger.info(
                f"Configured algorithm {algorithm} with parameters: {parameters}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Configuration error for {algorithm}: {e}")
            return False

    def get_algorithm_performance(
        self, algorithm: RoutingAlgorithm
    ) -> Dict[str, float]:
        """Get performance metrics for specific algorithm"""
        algo_name = algorithm.value
        return self.metrics.algorithm_performance.get(algo_name, {})

    def reset_metrics(self) -> None:
        """Reset routing metrics"""
        self.metrics = RoutingMetrics()
        self.logger.info("Routing metrics reset")


# Router factory for creating router instances
class RouterFactory:
    """Factory for creating router instances"""

    @staticmethod
    def create_router(
        algorithm: RoutingAlgorithm,
        node_id: str,
        buffer_manager: BufferManager,
        **kwargs,
    ) -> Router:
        """
        Create router instance for specified algorithm

        Args:
            algorithm: Routing algorithm type
            node_id: Node identifier
            buffer_manager: Buffer manager instance
            **kwargs: Algorithm-specific parameters

        Returns:
            Router instance
        """
        # Router implementations will be imported and created here
        # This is a placeholder for the factory pattern

        if algorithm == RoutingAlgorithm.EPIDEMIC:
            # from .epidemic_router import EpidemicRouter
            # return EpidemicRouter(node_id, buffer_manager, **kwargs)
            raise NotImplementedError("EpidemicRouter not yet implemented")

        elif algorithm == RoutingAlgorithm.PROPHET:
            # from .prophet_router import PROPHETRouter
            # return PROPHETRouter(node_id, buffer_manager, **kwargs)
            raise NotImplementedError("PROPHETRouter not yet implemented")

        elif algorithm == RoutingAlgorithm.SPRAY_AND_WAIT:
            # from .spray_wait_router import SprayAndWaitRouter
            # return SprayAndWaitRouter(node_id, buffer_manager, **kwargs)
            raise NotImplementedError("SprayAndWaitRouter not yet implemented")

        else:
            raise ValueError(f"Unknown routing algorithm: {algorithm}")
