"""
Satellite Physical Layer (P1-001)

Implements the physical layer abstraction for DTN satellite communication.
Includes link budget calculations, free space path loss, SNR, capacity,
propagation delay, and antenna modeling.

Dependencies:
- ContactWindow, SatelliteNode, GroundStation (higher-level modules)
"""

import math
from typing import Dict


class SatellitePhysicalLayer:
    def __init__(self, frequency_ghz: float = 12.0, bandwidth_mhz: float = 500,
                 noise_temperature_k: float = 150, efficiency_factor: float = 0.7):
        """
        Initialize physical layer parameters.
        """
        self.frequency_ghz = frequency_ghz
        self.bandwidth_hz = bandwidth_mhz * 1e6
        self.noise_temperature_k = noise_temperature_k
        self.efficiency_factor = efficiency_factor
        self.boltzmann_const = 1.38064852e-23  # J/K

    # 1. Free Space Path Loss
    def calculate_free_space_path_loss(self, distance_km: float) -> float:
        """
        FSPL(dB) = 20log10(d) + 20log10(f) + 92.45
        where:
            d = distance (km)
            f = frequency (GHz)
        """
        return 20 * math.log10(distance_km) + 20 * math.log10(self.frequency_ghz) + 92.45

    # 2. Link Budget & SNR
    def estimate_signal_to_noise_ratio(self, tx_power_watts: float,
                                       tx_antenna_gain_db: float,
                                       rx_antenna_gain_db: float,
                                       path_loss_db: float) -> float:
        """
        Estimate SNR (linear).
        """
        eirp_db = 10 * math.log10(tx_power_watts) + tx_antenna_gain_db
        received_power_db = eirp_db - path_loss_db + rx_antenna_gain_db
        noise_power_db = 10 * math.log10(self.boltzmann_const *
                                         self.noise_temperature_k *
                                         self.bandwidth_hz)
        snr_db = received_power_db - noise_power_db
        return 10 ** (snr_db / 10)

    # 3. Link Capacity (Shannon)
    def calculate_link_capacity(self, distance_km: float, tx_power_w: float,
                                tx_gain_db: float, rx_gain_db: float) -> float:
        """
        Shannon capacity with practical margin:
        C = bandwidth * log2(1 + SNR)
        """
        path_loss = self.calculate_free_space_path_loss(distance_km)
        snr = self.estimate_signal_to_noise_ratio(tx_power_w, tx_gain_db,
                                                  rx_gain_db, path_loss)
        return self.bandwidth_hz * math.log2(1 + snr) * self.efficiency_factor

    # 4. Propagation Delay
    def propagation_delay(self, distance_km: float) -> float:
      """
      Delay = distance / c
      Returns milliseconds (ms).
      """
      # distance_km → meters: distance_km * 1000
      # Speed of light c = 299,792,458 m/s
      delay_sec = (distance_km * 1000) / 299_792_458
      delay_ms = delay_sec * 1000.0
      return delay_ms


    # 5. Bit Error Rate (simplified QPSK model)
    def calculate_bit_error_rate(self, snr_linear: float,
                                 modulation_type: str = "QPSK") -> float:
        """
        Approximate BER for common modulation.
        """
        if modulation_type.upper() == "QPSK":
            return 0.5 * math.erfc(math.sqrt(snr_linear))
        return 0.5 * math.erfc(math.sqrt(snr_linear))  # fallback

    # 6. Transmission Time Estimate
    def estimate_transmission_time(self, bundle_size_bytes: int,
                                   link_capacity_bps: float,
                                   contact_duration_sec: float) -> float:
        """
        Estimate time to transmit a bundle given capacity and contact duration.
        Returns required time in seconds, or inf if not feasible.
        """
        transmission_time = (bundle_size_bytes * 8) / link_capacity_bps
        if transmission_time > contact_duration_sec:
            return float("inf")
        return transmission_time

    # 7. Antenna Pointing (simplified model)
    def model_antenna_pointing(self, pointing_error_deg: float = 0.1) -> float:
        """
        Estimate pointing loss in dB from misalignment.
        """
        return -0.5 * pointing_error_deg  # dB loss approx.


__all__ = ["SatellitePhysicalLayer"]

