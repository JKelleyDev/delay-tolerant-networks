"""
DTN Connectivity Restoration

Implements duplicate suppression, custody transfer, and connection restoration
mechanisms for delay-tolerant networking.
"""

import logging
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Set, List, Optional, Any, Tuple
from enum import Enum

from ..core.bundle import Bundle, EndpointID

logger = logging.getLogger(__name__)


class CustodyState(Enum):
    """Custody transfer states."""
    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    ACCEPTED = "accepted"
    RELEASED = "released"
    FAILED = "failed"


@dataclass
class CustodyRecord:
    """Record of custody transfer for a bundle."""
    bundle_id: str
    custodian_node_id: str
    custody_accepted_time: datetime
    custody_timeout: datetime
    next_hop_node_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    @property
    def is_expired(self) -> bool:
        """Check if custody has timed out."""
        return datetime.now() > self.custody_timeout


@dataclass
class DuplicateRecord:
    """Record for duplicate suppression."""
    bundle_hash: str
    bundle_id: str
    source_node: str
    destination_node: str
    creation_time: datetime
    last_seen: datetime
    hop_count: int
    
    def update_last_seen(self, hop_count: int):
        """Update when this duplicate was last seen."""
        self.last_seen = datetime.now()
        self.hop_count = min(self.hop_count, hop_count)  # Track shortest path


@dataclass
class ConnectionEvent:
    """Event when connectivity is restored."""
    event_time: datetime
    event_type: str  # "connection_restored", "partition_healed", "node_recovered"
    affected_nodes: List[str]
    description: str


class DuplicateSuppressionManager:
    """Manages duplicate detection and suppression."""
    
    def __init__(self, cleanup_interval_seconds: int = 3600):
        self.duplicate_records: Dict[str, DuplicateRecord] = {}
        self.cleanup_interval = timedelta(seconds=cleanup_interval_seconds)
        self.last_cleanup = datetime.now()
    
    def calculate_bundle_hash(self, bundle: Bundle) -> str:
        """Calculate a hash for bundle duplicate detection."""
        # Use bundle ID, source, destination, and creation time
        hash_data = f"{bundle.bundle_id}_{bundle.source}_{bundle.destination}_{bundle.creation_timestamp.isoformat()}"
        return hashlib.sha256(hash_data.encode()).hexdigest()[:16]
    
    def is_duplicate(self, bundle: Bundle) -> bool:
        """Check if bundle is a duplicate."""
        bundle_hash = self.calculate_bundle_hash(bundle)
        
        if bundle_hash in self.duplicate_records:
            record = self.duplicate_records[bundle_hash]
            record.update_last_seen(bundle.hop_count)
            logger.debug(f"Duplicate bundle detected: {bundle.bundle_id}")
            return True
        
        # Not a duplicate, record it
        self.duplicate_records[bundle_hash] = DuplicateRecord(
            bundle_hash=bundle_hash,
            bundle_id=bundle.bundle_id,
            source_node=bundle.source.ssp,
            destination_node=bundle.destination.ssp,
            creation_time=bundle.creation_timestamp,
            last_seen=datetime.now(),
            hop_count=bundle.hop_count
        )
        
        return False
    
    def cleanup_old_records(self, current_time: datetime):
        """Remove old duplicate records."""
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        # Remove records older than 24 hours
        cutoff_time = current_time - timedelta(hours=24)
        
        old_hashes = [
            bundle_hash for bundle_hash, record in self.duplicate_records.items()
            if record.last_seen < cutoff_time
        ]
        
        for bundle_hash in old_hashes:
            del self.duplicate_records[bundle_hash]
        
        self.last_cleanup = current_time
        
        if old_hashes:
            logger.debug(f"Cleaned up {len(old_hashes)} old duplicate records")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get duplicate suppression statistics."""
        return {
            'total_records': len(self.duplicate_records),
            'records_by_age': {
                'last_hour': len([r for r in self.duplicate_records.values() 
                                if (datetime.now() - r.last_seen).total_seconds() < 3600]),
                'last_day': len([r for r in self.duplicate_records.values() 
                               if (datetime.now() - r.last_seen).total_seconds() < 86400])
            }
        }


class CustodyTransferManager:
    """Manages custody transfer for reliable delivery."""
    
    def __init__(self, default_custody_timeout_seconds: int = 1800):  # 30 minutes
        self.custody_records: Dict[str, CustodyRecord] = {}
        self.default_timeout = timedelta(seconds=default_custody_timeout_seconds)
        self.custody_signals_sent = 0
        self.custody_acceptances = 0
        self.custody_failures = 0
    
    def request_custody(
        self,
        bundle: Bundle,
        custodian_node_id: str,
        next_hop_node_id: Optional[str] = None,
        timeout_override: Optional[timedelta] = None
    ) -> bool:
        """Request custody transfer for a bundle."""
        if not bundle.custody_requested:
            logger.debug(f"Custody not requested for bundle {bundle.bundle_id}")
            return False
        
        if bundle.bundle_id in self.custody_records:
            logger.warning(f"Custody already pending for bundle {bundle.bundle_id}")
            return False
        
        timeout = timeout_override or self.default_timeout
        custody_timeout = datetime.now() + timeout
        
        record = CustodyRecord(
            bundle_id=bundle.bundle_id,
            custodian_node_id=custodian_node_id,
            custody_accepted_time=datetime.now(),
            custody_timeout=custody_timeout,
            next_hop_node_id=next_hop_node_id
        )
        
        self.custody_records[bundle.bundle_id] = record
        self.custody_signals_sent += 1
        
        logger.info(f"Custody requested for bundle {bundle.bundle_id} by {custodian_node_id}")
        return True
    
    def accept_custody(self, bundle_id: str) -> bool:
        """Accept custody for a bundle."""
        if bundle_id not in self.custody_records:
            logger.warning(f"No custody record found for bundle {bundle_id}")
            return False
        
        record = self.custody_records[bundle_id]
        
        if record.is_expired:
            logger.warning(f"Custody timeout expired for bundle {bundle_id}")
            self.custody_failures += 1
            return False
        
        self.custody_acceptances += 1
        logger.info(f"Custody accepted for bundle {bundle_id}")
        return True
    
    def release_custody(self, bundle_id: str, reason: str = "delivered") -> bool:
        """Release custody when bundle is delivered or transferred."""
        if bundle_id in self.custody_records:
            record = self.custody_records[bundle_id]
            del self.custody_records[bundle_id]
            
            logger.info(f"Custody released for bundle {bundle_id}: {reason}")
            return True
        
        return False
    
    def check_custody_timeouts(self, current_time: datetime) -> List[str]:
        """Check for custody timeouts and return expired bundle IDs."""
        expired_bundles = []
        
        for bundle_id, record in list(self.custody_records.items()):
            if record.is_expired:
                expired_bundles.append(bundle_id)
                
                # Retry if within retry limit
                if record.retry_count < record.max_retries:
                    record.retry_count += 1
                    record.custody_timeout = current_time + self.default_timeout
                    logger.warning(f"Custody timeout for bundle {bundle_id}, retrying ({record.retry_count}/{record.max_retries})")
                else:
                    # Max retries exceeded
                    del self.custody_records[bundle_id]
                    self.custody_failures += 1
                    logger.error(f"Custody failed permanently for bundle {bundle_id}")
        
        return expired_bundles
    
    def get_custody_status(self, bundle_id: str) -> Optional[CustodyRecord]:
        """Get custody status for a bundle."""
        return self.custody_records.get(bundle_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get custody transfer statistics."""
        return {
            'active_custody_records': len(self.custody_records),
            'custody_signals_sent': self.custody_signals_sent,
            'custody_acceptances': self.custody_acceptances,
            'custody_failures': self.custody_failures,
            'success_rate': (self.custody_acceptances / max(1, self.custody_signals_sent)) * 100
        }


class ConnectivityRestorationManager:
    """Manages connectivity restoration and network healing."""
    
    def __init__(self):
        self.connection_events: List[ConnectionEvent] = []
        self.partition_history: List[Tuple[datetime, int]] = []  # (time, partition_count)
        self.bundle_queues: Dict[str, List[Bundle]] = {}  # node_id -> queued bundles
        self.failed_nodes: Set[str] = set()
        self.recovered_nodes: Set[str] = set()
    
    def record_connection_event(
        self,
        event_type: str,
        affected_nodes: List[str],
        description: str = ""
    ):
        """Record a connectivity event."""
        event = ConnectionEvent(
            event_time=datetime.now(),
            event_type=event_type,
            affected_nodes=affected_nodes,
            description=description
        )
        
        self.connection_events.append(event)
        
        # Limit event history
        if len(self.connection_events) > 1000:
            self.connection_events = self.connection_events[-500:]
        
        logger.info(f"Connectivity event: {event_type} - {description}")
    
    def record_partition_state(self, partition_count: int):
        """Record current network partition state."""
        self.partition_history.append((datetime.now(), partition_count))
        
        # Limit partition history
        if len(self.partition_history) > 1000:
            self.partition_history = self.partition_history[-500:]
    
    def queue_bundle_for_restoration(self, bundle: Bundle, target_node: str):
        """Queue bundle for delivery when connectivity is restored."""
        if target_node not in self.bundle_queues:
            self.bundle_queues[target_node] = []
        
        self.bundle_queues[target_node].append(bundle)
        logger.debug(f"Queued bundle {bundle.bundle_id} for node {target_node}")
    
    def handle_node_recovery(self, node_id: str) -> List[Bundle]:
        """Handle node recovery and return queued bundles."""
        if node_id in self.failed_nodes:
            self.failed_nodes.remove(node_id)
        
        self.recovered_nodes.add(node_id)
        
        # Record recovery event
        self.record_connection_event(
            "node_recovered",
            [node_id],
            f"Node {node_id} has recovered from failure"
        )
        
        # Return queued bundles for this node
        queued_bundles = self.bundle_queues.get(node_id, [])
        if queued_bundles:
            self.bundle_queues[node_id] = []
            logger.info(f"Releasing {len(queued_bundles)} queued bundles for recovered node {node_id}")
        
        return queued_bundles
    
    def handle_partition_healing(
        self,
        partition1_nodes: List[str],
        partition2_nodes: List[str]
    ) -> List[Bundle]:
        """Handle partition healing and redistribute queued bundles."""
        all_affected_nodes = partition1_nodes + partition2_nodes
        
        self.record_connection_event(
            "partition_healed",
            all_affected_nodes,
            f"Network partition healed between {len(partition1_nodes)} and {len(partition2_nodes)} nodes"
        )
        
        # Collect and redistribute queued bundles
        released_bundles = []
        
        for node_id in all_affected_nodes:
            if node_id in self.bundle_queues:
                released_bundles.extend(self.bundle_queues[node_id])
                self.bundle_queues[node_id] = []
        
        logger.info(f"Released {len(released_bundles)} bundles due to partition healing")
        return released_bundles
    
    def detect_connectivity_restoration(
        self,
        current_partitions: List[Set[str]],
        previous_partitions: List[Set[str]]
    ) -> List[ConnectionEvent]:
        """Detect connectivity restoration events."""
        restoration_events = []
        
        # Check if partition count decreased (partitions merged)
        if len(current_partitions) < len(previous_partitions):
            # Find which nodes were connected
            current_all_nodes = set()
            for partition in current_partitions:
                current_all_nodes.update(partition)
            
            previous_all_nodes = set()
            for partition in previous_partitions:
                previous_all_nodes.update(partition)
            
            # Nodes that are now connected but weren't before
            newly_connected = current_all_nodes - previous_all_nodes
            
            if newly_connected:
                event = ConnectionEvent(
                    event_time=datetime.now(),
                    event_type="connection_restored",
                    affected_nodes=list(newly_connected),
                    description=f"Connectivity restored for {len(newly_connected)} nodes"
                )
                restoration_events.append(event)
        
        # Check if any previously isolated nodes joined larger partitions
        for current_partition in current_partitions:
            if len(current_partition) > 1:
                # Check if any nodes in this partition were isolated before
                for previous_partition in previous_partitions:
                    if (len(previous_partition) == 1 and 
                        previous_partition.issubset(current_partition)):
                        
                        isolated_node = list(previous_partition)[0]
                        event = ConnectionEvent(
                            event_time=datetime.now(),
                            event_type="node_reconnected",
                            affected_nodes=[isolated_node],
                            description=f"Isolated node {isolated_node} reconnected to network"
                        )
                        restoration_events.append(event)
        
        return restoration_events
    
    def get_restoration_statistics(self) -> Dict[str, Any]:
        """Get connectivity restoration statistics."""
        # Analyze partition stability
        partition_stability = 0.0
        if len(self.partition_history) > 1:
            stable_periods = 0
            for i in range(1, len(self.partition_history)):
                if self.partition_history[i][1] == self.partition_history[i-1][1]:
                    stable_periods += 1
            partition_stability = stable_periods / (len(self.partition_history) - 1) * 100
        
        # Count event types
        event_counts = {}
        for event in self.connection_events:
            event_type = event.event_type
            if event_type not in event_counts:
                event_counts[event_type] = 0
            event_counts[event_type] += 1
        
        # Calculate queued bundle statistics
        total_queued_bundles = sum(len(bundles) for bundles in self.bundle_queues.values())
        nodes_with_queued_bundles = len([node for node, bundles in self.bundle_queues.items() if bundles])
        
        return {
            'total_connection_events': len(self.connection_events),
            'event_type_counts': event_counts,
            'partition_stability_percent': partition_stability,
            'current_partition_count': self.partition_history[-1][1] if self.partition_history else 0,
            'total_queued_bundles': total_queued_bundles,
            'nodes_with_queued_bundles': nodes_with_queued_bundles,
            'failed_nodes': len(self.failed_nodes),
            'recovered_nodes': len(self.recovered_nodes)
        }


class DTNRestorationService:
    """Combined service for DTN connectivity restoration."""
    
    def __init__(self):
        self.duplicate_manager = DuplicateSuppressionManager()
        self.custody_manager = CustodyTransferManager()
        self.connectivity_manager = ConnectivityRestorationManager()
    
    def process_incoming_bundle(
        self,
        bundle: Bundle,
        from_node_id: str,
        current_time: datetime
    ) -> Tuple[bool, str]:
        """Process incoming bundle with restoration checks."""
        # Clean up old records
        self.duplicate_manager.cleanup_old_records(current_time)
        
        # Check for duplicates
        if self.duplicate_manager.is_duplicate(bundle):
            return False, "Duplicate bundle suppressed"
        
        # Check custody timeouts
        expired_bundles = self.custody_manager.check_custody_timeouts(current_time)
        if expired_bundles:
            logger.warning(f"Found {len(expired_bundles)} bundles with expired custody")
        
        # Handle custody transfer if requested
        if bundle.custody_requested:
            self.custody_manager.request_custody(bundle, from_node_id)
        
        return True, "Bundle accepted"
    
    def handle_connectivity_change(
        self,
        event_type: str,
        affected_nodes: List[str],
        current_partitions: List[Set[str]] = None,
        previous_partitions: List[Set[str]] = None
    ) -> List[Bundle]:
        """Handle connectivity changes and return bundles to reprocess."""
        released_bundles = []
        
        if event_type == "node_recovery":
            for node_id in affected_nodes:
                released_bundles.extend(self.connectivity_manager.handle_node_recovery(node_id))
        
        elif event_type == "partition_healing" and len(affected_nodes) >= 2:
            mid_point = len(affected_nodes) // 2
            partition1 = affected_nodes[:mid_point]
            partition2 = affected_nodes[mid_point:]
            released_bundles.extend(
                self.connectivity_manager.handle_partition_healing(partition1, partition2)
            )
        
        # Detect and record restoration events
        if current_partitions and previous_partitions:
            restoration_events = self.connectivity_manager.detect_connectivity_restoration(
                current_partitions, previous_partitions
            )
            
            for event in restoration_events:
                self.connectivity_manager.connection_events.append(event)
        
        return released_bundles
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive restoration statistics."""
        return {
            'duplicate_suppression': self.duplicate_manager.get_statistics(),
            'custody_transfer': self.custody_manager.get_statistics(),
            'connectivity_restoration': self.connectivity_manager.get_restoration_statistics(),
            'service_status': {
                'active_custody_records': len(self.custody_manager.custody_records),
                'duplicate_records': len(self.duplicate_manager.duplicate_records),
                'queued_bundles': sum(
                    len(bundles) for bundles in self.connectivity_manager.bundle_queues.values()
                ),
                'restoration_events_last_hour': len([
                    event for event in self.connectivity_manager.connection_events
                    if (datetime.now() - event.event_time).total_seconds() < 3600
                ])
            }
        }
    
    def cleanup_expired_records(self, current_time: datetime):
        """Clean up expired records across all managers."""
        self.duplicate_manager.cleanup_old_records(current_time)
        expired_custody = self.custody_manager.check_custody_timeouts(current_time)
        
        if expired_custody:
            logger.info(f"Cleaned up {len(expired_custody)} expired custody records")