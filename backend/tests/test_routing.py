"""
Unit tests for DTN Routing Infrastructure

Tests cover:
- Base Router interface and abstract methods
- DTNRoutingManager functionality
- Router factory pattern
- Bundle prioritization framework
- Common routing utilities
- Routing configuration system
"""

import unittest
import time
from typing import List, Optional

from src.routing import (
    DTNRoutingManager,
    Router,
    RouterFactory,
    RoutingAlgorithm,
    RoutingConfig,
    RoutingMetrics,
    PriorityQueue,
    RoutingUtilities,
    BufferManager,
)
from src.bundle import Bundle, BundlePriority
from src.contact_prediction import ContactWindow


class MockBufferManager:
    """Mock buffer manager for testing"""

    def __init__(self):
        self.bundles = {}
        self.capacity = 1000000  # 1MB
        self.used_space = 0

    def store_bundle(self, bundle: Bundle) -> bool:
        bundle_size = len(bundle.payload)
        if self.used_space + bundle_size <= self.capacity:
            self.bundles[bundle.id] = bundle
            self.used_space += bundle_size
            return True
        return False

    def retrieve_bundle(self, bundle_id: str) -> Optional[Bundle]:
        return self.bundles.get(bundle_id)

    def get_all_bundles(self) -> List[Bundle]:
        return list(self.bundles.values())

    def remove_bundle(self, bundle_id: str) -> bool:
        if bundle_id in self.bundles:
            bundle = self.bundles[bundle_id]
            self.used_space -= len(bundle.payload)
            del self.bundles[bundle_id]
            return True
        return False

    def get_buffer_utilization(self) -> float:
        return self.used_space / self.capacity

    def get_available_space(self) -> int:
        return self.capacity - self.used_space


class MockRouter(Router):
    """Mock router implementation for testing"""

    def __init__(self, node_id: str, buffer_manager: BufferManager):
        super().__init__(node_id, buffer_manager)
        self.route_calls = []
        self.update_calls = []
        self.configured_params = {}

    def route_bundle(
        self, bundle: Bundle, available_contacts: List[ContactWindow], timestamp: float
    ) -> Optional[str]:
        self.route_calls.append((bundle.id, len(available_contacts), timestamp))
        # Return first available contact if any
        if available_contacts:
            return available_contacts[0].ground_station
        return None

    def update_state(
        self,
        encountered_node: str,
        timestamp: float,
        contact_window: Optional[ContactWindow] = None,
    ) -> None:
        self.update_calls.append((encountered_node, timestamp))

    def configure(self, parameters):
        self.configured_params.update(parameters)


class TestPriorityQueue(unittest.TestCase):
    """Test priority-based bundle queue"""

    def setUp(self):
        self.queue = PriorityQueue()
        self.bundles = {
            "low": Bundle("sat1", "ground1", b"low priority", 3600, BundlePriority.LOW),
            "normal": Bundle(
                "sat1", "ground1", b"normal priority", 3600, BundlePriority.NORMAL
            ),
            "high": Bundle(
                "sat1", "ground1", b"high priority", 3600, BundlePriority.HIGH
            ),
            "critical": Bundle(
                "sat1", "ground1", b"critical priority", 3600, BundlePriority.CRITICAL
            ),
        }

    def test_enqueue_dequeue_priority_order(self):
        """Test bundles are dequeued in priority order"""
        # Enqueue in random order
        for bundle in [
            self.bundles["normal"],
            self.bundles["critical"],
            self.bundles["low"],
            self.bundles["high"],
        ]:
            self.queue.enqueue(bundle)

        # Dequeue should return in priority order
        self.assertEqual(self.queue.dequeue().priority, BundlePriority.CRITICAL)
        self.assertEqual(self.queue.dequeue().priority, BundlePriority.HIGH)
        self.assertEqual(self.queue.dequeue().priority, BundlePriority.NORMAL)
        self.assertEqual(self.queue.dequeue().priority, BundlePriority.LOW)

    def test_empty_queue(self):
        """Test empty queue behavior"""
        self.assertTrue(self.queue.is_empty())
        self.assertEqual(self.queue.size(), 0)
        self.assertIsNone(self.queue.dequeue())

    def test_peek_functionality(self):
        """Test peek without removing bundles"""
        self.queue.enqueue(self.bundles["normal"])
        self.queue.enqueue(self.bundles["high"])

        peeked = self.queue.peek(BundlePriority.HIGH)
        self.assertEqual(peeked.priority, BundlePriority.HIGH)
        self.assertEqual(self.queue.size(), 2)  # Should not remove bundle


class TestRoutingUtilities(unittest.TestCase):
    """Test common routing utility functions"""

    def setUp(self):
        self.bundle = Bundle("sat1", "ground1", b"test data" * 100, 3600)
        self.contact = ContactWindow(
            satellite_id="sat2",
            ground_station="ground1",
            start_time=time.time(),
            end_time=time.time() + 300,
            duration_seconds=300.0,
            max_elevation_deg=45.0,
            max_data_rate_mbps=10.0,
            average_range_km=500.0,
        )

    def test_transmission_time_calculation(self):
        """Test bundle transmission time calculation"""
        transmission_time = RoutingUtilities.calculate_transmission_time(
            self.bundle, 10.0  # 10 Mbps
        )

        expected_bits = len(self.bundle.payload) * 8
        expected_time = expected_bits / (10.0 * 1_000_000)
        self.assertAlmostEqual(transmission_time, expected_time, places=6)

    def test_can_transmit_bundle(self):
        """Test bundle transmission feasibility check"""
        # Small bundle should fit
        small_bundle = Bundle("sat1", "ground1", b"small", 3600)
        self.assertTrue(
            RoutingUtilities.can_transmit_bundle(small_bundle, self.contact)
        )

        # Very large bundle should not fit (100MB for 10Mbps link, 300 second window)
        # 100MB = 800Mbit, at 10Mbps = 80 seconds, but we have 300 seconds so it should fit
        # Let's use a bundle that definitely won't fit: 1GB
        large_bundle = Bundle("sat1", "ground1", b"x" * 1_000_000_000, 3600)  # 1GB
        self.assertFalse(
            RoutingUtilities.can_transmit_bundle(large_bundle, self.contact)
        )

    def test_transmission_schedule_optimization(self):
        """Test bundle transmission scheduling optimization"""
        bundles = [
            Bundle("sat1", "ground1", b"critical", 3600, BundlePriority.CRITICAL),
            Bundle("sat1", "ground1", b"low", 3600, BundlePriority.LOW),
            Bundle("sat1", "ground1", b"normal", 3600, BundlePriority.NORMAL),
            Bundle("sat1", "ground1", b"high", 3600, BundlePriority.HIGH),
        ]

        scheduled = RoutingUtilities.optimize_transmission_schedule(
            bundles, self.contact
        )

        # Should be ordered by priority
        priorities = [bundle.priority for bundle in scheduled]
        expected_order = [
            BundlePriority.CRITICAL,
            BundlePriority.HIGH,
            BundlePriority.NORMAL,
            BundlePriority.LOW,
        ]
        self.assertEqual(priorities, expected_order)

    def test_delivery_probability_calculation(self):
        """Test delivery probability calculation"""
        contact_history = {
            "sat2": [
                time.time() - 3600,
                time.time() - 1800,
                time.time() - 900,
            ]  # 3 contacts in last hour
        }

        prob = RoutingUtilities.calculate_delivery_probability(
            "sat1", "ground1", "sat2", contact_history
        )

        self.assertGreater(prob, 0.0)
        self.assertLessEqual(prob, 1.0)

        # Unknown node should have low probability
        prob_unknown = RoutingUtilities.calculate_delivery_probability(
            "sat1", "ground1", "unknown_sat", contact_history
        )
        self.assertEqual(prob_unknown, 0.1)


class TestDTNRoutingManager(unittest.TestCase):
    """Test DTN Routing Manager functionality"""

    def setUp(self):
        self.buffer_manager = MockBufferManager()
        self.manager = DTNRoutingManager("sat1", self.buffer_manager)
        self.mock_router = MockRouter("sat1", self.buffer_manager)
        self.manager.register_router(RoutingAlgorithm.EPIDEMIC, self.mock_router)

        self.test_bundle = Bundle("sat1", "ground1", b"test data", 3600)
        self.test_contacts = [
            ContactWindow(
                satellite_id="sat2",
                ground_station="ground1",
                start_time=time.time(),
                end_time=time.time() + 300,
                duration_seconds=300.0,
                max_elevation_deg=45.0,
                max_data_rate_mbps=10.0,
                average_range_km=500.0,
            )
        ]

    def test_routing_manager_initialization(self):
        """Test routing manager initializes correctly"""
        self.assertEqual(self.manager.node_id, "sat1")
        self.assertEqual(self.manager.active_algorithm, RoutingAlgorithm.EPIDEMIC)
        self.assertIsInstance(self.manager.metrics, RoutingMetrics)
        self.assertIsInstance(self.manager.priority_queue, PriorityQueue)

    def test_router_registration(self):
        """Test router registration"""
        test_router = MockRouter("test", self.buffer_manager)
        self.manager.register_router(RoutingAlgorithm.PROPHET, test_router)

        self.assertIn(RoutingAlgorithm.PROPHET, self.manager.routers)
        self.assertEqual(self.manager.routers[RoutingAlgorithm.PROPHET], test_router)

    def test_route_bundle_success(self):
        """Test successful bundle routing"""
        result = self.manager.route_bundle(
            self.test_bundle, self.test_contacts, time.time()
        )

        self.assertEqual(result, "ground1")
        self.assertEqual(self.manager.metrics.routing_decisions, 1)
        self.assertEqual(self.manager.metrics.bundles_forwarded, 1)
        self.assertEqual(len(self.mock_router.route_calls), 1)

    def test_route_bundle_invalid_bundle(self):
        """Test routing with invalid bundle"""
        invalid_bundle = Bundle("", "", b"", -1)  # Invalid bundle
        result = self.manager.route_bundle(
            invalid_bundle, self.test_contacts, time.time()
        )

        self.assertIsNone(result)
        self.assertEqual(len(self.mock_router.route_calls), 0)

    def test_route_bundle_no_router(self):
        """Test routing when no router available"""
        manager = DTNRoutingManager("sat2", self.buffer_manager)
        result = manager.route_bundle(self.test_bundle, self.test_contacts, time.time())

        self.assertIsNone(result)

    def test_algorithm_switching(self):
        """Test dynamic algorithm switching"""
        prophet_router = MockRouter("sat1", self.buffer_manager)
        self.manager.register_router(RoutingAlgorithm.PROPHET, prophet_router)

        # Switch to PRoPHET
        success = self.manager.switch_routing_algorithm(RoutingAlgorithm.PROPHET)
        self.assertTrue(success)
        self.assertEqual(self.manager.active_algorithm, RoutingAlgorithm.PROPHET)
        self.assertEqual(self.manager.metrics.algorithm_switches, 1)

        # Route bundle with new algorithm
        self.manager.route_bundle(self.test_bundle, self.test_contacts, time.time())
        self.assertEqual(len(prophet_router.route_calls), 1)
        self.assertEqual(len(self.mock_router.route_calls), 0)

    def test_algorithm_switching_invalid(self):
        """Test switching to invalid algorithm"""
        success = self.manager.switch_routing_algorithm(RoutingAlgorithm.SPRAY_AND_WAIT)
        self.assertFalse(success)
        self.assertEqual(self.manager.active_algorithm, RoutingAlgorithm.EPIDEMIC)

    def test_algorithm_switching_same(self):
        """Test switching to same algorithm"""
        success = self.manager.switch_routing_algorithm(RoutingAlgorithm.EPIDEMIC)
        self.assertTrue(success)
        self.assertEqual(self.manager.metrics.algorithm_switches, 0)

    def test_bundle_validation(self):
        """Test bundle validation"""
        valid_bundle = Bundle("sat1", "ground1", b"test", 3600)
        self.assertTrue(self.manager.validate_bundle(valid_bundle))

        # Test expired bundle
        expired_bundle = Bundle("sat1", "ground1", b"test", 1)
        time.sleep(1.1)  # Wait for expiry
        self.assertFalse(self.manager.validate_bundle(expired_bundle))

    def test_contact_history_update(self):
        """Test contact history tracking"""
        timestamp = time.time()
        self.manager.update_contact_history("sat2", timestamp)

        self.assertIn("sat2", self.manager.contact_history)
        self.assertIn(timestamp, self.manager.contact_history["sat2"])

    def test_algorithm_configuration(self):
        """Test algorithm configuration"""
        params = {"test_param": 42}
        success = self.manager.configure_algorithm(RoutingAlgorithm.EPIDEMIC, params)

        self.assertTrue(success)
        self.assertEqual(self.mock_router.configured_params["test_param"], 42)

    def test_metrics_retrieval(self):
        """Test routing metrics retrieval"""
        # Generate some activity
        self.manager.route_bundle(self.test_bundle, self.test_contacts, time.time())

        metrics = self.manager.get_routing_metrics()
        self.assertGreater(metrics.routing_decisions, 0)
        self.assertGreater(metrics.bundles_forwarded, 0)

    def test_metrics_reset(self):
        """Test metrics reset functionality"""
        # Generate activity
        self.manager.route_bundle(self.test_bundle, self.test_contacts, time.time())

        # Reset metrics
        self.manager.reset_metrics()

        metrics = self.manager.get_routing_metrics()
        self.assertEqual(metrics.routing_decisions, 0)
        self.assertEqual(metrics.bundles_forwarded, 0)


class TestRouterFactory(unittest.TestCase):
    """Test router factory pattern"""

    def setUp(self):
        self.buffer_manager = MockBufferManager()

    def test_router_factory_not_implemented(self):
        """Test router factory raises NotImplementedError for unimplemented algorithms"""
        with self.assertRaises(NotImplementedError):
            RouterFactory.create_router(
                RoutingAlgorithm.EPIDEMIC, "sat1", self.buffer_manager
            )

        with self.assertRaises(NotImplementedError):
            RouterFactory.create_router(
                RoutingAlgorithm.PROPHET, "sat1", self.buffer_manager
            )

        with self.assertRaises(NotImplementedError):
            RouterFactory.create_router(
                RoutingAlgorithm.SPRAY_AND_WAIT, "sat1", self.buffer_manager
            )

    def test_router_factory_invalid_algorithm(self):
        """Test router factory with invalid algorithm"""
        with self.assertRaises(ValueError):
            RouterFactory.create_router(
                "invalid_algorithm", "sat1", self.buffer_manager
            )


class TestRoutingConfig(unittest.TestCase):
    """Test routing configuration system"""

    def test_default_config(self):
        """Test default routing configuration"""
        config = RoutingConfig()

        self.assertEqual(config.algorithm, RoutingAlgorithm.EPIDEMIC)
        self.assertTrue(config.epidemic_anti_entropy)
        self.assertEqual(config.epidemic_max_flood_rate, 10.0)
        self.assertEqual(config.prophet_p_encounter_max, 0.75)
        self.assertEqual(config.spray_initial_copies, 10)
        self.assertTrue(config.priority_queue_enabled)

    def test_custom_config(self):
        """Test custom routing configuration"""
        config = RoutingConfig(
            algorithm=RoutingAlgorithm.PROPHET,
            prophet_beta=0.5,
            spray_initial_copies=5,
            max_bundle_ttl_hours=48.0,
        )

        self.assertEqual(config.algorithm, RoutingAlgorithm.PROPHET)
        self.assertEqual(config.prophet_beta, 0.5)
        self.assertEqual(config.spray_initial_copies, 5)
        self.assertEqual(config.max_bundle_ttl_hours, 48.0)


class TestRoutingMetrics(unittest.TestCase):
    """Test routing metrics collection"""

    def test_metrics_initialization(self):
        """Test metrics initialize with zero values"""
        metrics = RoutingMetrics()

        self.assertEqual(metrics.bundles_forwarded, 0)
        self.assertEqual(metrics.routing_decisions, 0)
        self.assertEqual(metrics.successful_deliveries, 0)
        self.assertEqual(metrics.failed_deliveries, 0)
        self.assertEqual(metrics.total_delay_seconds, 0.0)
        self.assertEqual(metrics.algorithm_switches, 0)

    def test_metrics_defaultdict_behavior(self):
        """Test metrics defaultdict behavior"""
        metrics = RoutingMetrics()

        # Should create empty dict for new algorithms
        self.assertIsInstance(metrics.algorithm_performance["new_algo"], dict)
        self.assertEqual(len(metrics.delivery_ratios), 0)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complete routing scenarios"""

    def setUp(self):
        self.buffer_manager = MockBufferManager()
        self.manager = DTNRoutingManager("sat1", self.buffer_manager)

        # Register mock routers
        self.epidemic_router = MockRouter("sat1", self.buffer_manager)
        self.prophet_router = MockRouter("sat1", self.buffer_manager)

        self.manager.register_router(RoutingAlgorithm.EPIDEMIC, self.epidemic_router)
        self.manager.register_router(RoutingAlgorithm.PROPHET, self.prophet_router)

        # Test bundles with different priorities
        self.bundles = [
            Bundle("sat1", "ground1", b"critical", 3600, BundlePriority.CRITICAL),
            Bundle("sat1", "ground1", b"normal", 3600, BundlePriority.NORMAL),
            Bundle("sat1", "ground1", b"low", 3600, BundlePriority.LOW),
        ]

        self.contacts = [
            ContactWindow(
                "sat2",
                "ground1",
                time.time(),
                time.time() + 300,
                300.0,
                45.0,
                10.0,
                500.0,
            ),
            ContactWindow(
                "sat3",
                "ground2",
                time.time(),
                time.time() + 600,
                600.0,
                60.0,
                20.0,
                400.0,
            ),
        ]

    def test_full_routing_workflow(self):
        """Test complete routing workflow with algorithm switching"""
        timestamp = time.time()

        # Route bundles with epidemic algorithm
        for bundle in self.bundles:
            result = self.manager.route_bundle(bundle, self.contacts, timestamp)
            self.assertIsNotNone(result)

        # Verify epidemic router was used
        self.assertEqual(len(self.epidemic_router.route_calls), 3)
        self.assertEqual(len(self.prophet_router.route_calls), 0)

        # Switch to PRoPHET algorithm
        self.manager.switch_routing_algorithm(RoutingAlgorithm.PROPHET)

        # Route more bundles
        new_bundle = Bundle("sat1", "ground1", b"prophet test", 3600)
        result = self.manager.route_bundle(new_bundle, self.contacts, timestamp)
        self.assertIsNotNone(result)

        # Verify PRoPHET router was used
        self.assertEqual(len(self.epidemic_router.route_calls), 3)
        self.assertEqual(len(self.prophet_router.route_calls), 1)

        # Check metrics
        metrics = self.manager.get_routing_metrics()
        self.assertEqual(metrics.routing_decisions, 4)
        self.assertEqual(metrics.bundles_forwarded, 4)
        self.assertEqual(metrics.algorithm_switches, 1)

    def test_priority_based_routing(self):
        """Test priority-based bundle handling"""
        # Test that validation works for different priorities
        for bundle in self.bundles:
            self.assertTrue(self.manager.validate_bundle(bundle))

        # Test priority queue behavior
        queue = PriorityQueue()
        for bundle in self.bundles:
            queue.enqueue(bundle)

        # Should dequeue in priority order
        first = queue.dequeue()
        self.assertEqual(first.priority, BundlePriority.CRITICAL)

    def test_contact_history_and_state_management(self):
        """Test contact history tracking and state management"""
        timestamp = time.time()

        # Update contact history
        self.manager.update_contact_history("sat2", timestamp)
        self.manager.update_contact_history("sat3", timestamp - 3600)

        # Verify history is tracked
        self.assertIn("sat2", self.manager.contact_history)
        self.assertIn("sat3", self.manager.contact_history)

        # Test old entries are cleaned up
        old_timestamp = timestamp - (8 * 24 * 3600)  # 8 days ago
        self.manager.update_contact_history("sat4", old_timestamp)
        self.manager.update_contact_history(
            "sat4", timestamp
        )  # This should trigger cleanup

        # Should only have recent entry
        self.assertEqual(len(self.manager.contact_history["sat4"]), 1)
        self.assertEqual(self.manager.contact_history["sat4"][0], timestamp)


if __name__ == "__main__":
    # Configure logging for tests
    import logging

    logging.basicConfig(level=logging.INFO)

    # Run all tests
    unittest.main(verbosity=2)
