import math
import pytest
from src.satellite_physical_layer import SatellitePhysicalLayer


def test_fspl_calculation():
    phy = SatellitePhysicalLayer(frequency_ghz=12.0)
    fspl = phy.calculate_free_space_path_loss(550)  # 550 km (LEO)
    assert fspl > 150  # dB scale
    assert isinstance(fspl, float)


def test_snr_and_capacity():
    phy = SatellitePhysicalLayer(frequency_ghz=12.0, bandwidth_mhz=500)
    fspl = phy.calculate_free_space_path_loss(550)
    snr = phy.estimate_signal_to_noise_ratio(20, 30, 30, fspl)  # 20W, 30dB gains
    capacity = phy.calculate_link_capacity(550, 20, 30, 30)
    assert snr > 0
    assert capacity > 1e6  # at least 1 Mbps


def test_propagation_delay():
    phy = SatellitePhysicalLayer()
    delay_ms = phy.propagation_delay(550)  # in ms now
    # For 550 km, expect ~1.83 ms, so test range maybe 0.5 ms to 10 ms
    assert 0.5 < delay_ms < 10.0


def test_ber_qpsk():
    phy = SatellitePhysicalLayer()
    ber = phy.calculate_bit_error_rate(10)  # high SNR → low BER
    assert 0 <= ber < 0.1


def test_transmission_time_within_contact():
    phy = SatellitePhysicalLayer()
    capacity = phy.calculate_link_capacity(550, 20, 30, 30)
    time_sec = phy.estimate_transmission_time(1_000_000, capacity, 60)  # 1 MB bundle
    assert time_sec < 60


def test_transmission_time_exceeds_contact():
    phy = SatellitePhysicalLayer()
    capacity = 1e5  # 100 kbps
    time_sec = phy.estimate_transmission_time(10_000_000, capacity, 30)  # 10 MB bundle
    assert time_sec == float("inf")
