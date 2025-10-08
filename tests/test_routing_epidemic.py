import time
import pytest
from src.bundle import Bundle, BundlePriority
from src.routing_epidemic import EpidemicRouter


# ----------------------------
# Dummy helper classes
# ----------------------------
class DummyBufferManager:
    """Simple stand-in for real buffer manager."""

    def __init__(self):
        self.bundles = {}

    def store_bundle(self, bundle: Bundle):
        self.bundles[bundle.id] = bundle

    def has_bundle(self, bundle_id: str) -> bool:
        return bundle_id in self.bundles

    def get_all_bundles(self):
        return list(self.bundles.values())


class DummyContact:
    """Simple contact window stand-in."""

    def __init__(self, peer_id: str, duration: float = 30.0, quality: float = 1.0):
        self.peer_id = peer_id
        self.duration = duration
        self.quality = quality


# ----------------------------
# Bundle helper
# ----------------------------
def make_bundle(bundle_id: str, priority=BundlePriority.NORMAL, ttl=300):
    """Helper to create a simple Bundle compatible with your group's Bundle class."""
    b = Bundle(
        source="A",
        destination="B",
        payload=f"Payload for {bundle_id}".encode(),  # payload must be bytes
        ttl_seconds=ttl,
        priority=priority,
        creation_time=time.time(),
    )
    b.id = bundle_id  # override for predictable testing
    return b


# ----------------------------
# Test Cases
# ----------------------------
def test_epidemic_basic_flooding():
    """Test that EpidemicRouter floods a bundle to all available contacts."""
    buffer_mgr = DummyBufferManager()
    router = EpidemicRouter("nodeA", buffer_mgr)

    b = make_bundle("bundle1")
    buffer_mgr.store_bundle(b)

    contacts = [DummyContact("nodeB"), DummyContact("nodeC")]
    sent_to = router.route_bundle(b, contacts, timestamp=time.time())

    assert set(sent_to) == {"nodeB", "nodeC"}


def test_summary_vector_exchange():
    """Test that EpidemicRouter correctly performs anti-entropy vector exchange."""
    buffer_mgr = DummyBufferManager()
    router = EpidemicRouter("nodeA", buffer_mgr)

    b = make_bundle("bundle2")
    buffer_mgr.store_bundle(b)

    contact = DummyContact("nodeB")
    summary = router.exchange_summary_vector(contact.peer_id, contact)

    assert isinstance(summary, dict)
    assert b.id in summary["owned_bundles"]


def test_duplicate_suppression():
    """Test that duplicates are not re-forwarded."""
    buffer_mgr = DummyBufferManager()
    router = EpidemicRouter("nodeA", buffer_mgr)

    b = make_bundle("bundle3")
    buffer_mgr.store_bundle(b)

    contact = DummyContact("nodeB")

    # First send
    router.route_bundle(b, [contact], timestamp=time.time())

    # Second send should detect duplicate
    sent_to = router.route_bundle(b, [contact], timestamp=time.time())
    assert sent_to == []  # duplicate suppression should prevent re-send


def test_transmission_priority():
    """Test prioritization logic during contact-limited transmission."""
    buffer_mgr = DummyBufferManager()
    router = EpidemicRouter("nodeA", buffer_mgr)

    b1 = make_bundle("b1", priority=BundlePriority.CRITICAL, ttl=100)
    b2 = make_bundle("b2", priority=BundlePriority.LOW, ttl=300)
    b3 = make_bundle("b3", priority=BundlePriority.HIGH, ttl=150)

    bundles = [b1, b2, b3]
    ordered = router.calculate_transmission_priority(bundles, contact_duration=10.0)

    priorities = [b.priority for b in ordered]
    assert priorities[0] == BundlePriority.CRITICAL
    assert priorities[-1] == BundlePriority.LOW


if __name__ == "__main__":
    pytest.main(["-v", __file__])
