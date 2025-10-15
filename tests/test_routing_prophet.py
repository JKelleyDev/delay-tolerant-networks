
import time
from src.routing_prophet import PROPHETRouter
from src.bundle import Bundle, BundlePriority


# Helper buffer manager
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


def make_bundle(bundle_id: str, dest="B"):
    b = Bundle(
        source="A",
        destination=dest,
        payload=f"payload".encode(),
        ttl_seconds=300,
        priority=BundlePriority.NORMAL,
        creation_time=time.time(),
    )
    b.id = bundle_id
    return b


def test_prophet_direct_encounter():
    bm = DummyBufferManager()
    router = PROPHETRouter("A", bm, p_encounter_max=0.6)
    assert router.get_predictability("B") == 0.0
    router.update_delivery_predictability("B")
    p = router.get_predictability("B")
    assert 0.0 < p <= 1.0
    # second encounter increases (monotonic)
    prev = p
    router.update_delivery_predictability("B")
    assert router.get_predictability("B") >= prev


def test_prophet_aging():
    bm = DummyBufferManager()
    router = PROPHETRouter("A", bm, gamma=0.5)
    router.delivery_predictability["B"] = 0.8
    router.age_delivery_predictabilities(time_elapsed_seconds=1.0)  # apply gamma^1
    assert router.get_predictability("B") < 0.8


def test_prophet_transitivity():
    bm = DummyBufferManager()
    router = PROPHETRouter("A", bm, beta=0.5)
    # set P(a,b)
    router.delivery_predictability["B"] = 0.6
    # B's predictabilities (peer table)
    his_table = {"C": 0.7}
    router.transitivity_update("B", his_table)
    # Now P(a,C) should have increased above 0
    assert router.get_predictability("C") > 0.0


def test_prophet_routing_decision_and_bounds():
    bm = DummyBufferManager()
    router = PROPHETRouter("A", bm, p_encounter_max=0.7, gamma=0.99, beta=0.25, delta=0.01)
    # make router have meetings with B and C; B more frequent
    router.delivery_predictability["B"] = 0.6
    router.delivery_predictability["C"] = 0.02
    # create bundle destined to something (dest ignored for utility in this simple test)
    b = make_bundle("bundle1", dest="Z")
    contacts = [DummyContact("B"), DummyContact("C")]
    chosen = router.route_bundle(b, contacts, timestamp=time.time())
    assert isinstance(chosen, list)
    # should choose B (higher P)
    assert chosen and chosen[0] == "B"
    # all probabilities within [0,1]
    for v in router.delivery_predictability.values():
        assert 0.0 <= v <= 1.0
