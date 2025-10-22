import time
from src.routing_epidemic import EpidemicRouter
from src.bundle import Bundle, BundlePriority


class DummyBufferManager:
    def __init__(self):
        self.bundles = []

    def store_bundle(self, bundle):
        self.bundles.append(bundle)


class DummyContact:
    def __init__(self, peer_id):
        self.peer_id = peer_id
        self.received = []

    def receive_bundle(self, bundle):
        self.received.append(bundle)


def make_bundle(bundle_id: str, priority=BundlePriority.NORMAL, ttl=300):
    """Helper to create a simple Bundle compatible with your group's Bundle class."""
    b = Bundle(
        source="A",
        destination="B",
        payload=f"Payload for {bundle_id}".encode("utf-8"),
        ttl_seconds=ttl,
        priority=priority,
        creation_time=time.time(),
    )
    b.id = bundle_id
    return b


def test_epidemic_basic_flooding():
    buffer_mgr = DummyBufferManager()
    router = EpidemicRouter("nodeA", buffer_mgr)

    b = make_bundle("bundle1")
    buffer_mgr.store_bundle(b)
    contacts = [DummyContact("nodeB"), DummyContact("nodeC")]

    sent_to = router.route_bundle(b, contacts)
    assert "nodeB" in sent_to and "nodeC" in sent_to
    assert b.id in router.seen_bundles


def test_summary_vector_exchange():
    buffer_mgr = DummyBufferManager()
    router = EpidemicRouter("nodeA", buffer_mgr)

    b = make_bundle("bundle2")
    buffer_mgr.store_bundle(b)

    contact = DummyContact("nodeB")
    summary = router.exchange_summary_vector(contact.peer_id, contact)

    assert isinstance(summary, dict)
    assert b.id in summary["owned_bundles"]


def test_duplicate_suppression():
    buffer_mgr = DummyBufferManager()
    router = EpidemicRouter("nodeA", buffer_mgr)

    b = make_bundle("bundle3")
    buffer_mgr.store_bundle(b)
    contacts = [DummyContact("nodeB")]

    router.route_bundle(b, contacts)
    second_try = router.route_bundle(b, contacts)
    assert second_try == []  # no re-forwarding


def test_transmission_priority():
    buffer_mgr = DummyBufferManager()
    router = EpidemicRouter("nodeA", buffer_mgr)

    b1 = make_bundle("b1", priority=BundlePriority.CRITICAL, ttl=100)
    b2 = make_bundle("b2", priority=BundlePriority.NORMAL, ttl=300)

    p1 = router.calculate_transmission_priority(b1)
    p2 = router.calculate_transmission_priority(b2)

    assert p1 > p2
