import time
from typing import Dict, Any, Optional
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
