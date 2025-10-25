"""
DTN Bundle Protocol Implementation

Based on RFC 9171 - Bundle Protocol Version 7
Provides message encapsulation for delay-tolerant networks.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
import uuid
import json


class BundleFlags(Enum):
    """Bundle processing flags."""
    IS_FRAGMENT = 1
    ADMIN_RECORD = 2
    DONT_FRAGMENT = 4
    CUSTODY_XFER_REQUESTED = 8
    SINGLETON_DESTINATION = 16
    ACK_BY_APP = 32


class BundlePriority(Enum):
    """Bundle priority levels."""
    BULK = 0
    NORMAL = 1
    EXPEDITED = 2
    CRITICAL = 3


@dataclass
class EndpointID:
    """DTN Endpoint Identifier."""
    scheme: str
    ssp: str  # Scheme-specific part
    
    def __str__(self) -> str:
        return f"{self.scheme}:{self.ssp}"
    
    @classmethod
    def from_string(cls, eid_str: str) -> 'EndpointID':
        """Create EndpointID from string representation."""
        if ':' not in eid_str:
            raise ValueError(f"Invalid EID format: {eid_str}")
        scheme, ssp = eid_str.split(':', 1)
        return cls(scheme, ssp)


@dataclass
class Bundle:
    """DTN Bundle message."""
    
    # Primary Bundle Block
    bundle_id: str
    source: EndpointID
    destination: EndpointID
    report_to: EndpointID
    creation_timestamp: datetime
    lifetime: timedelta
    priority: BundlePriority = BundlePriority.NORMAL
    flags: List[BundleFlags] = None
    
    # Payload
    payload: bytes = b""
    payload_size: int = 0
    
    # Administrative data
    custody_requested: bool = False
    fragment_offset: int = 0
    total_length: int = 0
    
    # Routing metadata
    previous_hop: Optional[str] = None
    route_path: List[str] = None
    hop_count: int = 0
    
    def __post_init__(self):
        """Initialize computed fields."""
        if self.flags is None:
            self.flags = []
        if self.route_path is None:
            self.route_path = []
        if self.payload:
            self.payload_size = len(self.payload)
        if not self.bundle_id:
            self.bundle_id = str(uuid.uuid4())
    
    @property
    def age(self) -> timedelta:
        """Current age of the bundle."""
        return datetime.now() - self.creation_timestamp
    
    @property
    def remaining_lifetime(self) -> timedelta:
        """Remaining lifetime before expiration."""
        return self.lifetime - self.age
    
    @property
    def is_expired(self) -> bool:
        """Check if bundle has expired."""
        return self.remaining_lifetime <= timedelta(0)
    
    @property
    def is_fragment(self) -> bool:
        """Check if bundle is a fragment."""
        return BundleFlags.IS_FRAGMENT in self.flags
    
    def add_hop(self, node_id: str) -> None:
        """Add a hop to the route path."""
        self.previous_hop = self.route_path[-1] if self.route_path else None
        self.route_path.append(node_id)
        self.hop_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bundle to dictionary for serialization."""
        return {
            'bundle_id': self.bundle_id,
            'source': str(self.source),
            'destination': str(self.destination),
            'report_to': str(self.report_to),
            'creation_timestamp': self.creation_timestamp.isoformat(),
            'lifetime_seconds': self.lifetime.total_seconds(),
            'priority': self.priority.value,
            'flags': [f.value for f in self.flags],
            'payload_size': self.payload_size,
            'custody_requested': self.custody_requested,
            'fragment_offset': self.fragment_offset,
            'total_length': self.total_length,
            'previous_hop': self.previous_hop,
            'route_path': self.route_path,
            'hop_count': self.hop_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Bundle':
        """Create bundle from dictionary."""
        return cls(
            bundle_id=data['bundle_id'],
            source=EndpointID.from_string(data['source']),
            destination=EndpointID.from_string(data['destination']),
            report_to=EndpointID.from_string(data['report_to']),
            creation_timestamp=datetime.fromisoformat(data['creation_timestamp']),
            lifetime=timedelta(seconds=data['lifetime_seconds']),
            priority=BundlePriority(data['priority']),
            flags=[BundleFlags(f) for f in data['flags']],
            payload_size=data['payload_size'],
            custody_requested=data['custody_requested'],
            fragment_offset=data['fragment_offset'],
            total_length=data['total_length'],
            previous_hop=data['previous_hop'],
            route_path=data['route_path'],
            hop_count=data['hop_count']
        )


class BundleStore:
    """Bundle storage and management."""
    
    def __init__(self, max_size: int = 100 * 1024 * 1024):  # 100MB default
        self.max_size = max_size
        self.bundles: Dict[str, Bundle] = {}
        self.size_used = 0
    
    def store(self, bundle: Bundle) -> bool:
        """Store a bundle if space available."""
        if bundle.bundle_id in self.bundles:
            return True  # Already stored
        
        if self.size_used + bundle.payload_size > self.max_size:
            # Need to make space - drop oldest bundles
            self._make_space(bundle.payload_size)
        
        if self.size_used + bundle.payload_size <= self.max_size:
            self.bundles[bundle.bundle_id] = bundle
            self.size_used += bundle.payload_size
            return True
        
        return False  # Could not store
    
    def retrieve(self, bundle_id: str) -> Optional[Bundle]:
        """Retrieve a bundle by ID."""
        return self.bundles.get(bundle_id)
    
    def remove(self, bundle_id: str) -> bool:
        """Remove a bundle from storage."""
        if bundle_id in self.bundles:
            bundle = self.bundles.pop(bundle_id)
            self.size_used -= bundle.payload_size
            return True
        return False
    
    def get_all_bundles(self) -> List[Bundle]:
        """Get all stored bundles."""
        return list(self.bundles.values())
    
    def cleanup_expired(self) -> int:
        """Remove expired bundles and return count removed."""
        expired_ids = [
            bid for bid, bundle in self.bundles.items()
            if bundle.is_expired
        ]
        
        for bid in expired_ids:
            self.remove(bid)
        
        return len(expired_ids)
    
    def _make_space(self, required_space: int) -> None:
        """Make space by removing oldest bundles."""
        sorted_bundles = sorted(
            self.bundles.items(),
            key=lambda x: x[1].creation_timestamp
        )
        
        space_freed = 0
        for bundle_id, bundle in sorted_bundles:
            if space_freed >= required_space:
                break
            self.remove(bundle_id)
            space_freed += bundle.payload_size
    
    @property
    def utilization(self) -> float:
        """Storage utilization as percentage."""
        return (self.size_used / self.max_size) * 100 if self.max_size > 0 else 0
    
    @property
    def bundle_count(self) -> int:
        """Number of stored bundles."""
        return len(self.bundles)


def create_test_bundle(source: str, dest: str, payload: str = "Test message") -> Bundle:
    """Create a test bundle for demonstrations."""
    return Bundle(
        bundle_id=str(uuid.uuid4()),
        source=EndpointID.from_string(source),
        destination=EndpointID.from_string(dest),
        report_to=EndpointID.from_string(source),
        creation_timestamp=datetime.now(),
        lifetime=timedelta(hours=24),
        payload=payload.encode('utf-8'),
        priority=BundlePriority.NORMAL
    )