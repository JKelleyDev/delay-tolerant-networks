# src/satellite_physical_layer.py

import math


class SatellitePhysicalLayer:
    def __init__(
        self, frequency_ghz: float, bandwidth_mhz: float, noise_temp_k: float = 290.0
    ):
        self.frequency_ghz = frequency_ghz
        self.bandwidth_mhz = bandwidth_mhz
        self.noise_temp_k = noise_temp_k

    def calculate_free_space_path_loss(self, distance_km: float) -> float:
        """Return FSPL in dB."""
        freq_hz = self.frequency_ghz * 1e9
        d_m = distance_km * 1000
        return 20 * math.log10(d_m) + 20 * math.log10(freq_hz) - 147.55

    def calculate_link_capacity(
        self, satellite_range_km: float, snr_db: float
    ) -> float:
        """Return link capacity in bits/s using Shannon capacity."""
        snr_linear = 10 ** (snr_db / 10.0)
        bw_hz = self.bandwidth_mhz * 1e6
        return bw_hz * math.log2(1 + snr_linear)

    def estimate_signal_to_noise_ratio(
        self,
        tx_power_watts,
        tx_antenna_gain_db,
        rx_antenna_gain_db,
        path_loss_db,
        noise_temperature_k,
    ):
        """Estimate SNR at receiver in dB."""
        k = 1.38e-23  # Boltzmann constant
        bw_hz = self.bandwidth_mhz * 1e6
        noise_power_w = k * noise_temperature_k * bw_hz
        tx_power_dbw = 10 * math.log10(tx_power_watts)
        received_power_dbw = (
            tx_power_dbw + tx_antenna_gain_db + rx_antenna_gain_db - path_loss_db
        )
        snr_linear = 10 ** (received_power_dbw / 10) / noise_power_w
        return 10 * math.log10(snr_linear)

    def calculate_bit_error_rate(
        self, snr_db: float, modulation_type: str = "QPSK"
    ) -> float:
        """Approximate BER given modulation type."""
        from math import erfc, sqrt

        snr_linear = 10 ** (snr_db / 10.0)
        if modulation_type.upper() == "QPSK":
            return 0.5 * erfc(sqrt(snr_linear))
        elif modulation_type.upper() == "BPSK":
            return 0.5 * erfc(sqrt(2 * snr_linear))
        else:
            return 1.0  # unknown modulation → assume terrible BER

    def estimate_transmission_time(
        self,
        bundle_size_bytes: int,
        link_capacity_bps: float,
        contact_duration_sec: float,
    ) -> float:
        """Estimate how long it takes to send the bundle; return inf if not possible."""
        if link_capacity_bps <= 0:
            return float("inf")
        time_sec = (bundle_size_bytes * 8) / link_capacity_bps
        return time_sec if time_sec <= contact_duration_sec else float("inf")

    def estimate_doppler_shift(
        self, relative_velocity_mps: float, carrier_frequency_hz: float
    ) -> float:
        """Return Doppler frequency shift in Hz."""
        c = 3e8
        return (relative_velocity_mps / c) * carrier_frequency_hz
