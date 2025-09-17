import unittest
import time
import sys
import os

# Add the src directory to the path so we can import the bundle module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bundle import Bundle, BundlePriority


class TestBundle(unittest.TestCase):

    def setUp(self):
        self.test_payload = b"Hello, satellite network!"
        self.test_source = "satellite_1"
        self.test_destination = "ground_station_1"
        self.test_ttl = 3600  # 1 hour

    def test_bundle_creation(self):
        bundle = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
        )

        self.assertEqual(bundle.source, self.test_source)
        self.assertEqual(bundle.destination, self.test_destination)
        self.assertEqual(bundle.payload, self.test_payload)
        self.assertEqual(bundle.ttl_seconds, self.test_ttl)
        self.assertIsNotNone(bundle.id)
        self.assertIsNotNone(bundle.timestamp)
        self.assertIsNotNone(bundle.sequence)
        self.assertIsNotNone(bundle.creation_time)
        self.assertEqual(bundle.priority, BundlePriority.NORMAL)
        self.assertTrue(bundle.store_and_forward)

    def test_bundle_id_generation(self):
        bundle1 = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
        )

        time.sleep(0.001)  # Ensure different timestamp

        bundle2 = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
        )

        self.assertNotEqual(bundle1.id, bundle2.id)
        self.assertEqual(len(bundle1.id), 16)  # SHA256 truncated to 16 chars

    def test_bundle_id_consistency(self):
        bundle = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
        )

        expected_id = bundle._generate_id()
        self.assertEqual(bundle.id, expected_id)

    def test_ttl_countdown_and_expiration(self):
        short_ttl = 2  # 2 seconds to avoid timing issues
        bundle = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=short_ttl,
        )

        self.assertFalse(bundle.is_expired())
        self.assertGreaterEqual(bundle.remaining_ttl(), 1)

        time.sleep(2.1)  # Wait for expiration

        self.assertTrue(bundle.is_expired())
        self.assertEqual(bundle.remaining_ttl(), 0)

    def test_bundle_validation(self):
        valid_bundle = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
        )
        self.assertTrue(valid_bundle.validate())

        # Test empty source
        invalid_bundle = Bundle(
            source="",
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
        )
        self.assertFalse(invalid_bundle.validate())

        # Test empty destination
        invalid_bundle = Bundle(
            source=self.test_source,
            destination="",
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
        )
        self.assertFalse(invalid_bundle.validate())

        # Test zero TTL
        invalid_bundle = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=0,
        )
        self.assertFalse(invalid_bundle.validate())

        # Test empty payload
        invalid_bundle = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=b"",
            ttl_seconds=self.test_ttl,
        )
        self.assertFalse(invalid_bundle.validate())

    def test_serialization_deserialization(self):
        original_bundle = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
            priority=BundlePriority.HIGH,
            store_and_forward=False,
        )

        # Serialize
        serialized_data = original_bundle.serialize()
        self.assertIsInstance(serialized_data, bytes)

        # Deserialize
        deserialized_bundle = Bundle.deserialize(serialized_data)

        # Verify all fields match
        self.assertEqual(deserialized_bundle.id, original_bundle.id)
        self.assertEqual(deserialized_bundle.source, original_bundle.source)
        self.assertEqual(deserialized_bundle.destination, original_bundle.destination)
        self.assertEqual(deserialized_bundle.payload, original_bundle.payload)
        self.assertEqual(deserialized_bundle.ttl_seconds, original_bundle.ttl_seconds)
        self.assertEqual(deserialized_bundle.priority, original_bundle.priority)
        self.assertEqual(
            deserialized_bundle.store_and_forward, original_bundle.store_and_forward
        )
        self.assertEqual(deserialized_bundle.timestamp, original_bundle.timestamp)
        self.assertEqual(deserialized_bundle.sequence, original_bundle.sequence)
        self.assertEqual(
            deserialized_bundle.creation_time, original_bundle.creation_time
        )

    def test_to_dict_from_dict(self):
        original_bundle = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
            priority=BundlePriority.CRITICAL,
        )

        # Convert to dict
        bundle_dict = original_bundle.to_dict()
        self.assertIsInstance(bundle_dict, dict)
        self.assertIn("id", bundle_dict)
        self.assertIn("source", bundle_dict)
        self.assertIn("destination", bundle_dict)
        self.assertIn("payload", bundle_dict)

        # Convert back from dict
        reconstructed_bundle = Bundle.from_dict(bundle_dict)
        self.assertEqual(reconstructed_bundle.id, original_bundle.id)
        self.assertEqual(reconstructed_bundle.source, original_bundle.source)
        self.assertEqual(reconstructed_bundle.destination, original_bundle.destination)
        self.assertEqual(reconstructed_bundle.payload, original_bundle.payload)
        self.assertEqual(reconstructed_bundle.priority, original_bundle.priority)

    def test_satellite_specific_features(self):
        # Test priority levels
        low_priority = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
            priority=BundlePriority.LOW,
        )
        self.assertEqual(low_priority.priority, BundlePriority.LOW)

        critical_priority = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
            priority=BundlePriority.CRITICAL,
        )
        self.assertEqual(critical_priority.priority, BundlePriority.CRITICAL)

        # Test store-and-forward flag
        no_store_forward = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
            store_and_forward=False,
        )
        self.assertFalse(no_store_forward.store_and_forward)

    def test_long_delay_tolerance(self):
        # Test with satellite orbital period TTLs (hours/days)
        orbital_period_ttl = 24 * 60 * 60  # 24 hours
        long_delay_bundle = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=orbital_period_ttl,
        )

        self.assertEqual(long_delay_bundle.ttl_seconds, orbital_period_ttl)
        self.assertFalse(long_delay_bundle.is_expired())
        self.assertGreater(long_delay_bundle.remaining_ttl(), 0)

    def test_sequence_generation(self):
        bundle1 = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
        )

        time.sleep(0.001)

        bundle2 = Bundle(
            source=self.test_source,
            destination=self.test_destination,
            payload=self.test_payload,
            ttl_seconds=self.test_ttl,
        )

        self.assertNotEqual(bundle1.sequence, bundle2.sequence)
        self.assertIsInstance(bundle1.sequence, int)
        self.assertIsInstance(bundle2.sequence, int)


if __name__ == "__main__":
    unittest.main()
