import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json
import hashlib


class BundlePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Bundle:
    source: str
    destination: str
    payload: bytes
    ttl_seconds: int
    priority: BundlePriority = BundlePriority.NORMAL
    store_and_forward: bool = True
    id: Optional[str] = None
    timestamp: Optional[float] = None
    sequence: Optional[int] = None
    creation_time: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.creation_time is None:
            self.creation_time = time.time()
        if self.sequence is None:
            self.sequence = self._generate_sequence()
        if self.id is None:
            self.id = self._generate_id()

    def _generate_sequence(self) -> int:
        return int(time.time() * 1000000) % 1000000

    def _generate_id(self) -> str:
        id_string = f"{self.source}:{self.timestamp}:{self.sequence}"
        return hashlib.sha256(id_string.encode()).hexdigest()[:16]

    def is_expired(self) -> bool:
        current_time = time.time()
        assert self.creation_time is not None
        return (current_time - self.creation_time) > self.ttl_seconds

    def remaining_ttl(self) -> int:
        current_time = time.time()
        assert self.creation_time is not None
        elapsed = current_time - self.creation_time
        return max(0, int(self.ttl_seconds - elapsed))

    def validate(self) -> bool:
        if not self.source or not self.destination:
            return False
        if self.ttl_seconds <= 0:
            return False
        if not self.payload:
            return False
        if self.is_expired():
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "destination": self.destination,
            "payload": self.payload.hex(),
            "ttl_seconds": self.ttl_seconds,
            "priority": self.priority.value,
            "store_and_forward": self.store_and_forward,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "creation_time": self.creation_time,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Bundle":
        return cls(
            id=data["id"],
            source=data["source"],
            destination=data["destination"],
            payload=bytes.fromhex(data["payload"]),
            ttl_seconds=data["ttl_seconds"],
            priority=BundlePriority(data["priority"]),
            store_and_forward=data["store_and_forward"],
            timestamp=data["timestamp"],
            sequence=data["sequence"],
            creation_time=data["creation_time"],
        )

    def serialize(self) -> bytes:
        return json.dumps(self.to_dict()).encode("utf-8")

    @classmethod
    def deserialize(cls, data: bytes) -> "Bundle":
        return cls.from_dict(json.loads(data.decode("utf-8")))


class BufferManager:
    """Manages bundle storage with TTL expiration and priority-based dropping."""
    
    def __init__(self, max_size_mb: int = 20):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.bundles: Dict[str, Bundle] = {}
        self.total_size = 0
        
    def add_bundle(self, bundle: Bundle) -> bool:
        """Add bundle to buffer, handling overflow with priority-based dropping."""
        if not bundle.validate():
            return False
            
        if bundle.id in self.bundles:
            return True  # Already have this bundle
            
        bundle_size = len(bundle.serialize())
        
        # Make space if needed
        while self.total_size + bundle_size > self.max_size_bytes:
            if not self._evict_bundle():
                return False  # Can't make space
                
        self.bundles[bundle.id] = bundle
        self.total_size += bundle_size
        return True
        
    def _evict_bundle(self) -> bool:
        """Remove lowest priority, oldest bundle."""
        if not self.bundles:
            return False
            
        # Sort by priority (low first), then by age (old first)
        sorted_bundles = sorted(
            self.bundles.values(),
            key=lambda b: (b.priority.value, b.creation_time)
        )
        
        bundle_to_remove = sorted_bundles[0]
        self.remove_bundle(bundle_to_remove.id)
        return True
        
    def remove_bundle(self, bundle_id: str) -> bool:
        """Remove bundle from buffer."""
        if bundle_id not in self.bundles:
            return False
            
        bundle = self.bundles[bundle_id]
        bundle_size = len(bundle.serialize())
        del self.bundles[bundle_id]
        self.total_size -= bundle_size
        return True
        
    def get_bundle(self, bundle_id: str) -> Optional[Bundle]:
        """Get bundle by ID."""
        return self.bundles.get(bundle_id)
        
    def get_bundles_for_destination(self, destination: str) -> List[Bundle]:
        """Get all bundles destined for a specific node."""
        return [b for b in self.bundles.values() if b.destination == destination]
        
    def cleanup_expired(self) -> int:
        """Remove expired bundles, return count removed."""
        expired_ids = [bid for bid, bundle in self.bundles.items() if bundle.is_expired()]
        for bid in expired_ids:
            self.remove_bundle(bid)
        return len(expired_ids)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        return {
            "total_bundles": len(self.bundles),
            "total_size_bytes": self.total_size,
            "total_size_mb": self.total_size / (1024 * 1024),
            "utilization_percent": (self.total_size / self.max_size_bytes) * 100,
            "by_priority": {
                priority.name: len([b for b in self.bundles.values() if b.priority == priority])
                for priority in BundlePriority
            }
        }


class Contact:
    """Represents a communication link between two nodes."""
    
    def __init__(self, source: str, destination: str, start_time: float, 
                 end_time: float, data_rate_bps: int = 1000000):
        self.source = source
        self.destination = destination
        self.start_time = start_time
        self.end_time = end_time
        self.data_rate_bps = data_rate_bps
        self.bytes_transmitted = 0
        
    def is_active(self, current_time: float) -> bool:
        """Check if contact is currently active."""
        return self.start_time <= current_time <= self.end_time
        
    def remaining_capacity(self, current_time: float) -> int:
        """Calculate remaining transmission capacity in bytes."""
        if not self.is_active(current_time):
            return 0
            
        remaining_time = self.end_time - current_time
        total_capacity = int(self.data_rate_bps * remaining_time / 8)
        return max(0, total_capacity - self.bytes_transmitted)
        
    def can_transmit(self, bundle: Bundle, current_time: float) -> bool:
        """Check if bundle can be transmitted over this contact."""
        if not self.is_active(current_time):
            return False
            
        bundle_size = len(bundle.serialize())
        return self.remaining_capacity(current_time) >= bundle_size
        
    def transmit_bundle(self, bundle: Bundle) -> bool:
        """Record bundle transmission."""
        bundle_size = len(bundle.serialize())
        if self.bytes_transmitted + bundle_size <= self.remaining_capacity(time.time()):
            self.bytes_transmitted += bundle_size
            return True
        return False
