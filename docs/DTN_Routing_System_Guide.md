# DTN Routing System: Engineering Guide

## Table of Contents
1. [What is DTN Routing?](#what-is-dtn-routing)
2. [System Architecture](#system-architecture)
3. [Routing Algorithms Overview](#routing-algorithms-overview)
4. [Bundle Prioritization](#bundle-prioritization)
5. [Contact-Aware Routing](#contact-aware-routing)
6. [Factory Pattern Implementation](#factory-pattern-implementation)
7. [Performance Metrics](#performance-metrics)
8. [Integration Points](#integration-points)
9. [Usage Examples](#usage-examples)

---

## What is DTN Routing?

**Delay-Tolerant Networking (DTN)** is designed for environments where traditional internet protocols fail due to intermittent connectivity, long delays, and high error rates. Our satellite constellation represents a perfect DTN scenario.

### The Challenge: Space Communication
```
Traditional Internet:
[Device] ←→ [Router] ←→ [Router] ←→ [Destination]
         Continuous connection required

DTN in Space:
[Satellite A] ←...→ [Satellite B] ←...→ [Ground Station]
              Intermittent contacts with store-and-forward
```

### Key DTN Principles

1. **Store-and-Forward**: Messages are stored at intermediate nodes when no path exists
2. **Opportunistic Routing**: Forward messages when contacts become available
3. **Bundle-Based**: Data is packaged into self-contained "bundles" with metadata
4. **Contact-Aware**: Routing decisions based on predicted contact windows

---

## System Architecture

Our DTN Routing System implements a modular, algorithm-agnostic architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                    │
├─────────────────────────────────────────────────────────┤
│               DTN Routing Manager                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │   Epidemic  │ │   PRoPHET   │ │ Spray-and-Wait  │   │
│  │   Router    │ │   Router    │ │     Router      │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
│              │                │                │       │
│              └────────────────┼────────────────┘       │
│                               │                        │
│  ┌─────────────────────────────┼─────────────────────┐  │
│  │           Router Factory     │                   │  │
│  └─────────────────────────────┼─────────────────────┘  │
├─────────────────────────────────┼─────────────────────────┤
│           Core Infrastructure   │                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │   Bundle    │ │ Priority    │ │    Routing      │   │
│  │   Manager   │ │   Queue     │ │   Utilities     │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │   Buffer    │ │  Contact    │ │   Satellite     │   │
│  │  Manager    │ │ Predictor   │ │   Mobility      │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. DTN Routing Manager
The central orchestrator that:
- Manages multiple routing algorithms
- Handles algorithm switching
- Coordinates with buffer and contact prediction systems
- Tracks performance metrics

#### 2. Router Factory
Implements the Factory Pattern for:
- Dynamic router instantiation
- Algorithm-specific configuration
- Pluggable architecture for new algorithms

#### 3. Priority Queue System
Handles bundle prioritization:
```
Priority Levels:
CRITICAL (4) ──┐
HIGH (3) ──────┤
NORMAL (2) ────┤── Transmission Order
LOW (1) ───────┘
```

---

## Routing Algorithms Overview

### 1. Epidemic Routing
**Strategy**: Flood bundles to all encountered nodes

```
Time T1: Satellite A has Bundle X
[Sat A: Bundle X] ──contact──> [Sat B: Bundle X]
                              
Time T2: Both satellites spread Bundle X
[Sat A: Bundle X] ──contact──> [Sat C: Bundle X]
[Sat B: Bundle X] ──contact──> [Sat D: Bundle X]

Result: Bundle X spreads like an epidemic
```

**Advantages:**
- High delivery probability
- Simple implementation
- Works well in sparse networks

**Disadvantages:**
- High network overhead
- Resource intensive
- Potential for network flooding

**Use Cases:**
- Emergency communications
- High-priority, low-volume traffic
- Networks with abundant storage/bandwidth

### 2. PRoPHET (Probabilistic Routing Protocol using History of Encounters and Transitivity)
**Strategy**: Route based on delivery predictability

```
Delivery Predictability Calculation:
P(A,B) = Probability that node A can deliver to node B

On Contact: P(A,B) = P(A,B)_old + (1 - P(A,B)_old) × P_encounter_max
Aging: P(A,B) = P(A,B)_old × γ^k
Transitivity: P(A,C) = P(A,C)_old + (1 - P(A,C)_old) × P(A,B) × P(B,C) × β
```

**Visual Example:**
```
Historical Contacts:
Sat A ←→ Sat B (frequent) → P(A,B) = 0.8
Sat B ←→ Ground (frequent) → P(B,Ground) = 0.9
Sat A ←→ Ground (rare) → P(A,Ground) = 0.1

Routing Decision:
Bundle for Ground at Sat A:
- Direct: P(A,Ground) = 0.1
- Via Sat B: P(A,B) × P(B,Ground) = 0.8 × 0.9 = 0.72
→ Forward to Sat B
```

**Advantages:**
- Efficient resource usage
- Adapts to network patterns
- Good delivery ratio with lower overhead

**Disadvantages:**
- Complex probability calculations
- Requires contact history
- May miss rare opportunities

**Use Cases:**
- Regular communication patterns
- Resource-constrained environments
- Predictable satellite orbits

### 3. Spray-and-Wait Routing
**Strategy**: Limited replication followed by direct delivery

```
Phase 1 - Spray (L = 10 copies):
[Source] → creates 10 copies of Bundle X

[Node 1: 5 copies] ──contact──> [Node 2: 2 copies]
                              [Node 3: 3 copies]

Phase 2 - Wait:
Each node with copies waits for direct contact with destination
[Node 1: 5 copies] ──contact──> [Destination] ✓
```

**Copy Distribution Strategies:**
- **Binary Spray**: Divide copies by 2
- **Random Spray**: Random distribution
- **Utility-based Spray**: Based on node utility

**Advantages:**
- Controlled overhead
- Bounded resource usage
- Good delivery ratio

**Disadvantages:**
- Complex copy management
- May waste opportunities in wait phase
- Requires careful parameter tuning

**Use Cases:**
- Mixed traffic scenarios
- Limited storage networks
- Time-sensitive communications

---

## Bundle Prioritization

Our system implements a sophisticated 4-level priority system:

```
┌─────────────────────────────────────────────────────┐
│                 Priority Queue                      │
├─────────────────────────────────────────────────────┤
│ CRITICAL │ Emergency alerts, critical telemetry    │
│    (4)   │ ── Always transmitted first            │
├─────────────────────────────────────────────────────┤
│   HIGH   │ Important science data, commands        │
│    (3)   │ ── High priority transmission          │
├─────────────────────────────────────────────────────┤
│  NORMAL  │ Regular data, status updates           │
│    (2)   │ ── Standard transmission priority      │
├─────────────────────────────────────────────────────┤
│   LOW    │ Bulk data, non-critical updates        │
│    (1)   │ ── Transmitted when bandwidth available │
└─────────────────────────────────────────────────────┘
```

### Priority-Based Routing Logic

1. **Queue Management**: Bundles are sorted by priority in transmission queues
2. **Contact Utilization**: Higher priority bundles get first access to contact windows
3. **Resource Allocation**: Critical bundles can preempt lower priority transmissions
4. **TTL Consideration**: Priority is balanced with time-to-live for optimal delivery

### Transmission Scheduling

```python
def optimize_transmission_schedule(bundles, contact_window):
    """
    Optimize bundle transmission within contact window
    
    Factors considered:
    1. Bundle priority (highest first)
    2. Bundle size (smaller first to fit more)
    3. Remaining TTL (urgent first)
    4. Contact duration and data rate
    """
    
    # Sort by priority, then size
    sorted_bundles = sort_by_priority_and_size(bundles)
    
    # Select bundles that fit in contact window
    scheduled = []
    total_time = 0
    
    for bundle in sorted_bundles:
        tx_time = calculate_transmission_time(bundle, contact.data_rate)
        if total_time + tx_time <= contact.duration:
            scheduled.append(bundle)
            total_time += tx_time
    
    return scheduled
```

---

## Contact-Aware Routing

DTN routing leverages predicted contact windows for intelligent forwarding decisions:

### Contact Window Structure
```python
ContactWindow:
  - satellite_id: "SAT_001"
  - ground_station: "ALASKA_GS"
  - start_time: 1640995200  # Unix timestamp
  - end_time: 1640995500    # Unix timestamp  
  - duration_seconds: 300.0
  - max_elevation_deg: 45.0
  - max_data_rate_mbps: 10.0
  - average_range_km: 500.0
```

### Contact Evaluation Process

```
1. Contact Discovery
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │  Satellite  │───▶│  Contact    │───▶│ Available   │
   │  Position   │    │ Predictor   │    │ Contacts    │
   └─────────────┘    └─────────────┘    └─────────────┘

2. Contact Evaluation
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ Available   │───▶│  Routing    │───▶│   Next      │
   │ Contacts    │    │ Algorithm   │    │   Hop       │
   └─────────────┘    └─────────────┘    └─────────────┘

3. Utility Calculation
   Factors:
   - Contact duration × data rate = transmission capacity
   - Bundle priority boost
   - Remaining TTL penalty
   - Delivery probability to destination
```

### Utility-Based Contact Selection

```python
def calculate_contact_utility(contact, bundle):
    """
    Calculate utility of contact for bundle transmission
    
    Utility = base_capacity × priority_boost × ttl_factor × delivery_prob
    """
    
    # Base transmission capacity
    base_utility = contact.duration_seconds * contact.max_data_rate_mbps
    
    # Priority multiplier
    priority_boost = {
        CRITICAL: 5.0,
        HIGH: 2.0, 
        NORMAL: 1.0,
        LOW: 0.5
    }[bundle.priority]
    
    # TTL urgency factor
    ttl_factor = bundle.remaining_ttl() / bundle.ttl_seconds
    
    # Delivery probability (algorithm-specific)
    delivery_prob = calculate_delivery_probability(contact, bundle.destination)
    
    return base_utility * priority_boost * ttl_factor * delivery_prob
```

---

## Factory Pattern Implementation

The Router Factory enables pluggable routing algorithms:

### Factory Architecture
```
                    RouterFactory
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌─────────┐    ┌─────────────┐   ┌──────────────┐
   │Epidemic │    │   PRoPHET   │   │Spray-and-Wait│
   │ Router  │    │   Router    │   │   Router     │
   └─────────┘    └─────────────┘   └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                 Router (Abstract Base)
```

### Dynamic Algorithm Switching

```python
class DTNRoutingManager:
    def switch_routing_algorithm(self, new_algorithm):
        """
        Switch routing algorithm without losing state
        
        Process:
        1. Save current algorithm state
        2. Switch to new algorithm
        3. Restore compatible state
        4. Update metrics
        """
        
        # Preserve routing state
        old_algorithm = self.active_algorithm
        self.routing_state[old_algorithm] = self.get_current_state()
        
        # Switch algorithm
        self.active_algorithm = new_algorithm
        
        # Restore state if available
        if new_algorithm in self.routing_state:
            self.restore_state(self.routing_state[new_algorithm])
        
        # Update metrics
        self.metrics.algorithm_switches += 1
```

### Configuration Management

Each algorithm supports specific configuration:

```python
# Epidemic Configuration
EpidemicConfig:
  - anti_entropy: True
  - max_flood_rate: 10.0 bundles/sec
  - summary_vector_exchange: True

# PRoPHET Configuration  
PROPHETConfig:
  - p_encounter_max: 0.75
  - beta: 0.25  # transitivity scaling
  - gamma: 0.98 # aging factor
  - delta: 0.01 # minimum threshold

# Spray-and-Wait Configuration
SprayWaitConfig:
  - initial_copies: 10
  - spray_threshold: 1
  - copy_strategy: "binary" | "random" | "utility"
```

---

## Performance Metrics

The system tracks comprehensive metrics for performance analysis:

### Real-Time Metrics Dashboard
```
┌─────────────────────────────────────────────────────┐
│                Routing Metrics                      │
├─────────────────────────────────────────────────────┤
│ Active Algorithm: PRoPHET                           │
│ Routing Decisions: 1,247 (avg 23ms)               │
│ Bundles Forwarded: 856                             │
│ Success Rate: 68.6%                                │
├─────────────────────────────────────────────────────┤
│              Algorithm Performance                  │
│ ┌─────────┬─────────┬─────────┬─────────────────┐   │
│ │Algorithm│Delivery │Avg Delay│Overhead Ratio   │   │
│ │         │ Rate    │   (s)   │                 │   │
│ ├─────────┼─────────┼─────────┼─────────────────┤   │
│ │Epidemic │  95.2%  │   245   │      3.4x       │   │
│ │PRoPHET  │  84.1%  │   312   │      1.8x       │   │
│ │Spray&Wait│  76.8%  │   198   │      2.1x       │   │
│ └─────────┴─────────┴─────────┴─────────────────┘   │
├─────────────────────────────────────────────────────┤
│              Resource Utilization                   │
│ Buffer Usage: ████████░░ 78%                       │
│ Contact Efficiency: ██████████ 92%                 │
│ Network Overhead: ███░░░░░░░ 34%                   │
└─────────────────────────────────────────────────────┘
```

### Metrics Collection
```python
class RoutingMetrics:
    def record_routing_decision(self, algorithm, bundle, decision_time):
        """Record routing decision for performance analysis"""
        
        self.routing_decisions += 1
        self.algorithm_performance[algorithm]['decisions'] += 1
        self.algorithm_performance[algorithm]['avg_time'] = update_average(
            self.algorithm_performance[algorithm]['avg_time'],
            decision_time
        )
        
    def calculate_delivery_ratio(self, algorithm, time_window=24*3600):
        """Calculate delivery success ratio for algorithm"""
        
        recent_deliveries = self.get_recent_deliveries(algorithm, time_window)
        recent_attempts = self.get_recent_attempts(algorithm, time_window)
        
        return recent_deliveries / recent_attempts if recent_attempts > 0 else 0.0
```

---

## Integration Points

### Partner Integration Architecture
```
┌─────────────────────────────────────────────────────┐
│                  Partner A                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │  Orbital    │ │  Contact    │ │  Satellite  │   │
│  │ Mechanics   │ │ Prediction  │ │  Mobility   │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
│         │               │               │          │
│         └───────────────┼───────────────┘          │
├─────────────────────────┼─────────────────────────────┤
│                  Partner B (This Implementation)   │
│  ┌─────────────────────┼─────────────────────────┐   │
│  │        DTN Routing Manager                   │   │
│  │                     │                       │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────┐│   │
│  │  │   Buffer    │ │   Priority  │ │Routing  ││   │
│  │  │  Manager    │ │    Queue    │ │Algorithms││   │
│  │  └─────────────┘ └─────────────┘ └─────────┘│   │
│  └─────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│               Shared Components                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │   Bundle    │ │ ContactWindow│ │Physical Layer│   │
│  │   Format    │ │   Format    │ │Integration  │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────┘
```

### API Interfaces

#### Contact Predictor Integration
```python
# Partner A provides contact predictions
contact_predictor = PartnerAContactPredictor()
current_contacts = contact_predictor.get_current_contacts(satellite_id, timestamp)
future_contacts = contact_predictor.predict_contacts(satellite_id, lookahead_hours=6)

# Routing manager uses predictions
routing_manager = DTNRoutingManager(node_id, buffer_manager, contact_predictor)
next_hop = routing_manager.route_bundle(bundle, current_contacts, timestamp)
```

#### Buffer Manager Integration
```python
# Flexible buffer manager interface
class BufferManager(Protocol):
    def store_bundle(self, bundle: Bundle) -> bool: ...
    def retrieve_bundle(self, bundle_id: str) -> Optional[Bundle]: ...
    def get_buffer_utilization(self) -> float: ...
    
# Partner implementations can use any buffer strategy
buffer_manager = PartnerBufferImplementation()
routing_manager = DTNRoutingManager(node_id, buffer_manager)
```

---

## Usage Examples

### Basic Routing Setup
```python
from src.routing import DTNRoutingManager, RoutingAlgorithm

# Initialize components
buffer_manager = SatelliteBufferManager(capacity_mb=100)
contact_predictor = SatelliteContactPredictor(orbital_model)
routing_manager = DTNRoutingManager("SAT_001", buffer_manager, contact_predictor)

# Create a bundle
bundle = Bundle(
    source="SAT_001",
    destination="GROUND_ALASKA", 
    payload=sensor_data,
    ttl_seconds=3600,  # 1 hour
    priority=BundlePriority.HIGH
)

# Get current contacts
contacts = contact_predictor.get_current_contacts("SAT_001", time.time())

# Route the bundle
next_hop = routing_manager.route_bundle(bundle, contacts, time.time())
if next_hop:
    print(f"Forward bundle to: {next_hop}")
else:
    print("Store bundle - no routes available")
```

### Algorithm Switching Example
```python
# Start with Epidemic routing for high delivery probability
routing_manager.switch_routing_algorithm(RoutingAlgorithm.EPIDEMIC)

# Monitor network congestion
while monitoring:
    metrics = routing_manager.get_routing_metrics()
    network_load = calculate_network_load(metrics)
    
    if network_load > HIGH_THRESHOLD:
        # Switch to PRoPHET for efficiency
        routing_manager.switch_routing_algorithm(RoutingAlgorithm.PROPHET)
        print("Switched to PRoPHET due to high network load")
    
    elif network_load < LOW_THRESHOLD and critical_traffic_detected():
        # Switch to Epidemic for critical traffic
        routing_manager.switch_routing_algorithm(RoutingAlgorithm.EPIDEMIC)
        print("Switched to Epidemic for critical traffic")
```

### Priority-Based Traffic Management
```python
# Create bundles with different priorities
emergency_bundle = Bundle("SAT_001", "CONTROL_CENTER", 
                         emergency_data, 600, BundlePriority.CRITICAL)

science_bundle = Bundle("SAT_001", "RESEARCH_CENTER",
                       science_data, 3600, BundlePriority.HIGH)

status_bundle = Bundle("SAT_001", "OPERATIONS",
                      status_data, 7200, BundlePriority.NORMAL)

# Route bundles - emergency gets priority
for bundle in [status_bundle, science_bundle, emergency_bundle]:
    next_hop = routing_manager.route_bundle(bundle, contacts, timestamp)
    # Emergency bundle will be routed first due to priority queue
```

### Performance Monitoring
```python
# Continuous performance monitoring
def monitor_routing_performance():
    while True:
        metrics = routing_manager.get_routing_metrics()
        
        # Check delivery ratios
        for algorithm in RoutingAlgorithm:
            delivery_ratio = metrics.delivery_ratios.get(algorithm.value, 0)
            if delivery_ratio < MINIMUM_DELIVERY_RATIO:
                print(f"Warning: {algorithm.value} delivery ratio low: {delivery_ratio:.2%}")
        
        # Check resource utilization
        buffer_util = buffer_manager.get_buffer_utilization()
        if buffer_util > BUFFER_WARNING_THRESHOLD:
            print(f"Warning: Buffer utilization high: {buffer_util:.1%}")
            
        # Adaptive algorithm selection
        optimal_algorithm = select_optimal_algorithm(metrics, network_conditions)
        if optimal_algorithm != routing_manager.active_algorithm:
            routing_manager.switch_routing_algorithm(optimal_algorithm)
        
        time.sleep(MONITORING_INTERVAL)
```

---

## Conclusion

This DTN Routing System provides a robust, scalable foundation for satellite delay-tolerant networking. The modular architecture supports multiple routing algorithms, intelligent bundle prioritization, and seamless integration with satellite mobility and contact prediction systems.

### Key Benefits:
- **Flexibility**: Pluggable routing algorithms via factory pattern
- **Intelligence**: Contact-aware routing with predictive capabilities  
- **Efficiency**: Priority-based bundle management and transmission scheduling
- **Reliability**: Comprehensive metrics and adaptive algorithm selection
- **Scalability**: Protocol-based interfaces for easy integration and extension

The system is ready for algorithm implementations (Epidemic, PRoPHET, Spray-and-Wait) and Partner A integration for a complete DTN satellite networking solution.