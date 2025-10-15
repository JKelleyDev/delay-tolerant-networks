import time
from src.routing_prophet import PROPHETRouter
from src.bundle import Bundle


class DummyBufferManager:
    def store_bundle(self, b): pass


class DummyContact:
    def __init__(self, peer_id):
        self.peer_id = peer_id


def make_bundle(dest="B"):
    return Bundle(source="A", destination=dest, payload=b"data", ttl_seconds=300)


def test_prophet_direct_encounter():
    router = PROPHETRouter("nodeA", DummyBufferManager())
    router.update_delivery_predictability("nodeB")
    assert 0 < router.get_predictability("nodeB") <= 1


def test_prophet_aging():
    router = PROPHETRouter("nodeA", DummyBufferManager())
    router.update_delivery_predictability("nodeB")
    old_p = router.get_predictability("nodeB")
    time.sleep(0.1)
    router.age_delivery_predictabilities()
    new_p = router.get_predictability("nodeB")
    assert new_p <= old_p


def test_prophet_transitivity():
    router = PROPHETRouter("nodeA", DummyBufferManager())
    router.update_delivery_predictability("nodeB")
    peer_table = {"nodeC": 0.8}
    router.transitivity_update("nodeB", peer_table)
    assert router.get_predictability("nodeC") > 0


def test_prophet_routing_decision():
    router = PROPHETRouter("nodeA", DummyBufferManager())
    bundle = make_bundle("nodeC")
    router.delivery_predictability = {"nodeB": 0.5, "nodeC": 0.9}
    contacts = [DummyContact("nodeB"), DummyContact("nodeC")]
    next_hops = router.route_bundle(bundle, contacts, time.time())
    assert next_hops == ["nodeC"]


def test_prophet_probability_bounds():
    router = PROPHETRouter("nodeA", DummyBufferManager())
    router.delivery_predictability["nodeB"] = 1.5
    router.age_delivery_predictabilities()
    assert 0 <= router.get_predictability("nodeB") <= 1
