# tests/test_satellite_physical_layer.py
import sys
import pathlib
import math
import pytest

# Ensure tests can import the module from src/
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from satellite_physical_layer import SatellitePhysicalLayer

@pytest.fixture
def phy():
    # default Ka-band-ish example
    return SatellitePhysicalLayer(frequency_ghz=12.0, bandwidth_mhz=500)

def test_fspl_is_positive(phy):
    # FSPL should be a positive dB value for Earth-space distances
    fspl = phy.calculate_free_space_path_loss(1000.0)  # 1000 km
    assert fspl > 0.0
    # check growth: farther distance -> larger FSPL
    fspl_far = phy.calculate_free_space_path_loss(40000.0)
    assert fspl_far > fspl

def test_link_capacity_scaling_with_snr(phy):
    # capacity increases with SNR
    cap_low = phy.calculate_link_capacity(satellite_range_km=1000.0, snr_db=0.0)
    cap_high = phy.calculate_link_capacity(satellite_range_km=1000.0, snr_db=20.0)
    assert cap_high > cap_low
    assert cap_low >= 0

def test_snr_computation_reasonable(phy):
    # Provide a toy link budget: small tx power, small gains -> small SNR
    snr_db = phy.estimate_signal_to_noise_ratio(
        tx_power_watts=5.0,  # 5 W
        tx_antenna_gain_db=30.0,  # modest dish
        rx_antenna_gain_db=30.0,
        path_loss_db=phy.calculate_free_space_path_loss(1000.0),
        noise_temperature_k=200.0
    )
    # SNR could be negative or positive depending on numbers, but should be finite
    assert math.isfinite(snr_db)

def test_ber_qpsk_bounds(phy):
    # For a reasonable SNR, BER should be in (0,1)
    snr_db = 10.0
    ber = phy.calculate_bit_error_rate(snr_db, modulation_type="QPSK")
    assert 0.0 <= ber < 1.0

def test_transmission_time_and_fit(phy):
    # small bundle should fit in a long contact
    bundle_bytes = 200 * 1024  # 200 KB
    # assume moderate SNR -> compute capacity
    snr_db = 15.0
    cap_bps = phy.calculate_link_capacity(satellite_range_km=1000.0, snr_db=snr_db)
    tx_time = phy.estimate_transmission_time(bundle_bytes, cap_bps, contact_duration_sec=3600.0)
    assert tx_time > 0.0 and tx_time != float("inf")
    # very small capacity should not fit -> returns inf
    tx_time_impossible = phy.estimate_transmission_time(bundle_bytes, link_capacity_bps=1.0, contact_duration_sec=10.0)
    assert tx_time_impossible == float("inf")

def test_doppler_shift(phy):
    # small velocity results in small doppler shift
    carrier = phy.frequency_ghz * 1e9
    shift = phy.estimate_doppler_shift(relative_velocity_mps=1000.0, carrier_frequency_hz=carrier)
    assert abs(shift) < carrier * 1e-3  # small fraction of carrier

