#!/usr/bin/env python3
"""
DTN Routing System Demo

This example demonstrates the DTN Routing Manager and Factory Pattern
implementation for satellite delay-tolerant networks.
"""

import time
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import routing
from bundle import Bundle, BundlePriority
from contact_prediction import ContactWindow

# Import from routing module
DTNRoutingManager = routing.DTNRoutingManager
RoutingAlgorithm = routing.RoutingAlgorithm
RoutingConfig = routing.RoutingConfig
PriorityQueue = routing.PriorityQueue
RouterFactory = routing.RouterFactory


class MockBufferManager:
    """Simple buffer manager for demo purposes"""
    
    def __init__(self, capacity_bytes=1000000):
        self.bundles = {}
        self.capacity = capacity_bytes
        self.used_space = 0
        
    def store_bundle(self, bundle):
        bundle_size = len(bundle.payload)
        if self.used_space + bundle_size <= self.capacity:
            self.bundles[bundle.id] = bundle
            self.used_space += bundle_size
            return True
        return False
        
    def retrieve_bundle(self, bundle_id):
        return self.bundles.get(bundle_id)
        
    def get_all_bundles(self):
        return list(self.bundles.values())
        
    def remove_bundle(self, bundle_id):
        if bundle_id in self.bundles:
            bundle = self.bundles[bundle_id]
            self.used_space -= len(bundle.payload)
            del self.bundles[bundle_id]
            return True
        return False
        
    def get_buffer_utilization(self):
        return self.used_space / self.capacity
        
    def get_available_space(self):
        return self.capacity - self.used_space


def demo_priority_queue():
    """Demonstrate bundle prioritization"""
    print("=== Bundle Priority Queue Demo ===")
    
    queue = PriorityQueue()
    
    # Create bundles with different priorities
    bundles = [
        Bundle("sat1", "ground1", b"Low priority message", 3600, BundlePriority.LOW),
        Bundle("sat1", "ground1", b"Critical emergency message", 3600, BundlePriority.CRITICAL),
        Bundle("sat1", "ground1", b"Normal message", 3600, BundlePriority.NORMAL),
        Bundle("sat1", "ground1", b"High priority message", 3600, BundlePriority.HIGH),
    ]
    
    # Enqueue bundles in random order
    print("Enqueueing bundles:")
    for bundle in bundles:
        queue.enqueue(bundle)
        print(f"  - {bundle.priority.name}: {bundle.payload.decode()}")
    
    print(f"\nTotal bundles in queue: {queue.size()}")
    
    # Dequeue bundles (should come out in priority order)
    print("\nDequeue order (priority-based):")
    while not queue.is_empty():
        bundle = queue.dequeue()
        print(f"  - {bundle.priority.name}: {bundle.payload.decode()}")
    
    print()


def demo_routing_manager():
    """Demonstrate DTN Routing Manager functionality"""
    print("=== DTN Routing Manager Demo ===")
    
    # Initialize buffer manager and routing manager
    buffer_manager = MockBufferManager()
    routing_manager = DTNRoutingManager("satellite_1", buffer_manager)
    
    print(f"Routing Manager initialized for node: {routing_manager.node_id}")
    print(f"Active algorithm: {routing_manager.active_algorithm.value}")
    
    # Create sample contact windows
    current_time = time.time()
    contacts = [
        ContactWindow(
            satellite_id="satellite_2",
            ground_station="ground_station_1",
            start_time=current_time,
            end_time=current_time + 300,
            duration_seconds=300.0,
            max_elevation_deg=45.0,
            max_data_rate_mbps=10.0,
            average_range_km=500.0
        ),
        ContactWindow(
            satellite_id="satellite_3", 
            ground_station="ground_station_2",
            start_time=current_time,
            end_time=current_time + 600,
            duration_seconds=600.0,
            max_elevation_deg=60.0,
            max_data_rate_mbps=20.0,
            average_range_km=400.0
        )
    ]
    
    print(f"\nAvailable contacts: {len(contacts)}")
    for i, contact in enumerate(contacts):
        print(f"  Contact {i+1}: {contact.satellite_id} -> {contact.ground_station}")
        print(f"    Duration: {contact.duration_seconds}s, Rate: {contact.max_data_rate_mbps}Mbps")
    
    # Create test bundles
    bundles = [
        Bundle("satellite_1", "ground_station_1", b"Emergency telemetry data", 
               3600, BundlePriority.CRITICAL),
        Bundle("satellite_1", "ground_station_2", b"Science experiment results",
               7200, BundlePriority.HIGH),
        Bundle("satellite_1", "ground_station_1", b"Routine status update",
               1800, BundlePriority.NORMAL)
    ]
    
    print(f"\nTest bundles: {len(bundles)}")
    for bundle in bundles:
        print(f"  - {bundle.priority.name}: {bundle.destination} -> {bundle.payload.decode()}")
    
    # Note: Since we haven't implemented actual routing algorithms yet,
    # we can't demonstrate actual routing. But we can show the manager structure.
    print(f"\nRouting manager is ready to route bundles once algorithms are implemented.")
    print(f"Available routing algorithms: {[alg.value for alg in RoutingAlgorithm]}")
    
    # Show current metrics
    metrics = routing_manager.get_routing_metrics()
    print(f"\nCurrent metrics:")
    print(f"  - Routing decisions: {metrics.routing_decisions}")
    print(f"  - Bundles forwarded: {metrics.bundles_forwarded}")
    print(f"  - Algorithm switches: {metrics.algorithm_switches}")
    
    print()


def demo_routing_config():
    """Demonstrate routing configuration system"""
    print("=== Routing Configuration Demo ===")
    
    # Default configuration
    default_config = RoutingConfig()
    print("Default configuration:")
    print(f"  - Algorithm: {default_config.algorithm.value}")
    print(f"  - Priority queue enabled: {default_config.priority_queue_enabled}")
    print(f"  - Max bundle TTL: {default_config.max_bundle_ttl_hours} hours")
    print(f"  - Contact lookahead: {default_config.contact_lookahead_hours} hours")
    
    # PRoPHET configuration
    prophet_config = RoutingConfig(
        algorithm=RoutingAlgorithm.PROPHET,
        prophet_p_encounter_max=0.8,
        prophet_beta=0.3,
        prophet_gamma=0.95,
        contact_lookahead_hours=48.0
    )
    
    print("\nPRoPHET configuration:")
    print(f"  - Algorithm: {prophet_config.algorithm.value}")
    print(f"  - P_encounter_max: {prophet_config.prophet_p_encounter_max}")
    print(f"  - Beta: {prophet_config.prophet_beta}")
    print(f"  - Gamma: {prophet_config.prophet_gamma}")
    print(f"  - Contact lookahead: {prophet_config.contact_lookahead_hours} hours")
    
    # Spray-and-Wait configuration
    spray_config = RoutingConfig(
        algorithm=RoutingAlgorithm.SPRAY_AND_WAIT,
        spray_initial_copies=15,
        spray_threshold=2,
        max_bundle_ttl_hours=72.0
    )
    
    print("\nSpray-and-Wait configuration:")
    print(f"  - Algorithm: {spray_config.algorithm.value}")
    print(f"  - Initial copies: {spray_config.spray_initial_copies}")
    print(f"  - Spray threshold: {spray_config.spray_threshold}")
    print(f"  - Max bundle TTL: {spray_config.max_bundle_ttl_hours} hours")
    
    print()


def demo_router_factory():
    """Demonstrate router factory pattern"""
    print("=== Router Factory Demo ===")
    
    buffer_manager = MockBufferManager()
    
    print("Available routing algorithms:")
    for algorithm in RoutingAlgorithm:
        print(f"  - {algorithm.value}")
    
    print("\nTrying to create routers (will show NotImplementedError since algorithms aren't implemented yet):")
    
    for algorithm in RoutingAlgorithm:
        try:
            router = RouterFactory.create_router(algorithm, "test_node", buffer_manager)
            print(f"  ✓ {algorithm.value}: Created successfully")
        except NotImplementedError as e:
            print(f"  ⚠ {algorithm.value}: {e}")
        except Exception as e:
            print(f"  ✗ {algorithm.value}: Error - {e}")
    
    print("\nRouter factory is ready for algorithm implementations.")
    print()


def main():
    """Run all demos"""
    print("DTN Routing System Demonstration")
    print("=" * 50)
    print()
    
    try:
        demo_priority_queue()
        demo_routing_manager()
        demo_routing_config()
        demo_router_factory()
        
        print("=== Demo Complete ===")
        print("The DTN Routing Infrastructure is ready for:")
        print("  1. Epidemic routing algorithm implementation")
        print("  2. PRoPHET routing algorithm implementation") 
        print("  3. Spray-and-Wait routing algorithm implementation")
        print("  4. Integration with contact prediction and buffer management")
        print("  5. Real-world satellite network testing")
        
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()