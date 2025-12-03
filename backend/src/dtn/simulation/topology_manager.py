"""
Topology and Contact Plan Change Management

Handles dynamic topology changes during simulation including contact plan
modifications, node failures, and network partitions.
"""

import logging
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum

from ..orbital.contact_prediction import ContactWindow
from ..core.bundle import Bundle

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of topology changes."""
    CONTACT_ADD = "contact_add"
    CONTACT_REMOVE = "contact_remove"
    CONTACT_MODIFY = "contact_modify"
    NODE_FAILURE = "node_failure"
    NODE_RECOVERY = "node_recovery"
    LINK_QUALITY_CHANGE = "link_quality_change"
    NETWORK_PARTITION = "network_partition"


@dataclass
class TopologyChange:
    """Represents a change in network topology."""
    change_id: str
    change_type: ChangeType
    timestamp: datetime
    affected_nodes: List[str]
    parameters: Dict[str, Any]
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'change_id': self.change_id,
            'change_type': self.change_type.value,
            'timestamp': self.timestamp.isoformat(),
            'affected_nodes': self.affected_nodes,
            'parameters': self.parameters,
            'description': self.description
        }


@dataclass
class NetworkMetricsSnapshot:
    """Snapshot of network metrics at a point in time."""
    timestamp: datetime
    total_nodes: int
    active_nodes: int
    total_contacts: int
    active_contacts: int
    bundles_in_network: int
    delivery_ratio: float
    average_delay: float
    network_overhead: float
    partition_count: int
    largest_partition_size: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class TopologyManager:
    """Manages topology changes during simulation."""
    
    def __init__(self, initial_contact_plan: List[ContactWindow]):
        self.initial_contact_plan = initial_contact_plan.copy()
        self.current_contact_plan = initial_contact_plan.copy()
        self.scheduled_changes: List[TopologyChange] = []
        self.applied_changes: List[TopologyChange] = []
        self.metrics_snapshots: List[NetworkMetricsSnapshot] = []
        
        # Network state tracking
        self.active_nodes: Set[str] = set()
        self.failed_nodes: Set[str] = set()
        self.node_connections: Dict[str, Set[str]] = {}
        self.contact_windows: Dict[str, ContactWindow] = {}
        
        # Initialize from contact plan
        self._initialize_from_contact_plan()
    
    def _initialize_from_contact_plan(self):
        """Initialize network state from contact plan."""
        for contact in self.current_contact_plan:
            self.active_nodes.add(contact.source_id)
            self.active_nodes.add(contact.target_id)
            self.contact_windows[contact.contact_id] = contact
            
            # Build connection graph
            if contact.source_id not in self.node_connections:
                self.node_connections[contact.source_id] = set()
            if contact.target_id not in self.node_connections:
                self.node_connections[contact.target_id] = set()
            
            self.node_connections[contact.source_id].add(contact.target_id)
            self.node_connections[contact.target_id].add(contact.source_id)
    
    def schedule_change(
        self,
        change_type: ChangeType,
        timestamp: datetime,
        affected_nodes: List[str],
        parameters: Dict[str, Any],
        description: str = ""
    ) -> str:
        """Schedule a topology change."""
        change_id = f"change_{len(self.scheduled_changes)}_{timestamp.timestamp()}"
        
        change = TopologyChange(
            change_id=change_id,
            change_type=change_type,
            timestamp=timestamp,
            affected_nodes=affected_nodes,
            parameters=parameters,
            description=description
        )
        
        self.scheduled_changes.append(change)
        self.scheduled_changes.sort(key=lambda x: x.timestamp)  # Keep sorted by time
        
        logger.info(f"Scheduled {change_type.value} at {timestamp}: {description}")
        return change_id
    
    def apply_pending_changes(self, current_time: datetime) -> List[TopologyChange]:
        """Apply all changes scheduled up to current time."""
        applied_changes = []
        
        # Find changes to apply
        changes_to_apply = [
            change for change in self.scheduled_changes 
            if change.timestamp <= current_time
        ]
        
        for change in changes_to_apply:
            try:
                self._apply_change(change)
                self.applied_changes.append(change)
                applied_changes.append(change)
                self.scheduled_changes.remove(change)
                
                logger.info(f"Applied change {change.change_id}: {change.description}")
                
            except Exception as e:
                logger.error(f"Failed to apply change {change.change_id}: {e}")
        
        return applied_changes
    
    def _apply_change(self, change: TopologyChange):
        """Apply a specific topology change."""
        if change.change_type == ChangeType.CONTACT_ADD:
            self._add_contact(change)
        elif change.change_type == ChangeType.CONTACT_REMOVE:
            self._remove_contact(change)
        elif change.change_type == ChangeType.CONTACT_MODIFY:
            self._modify_contact(change)
        elif change.change_type == ChangeType.NODE_FAILURE:
            self._fail_node(change)
        elif change.change_type == ChangeType.NODE_RECOVERY:
            self._recover_node(change)
        elif change.change_type == ChangeType.LINK_QUALITY_CHANGE:
            self._change_link_quality(change)
        elif change.change_type == ChangeType.NETWORK_PARTITION:
            self._create_partition(change)
        else:
            raise ValueError(f"Unknown change type: {change.change_type}")
    
    def _add_contact(self, change: TopologyChange):
        """Add a new contact window."""
        params = change.parameters
        
        new_contact = ContactWindow(
            contact_id=params['contact_id'],
            source_id=params['source_id'],
            target_id=params['target_id'],
            start_time=datetime.fromisoformat(params['start_time']),
            end_time=datetime.fromisoformat(params['end_time']),
            duration_seconds=params.get('duration_seconds', 0),
            data_rate=params.get('data_rate', 1000000),  # 1 Mbps default
            elevation_angle=params.get('elevation_angle', 10.0),
            distance_km=params.get('distance_km', 1000.0)
        )
        
        self.current_contact_plan.append(new_contact)
        self.contact_windows[new_contact.contact_id] = new_contact
        
        # Update node connections
        source_id = new_contact.source_id
        target_id = new_contact.target_id
        
        self.active_nodes.add(source_id)
        self.active_nodes.add(target_id)
        
        if source_id not in self.node_connections:
            self.node_connections[source_id] = set()
        if target_id not in self.node_connections:
            self.node_connections[target_id] = set()
        
        self.node_connections[source_id].add(target_id)
        self.node_connections[target_id].add(source_id)
    
    def _remove_contact(self, change: TopologyChange):
        """Remove a contact window."""
        contact_id = change.parameters['contact_id']
        
        if contact_id in self.contact_windows:
            contact = self.contact_windows[contact_id]
            
            # Remove from contact plan
            self.current_contact_plan = [
                c for c in self.current_contact_plan 
                if c.contact_id != contact_id
            ]
            
            del self.contact_windows[contact_id]
            
            # Update node connections (remove if no other contacts exist)
            self._update_node_connections_after_removal(contact)
    
    def _modify_contact(self, change: TopologyChange):
        """Modify an existing contact window."""
        contact_id = change.parameters['contact_id']
        
        if contact_id in self.contact_windows:
            contact = self.contact_windows[contact_id]
            
            # Update contact parameters
            for param, value in change.parameters.items():
                if param == 'contact_id':
                    continue
                elif param == 'start_time':
                    contact.start_time = datetime.fromisoformat(value)
                elif param == 'end_time':
                    contact.end_time = datetime.fromisoformat(value)
                elif hasattr(contact, param):
                    setattr(contact, param, value)
    
    def _fail_node(self, change: TopologyChange):
        """Simulate node failure."""
        for node_id in change.affected_nodes:
            self.failed_nodes.add(node_id)
            self.active_nodes.discard(node_id)
            
            # Remove all contacts involving this node
            self.current_contact_plan = [
                c for c in self.current_contact_plan
                if c.source_id != node_id and c.target_id != node_id
            ]
            
            # Update contact windows
            removed_contacts = [
                contact_id for contact_id, contact in self.contact_windows.items()
                if contact.source_id == node_id or contact.target_id == node_id
            ]
            
            for contact_id in removed_contacts:
                del self.contact_windows[contact_id]
            
            # Update node connections
            if node_id in self.node_connections:
                # Remove this node from all neighbor lists
                neighbors = self.node_connections[node_id].copy()
                for neighbor in neighbors:
                    if neighbor in self.node_connections:
                        self.node_connections[neighbor].discard(node_id)
                
                del self.node_connections[node_id]
    
    def _recover_node(self, change: TopologyChange):
        """Simulate node recovery."""
        for node_id in change.affected_nodes:
            if node_id in self.failed_nodes:
                self.failed_nodes.remove(node_id)
                self.active_nodes.add(node_id)
                
                # Restore contacts from initial contact plan
                for contact in self.initial_contact_plan:
                    if (contact.source_id == node_id or contact.target_id == node_id) and \
                       contact.contact_id not in self.contact_windows:
                        
                        # Only restore if both nodes are now active
                        if (contact.source_id in self.active_nodes and 
                            contact.target_id in self.active_nodes):
                            
                            self.current_contact_plan.append(contact)
                            self.contact_windows[contact.contact_id] = contact
                            
                            # Update connections
                            if contact.source_id not in self.node_connections:
                                self.node_connections[contact.source_id] = set()
                            if contact.target_id not in self.node_connections:
                                self.node_connections[contact.target_id] = set()
                            
                            self.node_connections[contact.source_id].add(contact.target_id)
                            self.node_connections[contact.target_id].add(contact.source_id)
    
    def _change_link_quality(self, change: TopologyChange):
        """Change link quality parameters."""
        contact_id = change.parameters['contact_id']
        
        if contact_id in self.contact_windows:
            contact = self.contact_windows[contact_id]
            
            # Update link quality parameters
            if 'data_rate' in change.parameters:
                contact.data_rate = change.parameters['data_rate']
            if 'elevation_angle' in change.parameters:
                contact.elevation_angle = change.parameters['elevation_angle']
            if 'distance_km' in change.parameters:
                contact.distance_km = change.parameters['distance_km']
    
    def _create_partition(self, change: TopologyChange):
        """Create a network partition by removing contacts between groups."""
        group1 = set(change.parameters.get('group1', []))
        group2 = set(change.parameters.get('group2', []))
        
        # Remove all contacts between the two groups
        contacts_to_remove = []
        
        for contact in self.current_contact_plan:
            if ((contact.source_id in group1 and contact.target_id in group2) or
                (contact.source_id in group2 and contact.target_id in group1)):
                contacts_to_remove.append(contact.contact_id)
        
        for contact_id in contacts_to_remove:
            if contact_id in self.contact_windows:
                contact = self.contact_windows[contact_id]
                self.current_contact_plan.remove(contact)
                del self.contact_windows[contact_id]
                self._update_node_connections_after_removal(contact)
    
    def _update_node_connections_after_removal(self, contact: ContactWindow):
        """Update node connections after contact removal."""
        source_id = contact.source_id
        target_id = contact.target_id
        
        # Check if there are other contacts between these nodes
        has_other_contacts = any(
            (c.source_id == source_id and c.target_id == target_id) or
            (c.source_id == target_id and c.target_id == source_id)
            for c in self.current_contact_plan
        )
        
        if not has_other_contacts:
            # Remove connection
            if source_id in self.node_connections:
                self.node_connections[source_id].discard(target_id)
            if target_id in self.node_connections:
                self.node_connections[target_id].discard(source_id)
    
    def take_metrics_snapshot(
        self,
        current_time: datetime,
        bundles_in_network: int,
        delivery_ratio: float,
        average_delay: float,
        network_overhead: float
    ):
        """Take a snapshot of current network metrics."""
        # Calculate partition information
        partitions = self._calculate_network_partitions()
        partition_count = len(partitions)
        largest_partition_size = max(len(p) for p in partitions) if partitions else 0
        
        snapshot = NetworkMetricsSnapshot(
            timestamp=current_time,
            total_nodes=len(self.active_nodes) + len(self.failed_nodes),
            active_nodes=len(self.active_nodes),
            total_contacts=len(self.current_contact_plan),
            active_contacts=len([c for c in self.current_contact_plan if c.start_time <= current_time <= c.end_time]),
            bundles_in_network=bundles_in_network,
            delivery_ratio=delivery_ratio,
            average_delay=average_delay,
            network_overhead=network_overhead,
            partition_count=partition_count,
            largest_partition_size=largest_partition_size
        )
        
        self.metrics_snapshots.append(snapshot)
        
        # Limit snapshot history
        if len(self.metrics_snapshots) > 1000:
            self.metrics_snapshots = self.metrics_snapshots[-500:]
    
    def _calculate_network_partitions(self) -> List[Set[str]]:
        """Calculate current network partitions using graph connectivity."""
        if not self.active_nodes:
            return []
        
        partitions = []
        unvisited = self.active_nodes.copy()
        
        while unvisited:
            # Start DFS from an unvisited node
            start_node = unvisited.pop()
            current_partition = set([start_node])
            stack = [start_node]
            
            while stack:
                node = stack.pop()
                
                # Visit all connected neighbors
                if node in self.node_connections:
                    for neighbor in self.node_connections[node]:
                        if neighbor in unvisited:
                            unvisited.remove(neighbor)
                            current_partition.add(neighbor)
                            stack.append(neighbor)
            
            partitions.append(current_partition)
        
        return partitions
    
    def get_current_contact_plan(self) -> List[ContactWindow]:
        """Get current contact plan."""
        return self.current_contact_plan.copy()
    
    def analyze_topology_changes(self) -> Dict[str, Any]:
        """Analyze the impact of topology changes."""
        if len(self.metrics_snapshots) < 2:
            return {"error": "Insufficient data for analysis"}
        
        # Find snapshots before and after major changes
        analysis = {
            "total_changes": len(self.applied_changes),
            "change_types": {},
            "performance_impact": {},
            "partition_analysis": {},
            "timeline": []
        }
        
        # Count change types
        for change in self.applied_changes:
            change_type = change.change_type.value
            if change_type not in analysis["change_types"]:
                analysis["change_types"][change_type] = 0
            analysis["change_types"][change_type] += 1
        
        # Analyze performance before/after changes
        if self.metrics_snapshots:
            first_snapshot = self.metrics_snapshots[0]
            last_snapshot = self.metrics_snapshots[-1]
            
            analysis["performance_impact"] = {
                "delivery_ratio_change": last_snapshot.delivery_ratio - first_snapshot.delivery_ratio,
                "delay_change": last_snapshot.average_delay - first_snapshot.average_delay,
                "overhead_change": last_snapshot.network_overhead - first_snapshot.network_overhead,
                "partition_count_change": last_snapshot.partition_count - first_snapshot.partition_count
            }
        
        # Create timeline of significant events
        for change in self.applied_changes:
            # Find nearby snapshots
            before_snapshot = None
            after_snapshot = None
            
            for snapshot in self.metrics_snapshots:
                if snapshot.timestamp <= change.timestamp:
                    before_snapshot = snapshot
                elif after_snapshot is None and snapshot.timestamp > change.timestamp:
                    after_snapshot = snapshot
                    break
            
            if before_snapshot and after_snapshot:
                timeline_entry = {
                    "timestamp": change.timestamp.isoformat(),
                    "change_type": change.change_type.value,
                    "description": change.description,
                    "impact": {
                        "delivery_ratio_delta": after_snapshot.delivery_ratio - before_snapshot.delivery_ratio,
                        "delay_delta": after_snapshot.average_delay - before_snapshot.average_delay,
                        "partition_count_delta": after_snapshot.partition_count - before_snapshot.partition_count
                    }
                }
                analysis["timeline"].append(timeline_entry)
        
        return analysis
    
    def export_change_log(self) -> Dict[str, Any]:
        """Export complete change log for analysis."""
        return {
            "initial_contact_plan": [contact.__dict__ for contact in self.initial_contact_plan],
            "scheduled_changes": [change.to_dict() for change in self.scheduled_changes],
            "applied_changes": [change.to_dict() for change in self.applied_changes],
            "metrics_snapshots": [snapshot.to_dict() for snapshot in self.metrics_snapshots],
            "current_active_nodes": list(self.active_nodes),
            "failed_nodes": list(self.failed_nodes)
        }


def create_sample_topology_changes(contact_plan: List[ContactWindow], simulation_duration_hours: int = 24) -> List[TopologyChange]:
    """Create sample topology changes for demonstration."""
    changes = []
    start_time = datetime.now()
    
    # Node failure at 25% into simulation
    failure_time = start_time + timedelta(hours=simulation_duration_hours * 0.25)
    changes.append(TopologyChange(
        change_id="sample_node_failure",
        change_type=ChangeType.NODE_FAILURE,
        timestamp=failure_time,
        affected_nodes=["starlink_sat_001"],
        parameters={},
        description="Simulated satellite failure"
    ))
    
    # Network partition at 50% into simulation
    partition_time = start_time + timedelta(hours=simulation_duration_hours * 0.5)
    changes.append(TopologyChange(
        change_id="sample_partition",
        change_type=ChangeType.NETWORK_PARTITION,
        timestamp=partition_time,
        affected_nodes=[],
        parameters={
            "group1": ["starlink_sat_001", "starlink_sat_002"],
            "group2": ["starlink_sat_003", "starlink_sat_004"]
        },
        description="Simulated network partition due to solar storm"
    ))
    
    # Node recovery at 75% into simulation
    recovery_time = start_time + timedelta(hours=simulation_duration_hours * 0.75)
    changes.append(TopologyChange(
        change_id="sample_recovery",
        change_type=ChangeType.NODE_RECOVERY,
        timestamp=recovery_time,
        affected_nodes=["starlink_sat_001"],
        parameters={},
        description="Satellite recovery after repair"
    ))
    
    return changes