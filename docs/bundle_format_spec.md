# DTN Bundle Format Specification

## Overview

This document specifies the bundle data structure and format for Delay-Tolerant Network (DTN) message handling in satellite communication networks.

## Bundle Structure

### Core Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `id` | string | Unique bundle identifier (16-char SHA256 hash) | Yes |
| `source` | string | Source node identifier | Yes |
| `destination` | string | Destination node identifier | Yes |
| `payload` | bytes | Message data | Yes |
| `ttl_seconds` | int | Time-to-live in seconds | Yes |
| `timestamp` | float | Creation timestamp (Unix epoch) | Yes |
| `sequence` | int | Sequence number for ID generation | Yes |
| `creation_time` | float | Bundle creation time (Unix epoch) | Yes |
| `priority` | BundlePriority | Message priority level | Yes |
| `store_and_forward` | bool | Store-and-forward optimization flag | Yes |

### Bundle Priority Levels

```python
class BundlePriority(Enum):
    LOW = 1      # Background data, telemetry
    NORMAL = 2   # Regular communications
    HIGH = 3     # Important operational data
    CRITICAL = 4 # Emergency communications
```

## Bundle ID Generation

Bundle IDs are generated using the following scheme:

1. Create ID string: `{source}:{timestamp}:{sequence}`
2. Generate SHA256 hash of the ID string
3. Truncate to first 16 characters

Example:
```python
id_string = "satellite_1:1695824400.123456:789012"
bundle_id = hashlib.sha256(id_string.encode()).hexdigest()[:16]
# Result: "a1b2c3d4e5f67890"
```

## Time-to-Live (TTL) Management

### TTL Countdown
- TTL is specified in seconds
- Countdown begins at bundle creation time
- Remaining TTL = `ttl_seconds - (current_time - creation_time)`

### Expiration Checking
```python
def is_expired(self) -> bool:
    current_time = time.time()
    return (current_time - self.creation_time) > self.ttl_seconds
```

### Satellite-Specific TTL Considerations
- **Orbital Period TTLs**: Support TTL values of hours to days for satellite orbital periods
- **Long Delay Tolerance**: Handle communication delays up to several hours
- **Contact Window Optimization**: TTL should accommodate limited satellite contact windows

## Serialization Format

### JSON Serialization
Bundles are serialized to JSON format for network transmission:

```json
{
  "id": "a1b2c3d4e5f67890",
  "source": "satellite_1",
  "destination": "ground_station_1",
  "payload": "48656c6c6f2c20736174656c6c697465206e6574776f726b21",
  "ttl_seconds": 86400,
  "priority": 2,
  "store_and_forward": true,
  "timestamp": 1695824400.123456,
  "sequence": 789012,
  "creation_time": 1695824400.123456
}
```

### Binary Encoding
- JSON is UTF-8 encoded to bytes for transmission
- Payload is hex-encoded in JSON format
- Deserialization converts hex back to bytes

## Validation Rules

### Required Field Validation
1. `source` must not be empty
2. `destination` must not be empty
3. `payload` must not be empty
4. `ttl_seconds` must be greater than 0

### Expiration Validation
- Bundles failing `is_expired()` check are invalid
- Validation must occur before processing

### Example Validation
```python
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
```

## Satellite-Specific Features

### Store-and-Forward Optimization
- `store_and_forward` flag indicates bundle eligibility for intermediate storage
- Critical for satellite networks with intermittent connectivity
- Default: `True`

### Priority Handling
- Higher priority bundles should be processed first during limited contact windows
- Priority affects routing and storage decisions
- Emergency communications use `CRITICAL` priority

### Long-Delay Considerations
- Bundle structure accommodates multi-hour delays
- TTL values support orbital periods (typically 90-120 minutes)
- Sequence numbers prevent ID collisions across orbital periods

## API Usage Examples

### Bundle Creation
```python
# Basic bundle
bundle = Bundle(
    source="satellite_1",
    destination="ground_station_1",
    payload=b"Hello, satellite network!",
    ttl_seconds=3600  # 1 hour
)

# High-priority bundle with custom settings
priority_bundle = Bundle(
    source="satellite_1",
    destination="ground_station_1",
    payload=b"Emergency data",
    ttl_seconds=86400,  # 24 hours
    priority=BundlePriority.CRITICAL,
    store_and_forward=False
)
```

### Serialization/Deserialization
```python
# Serialize for transmission
serialized = bundle.serialize()

# Deserialize received data
received_bundle = Bundle.deserialize(serialized)
```

### TTL Management
```python
# Check expiration
if bundle.is_expired():
    print("Bundle expired, discarding")

# Get remaining TTL
remaining = bundle.remaining_ttl()
print(f"Bundle expires in {remaining} seconds")
```

## Implementation Notes

- All timestamps use Unix epoch (seconds since 1970-01-01 UTC)
- Sequence numbers are microsecond-based to ensure uniqueness
- Bundle IDs are deterministic based on source, timestamp, and sequence
- Validation should be performed before bundle processing or forwarding
- Priority and store-and-forward flags optimize satellite network performance

## Future Extensions

This format is designed to be extensible for future DTN protocol enhancements:
- Additional routing metadata
- Encryption and authentication fields
- Quality of Service (QoS) parameters
- Network topology awareness