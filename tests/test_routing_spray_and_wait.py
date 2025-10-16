import time
from src.routing_spray_and_wait import SprayAndWaitRouter
from src.bundle import Bundle, BundlePriority


class DummyBufferManager:
    def __init__(self):
        self._bundles = {}

    def store_bundle(self, bundle: Bundle):
        self._bundles[bundle.id] = bundle

    def get_all_bundles(self):
        return list(self._bundles.values())


class DummyContact:
    def __init__(self, peer_id: str):
        self.peer_id = peer_id
        self.duration = 60.0


def make_bundle(bundle_id: str, dest="dest"):
    b = Bundle(
        source="self",
        destination=dest,
        payload=b"p",
        ttl_seconds=300,
        priority=BundlePriority.NORMAL,
        creation_time=time.time(),
    )
    b.id = bundle_id
    return b


def test_spray_phase_copy_distribution_binary():
    bm = DummyBufferManager()
    router = SprayAndWaitRouter("A", bm, initial_copies=10, spray_threshold=1)
    b = make_bundle("b1", dest="D")
    bm.store_bundle(b)
    # start spraying
    contacts = [DummyContact("B"), DummyContact("C")]
    peers = router.route_bundle(b, contacts, timestamp=time.time())
    # binary strategy gives half to first peer: 10 -> give 5 to first peer
    remaining = router.get_remaining_copies(b.id)
    assert remaining == 5
    assert peers == ["B"]


def test_wait_phase_destination_only():
    bm = DummyBufferManager()
    router = SprayAndWaitRouter("A", bm, initial_copies=2, spray_threshold=1)
    b = make_bundle("b2", dest="DEST")
    bm.store_bundle(b)
    # first spray: initial copies 2 -> binary gives 1 to first peer (if present)
    contacts1 = [DummyContact("X")]
    router.route_bundle(b, contacts1, timestamp=time.time())
    # now remaining should be 1 -> wait phase
    contacts2 = [DummyContact("DEST"), DummyContact("Y")]
    forwarded = router.route_bundle(b, contacts2, timestamp=time.time())
    assert forwarded == ["DEST"]
    assert router.get_remaining_copies(b.id) == 0


def test_binary_spray_division():
    bm = DummyBufferManager()
    router = SprayAndWaitRouter("A", bm, initial_copies=9, spray_threshold=1)
    b = make_bundle("b3", dest="Z")
    bm.store_bundle(b)
    # first spray: 9 -> give floor(9/2) = 4 to first peer -> remaining 5
    contacts = [DummyContact("P")]
    peers = router.route_bundle(b, contacts, timestamp=time.time())
    assert peers == ["P"]
    assert router.get_remaining_copies(b.id) == 5


def test_copy_counter_management_and_phase_transition():
    bm = DummyBufferManager()
    router = SprayAndWaitRouter("A", bm, initial_copies=4, spray_threshold=1)
    b = make_bundle("b4", dest="D")
    bm.store_bundle(b)
    # spray 1: 4 -> give 2 to first peer -> remaining 2
    router.route_bundle(b, [DummyContact("N1")], timestamp=time.time())
    assert router.get_remaining_copies(b.id) == 2
    # spray 2: 2 -> give 1 to next peer -> remaining 1 (now wait phase)
    router.route_bundle(b, [DummyContact("N2")], timestamp=time.time())
    assert router.get_remaining_copies(b.id) == 1
    # wait phase: meet destination
    forwarded = router.route_bundle(b, [DummyContact("D")], timestamp=time.time())
    assert forwarded == ["D"]
    assert router.get_remaining_copies(b.id) == 0
