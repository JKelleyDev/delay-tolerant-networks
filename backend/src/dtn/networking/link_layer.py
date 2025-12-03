"""
Link Layer Implementation for Satellite DTN

Implements ARQ (Automatic Repeat Request) protocols with BER-driven errors
and finite link buffers for realistic satellite communication modeling.
"""

import math
import random
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum

from ..core.bundle import Bundle

logger = logging.getLogger(__name__)


class ARQProtocol(Enum):
    """ARQ protocol types."""
    STOP_AND_WAIT = "stop_and_wait"
    SLIDING_WINDOW = "sliding_window"


class TransmissionState(Enum):
    """Transmission states for ARQ."""
    IDLE = "idle"
    TRANSMITTING = "transmitting"
    WAITING_ACK = "waiting_ack"
    RETRANSMITTING = "retransmitting"


@dataclass
class LinkParameters:
    """Physical link parameters."""
    frequency_ghz: float = 14.0  # Ka-band uplink
    bandwidth_mhz: float = 500.0
    transmit_power_dbm: float = 50.0
    antenna_gain_db: float = 45.0
    noise_temperature_k: float = 290.0
    
    # ARQ parameters
    arq_protocol: ARQProtocol = ARQProtocol.STOP_AND_WAIT
    window_size: int = 4  # For sliding window
    max_retransmissions: int = 5
    timeout_seconds: float = 2.0
    
    # Buffer parameters
    transmit_buffer_size: int = 1024 * 1024  # 1MB
    receive_buffer_size: int = 1024 * 1024   # 1MB


@dataclass
class LinkQuality:
    """Current link quality metrics."""
    distance_km: float
    signal_to_noise_ratio_db: float
    bit_error_rate: float
    packet_error_rate: float
    atmospheric_loss_db: float = 0.0
    rain_attenuation_db: float = 0.0
    
    @property
    def total_loss_db(self) -> float:
        """Total path loss including atmospheric effects."""
        # Free space path loss
        fspl_db = 32.45 + 20 * math.log10(self.distance_km) + 20 * math.log10(self.frequency_ghz)
        return fspl_db + self.atmospheric_loss_db + self.rain_attenuation_db


@dataclass
class Packet:
    """Network packet with error control."""
    packet_id: str
    bundle_id: str
    sequence_number: int
    data: bytes
    checksum: int
    timestamp: datetime
    retransmission_count: int = 0
    
    @property
    def size_bytes(self) -> int:
        return len(self.data) + 20  # Add header overhead


class ARQTransmitter:
    """ARQ transmitter with error handling."""
    
    def __init__(self, link_params: LinkParameters):
        self.params = link_params
        self.state = TransmissionState.IDLE
        self.transmit_buffer: List[Packet] = []
        self.send_window: Dict[int, Packet] = {}  # seq_num -> packet
        self.next_seq_num = 0
        self.window_base = 0
        self.last_ack_time = datetime.now()
        self.retransmission_timer = None
        
        # Statistics
        self.packets_sent = 0
        self.packets_retransmitted = 0
        self.packets_dropped = 0
        self.total_bytes_sent = 0
    
    def queue_bundle(self, bundle: Bundle) -> bool:
        """Queue a bundle for transmission."""
        # Fragment bundle into packets if needed
        max_packet_size = 1400  # MTU consideration
        bundle_data = bundle.payload
        
        if len(bundle_data) <= max_packet_size:
            # Single packet
            packet = Packet(
                packet_id=f"{bundle.bundle_id}_0",
                bundle_id=bundle.bundle_id,
                sequence_number=self.next_seq_num,
                data=bundle_data,
                checksum=self._calculate_checksum(bundle_data),
                timestamp=datetime.now()
            )
            
            if self._can_buffer_packet(packet):
                self.transmit_buffer.append(packet)
                self.next_seq_num += 1
                return True
            else:
                logger.warning(f"Transmit buffer full, dropping bundle {bundle.bundle_id}")
                self.packets_dropped += 1
                return False
        else:
            # Fragment bundle into multiple packets
            fragments_queued = 0
            for i in range(0, len(bundle_data), max_packet_size):
                fragment_data = bundle_data[i:i + max_packet_size]
                packet = Packet(
                    packet_id=f"{bundle.bundle_id}_{i // max_packet_size}",
                    bundle_id=bundle.bundle_id,
                    sequence_number=self.next_seq_num,
                    data=fragment_data,
                    checksum=self._calculate_checksum(fragment_data),
                    timestamp=datetime.now()
                )
                
                if self._can_buffer_packet(packet):
                    self.transmit_buffer.append(packet)
                    self.next_seq_num += 1
                    fragments_queued += 1
                else:
                    logger.warning(f"Buffer full during fragmentation of {bundle.bundle_id}")
                    break
            
            return fragments_queued > 0
    
    def transmit_packets(self, link_quality: LinkQuality, current_time: datetime) -> List[Tuple[Packet, bool]]:
        """Transmit packets according to ARQ protocol."""
        transmitted = []
        
        if self.params.arq_protocol == ARQProtocol.STOP_AND_WAIT:
            transmitted.extend(self._stop_and_wait_transmit(link_quality, current_time))
        else:
            transmitted.extend(self._sliding_window_transmit(link_quality, current_time))
        
        return transmitted
    
    def _stop_and_wait_transmit(self, link_quality: LinkQuality, current_time: datetime) -> List[Tuple[Packet, bool]]:
        """Stop-and-wait ARQ implementation."""
        transmitted = []
        
        if self.state == TransmissionState.IDLE and self.transmit_buffer:
            # Start transmitting next packet
            packet = self.transmit_buffer.pop(0)
            self.send_window[packet.sequence_number] = packet
            success = self._transmit_packet(packet, link_quality)
            
            transmitted.append((packet, success))
            
            if success:
                self.state = TransmissionState.WAITING_ACK
                self.last_ack_time = current_time
            else:
                # Packet corrupted, schedule retransmission
                self.state = TransmissionState.RETRANSMITTING
                
        elif self.state == TransmissionState.WAITING_ACK:
            # Check for timeout
            if (current_time - self.last_ack_time).total_seconds() > self.params.timeout_seconds:
                # Timeout, retransmit
                self.state = TransmissionState.RETRANSMITTING
                
        elif self.state == TransmissionState.RETRANSMITTING:
            # Retransmit the packet
            if self.send_window:
                packet = list(self.send_window.values())[0]
                packet.retransmission_count += 1
                
                if packet.retransmission_count <= self.params.max_retransmissions:
                    success = self._transmit_packet(packet, link_quality)
                    transmitted.append((packet, success))
                    
                    if success:
                        self.state = TransmissionState.WAITING_ACK
                        self.last_ack_time = current_time
                    # else: stay in retransmitting state for next attempt
                else:
                    # Max retransmissions exceeded, drop packet
                    logger.warning(f"Dropping packet {packet.packet_id} after {packet.retransmission_count} retransmissions")
                    self.send_window.clear()
                    self.packets_dropped += 1
                    self.state = TransmissionState.IDLE
        
        return transmitted
    
    def _sliding_window_transmit(self, link_quality: LinkQuality, current_time: datetime) -> List[Tuple[Packet, bool]]:
        """Sliding window ARQ implementation."""
        transmitted = []
        
        # Send new packets if window has space
        while (len(self.send_window) < self.params.window_size and 
               self.transmit_buffer):
            packet = self.transmit_buffer.pop(0)
            success = self._transmit_packet(packet, link_quality)
            transmitted.append((packet, success))
            
            if success:
                self.send_window[packet.sequence_number] = packet
            else:
                # Schedule for retransmission
                packet.retransmission_count += 1
                if packet.retransmission_count <= self.params.max_retransmissions:
                    self.transmit_buffer.insert(0, packet)  # Retry soon
                else:
                    self.packets_dropped += 1
        
        # Check for timeouts and retransmissions
        timed_out_packets = []
        for seq_num, packet in self.send_window.items():
            if (current_time - packet.timestamp).total_seconds() > self.params.timeout_seconds:
                timed_out_packets.append(seq_num)
        
        for seq_num in timed_out_packets:
            packet = self.send_window[seq_num]
            packet.retransmission_count += 1
            
            if packet.retransmission_count <= self.params.max_retransmissions:
                success = self._transmit_packet(packet, link_quality)
                transmitted.append((packet, success))
                packet.timestamp = current_time  # Reset timeout
            else:
                # Drop packet
                logger.warning(f"Dropping packet {packet.packet_id} after timeout")
                del self.send_window[seq_num]
                self.packets_dropped += 1
        
        return transmitted
    
    def _transmit_packet(self, packet: Packet, link_quality: LinkQuality) -> bool:
        """Simulate physical transmission with BER-driven errors."""
        # Calculate packet error probability based on BER
        packet_bits = packet.size_bytes * 8
        packet_error_prob = 1 - (1 - link_quality.bit_error_rate) ** packet_bits
        
        # Simulate transmission
        transmission_successful = random.random() > packet_error_prob
        
        self.packets_sent += 1
        if packet.retransmission_count > 0:
            self.packets_retransmitted += 1
        self.total_bytes_sent += packet.size_bytes
        
        logger.debug(f"Transmitting packet {packet.packet_id}: {'SUCCESS' if transmission_successful else 'ERROR'}")
        
        return transmission_successful
    
    def receive_acknowledgment(self, ack_seq_num: int):
        """Process acknowledgment for a packet."""
        if self.params.arq_protocol == ARQProtocol.STOP_AND_WAIT:
            if ack_seq_num in self.send_window:
                del self.send_window[ack_seq_num]
                self.state = TransmissionState.IDLE
        else:  # Sliding window
            # Remove acknowledged packets (cumulative ACK)
            acked_packets = [seq for seq in self.send_window.keys() if seq <= ack_seq_num]
            for seq in acked_packets:
                del self.send_window[seq]
    
    def _can_buffer_packet(self, packet: Packet) -> bool:
        """Check if packet can be buffered."""
        current_buffer_size = sum(p.size_bytes for p in self.transmit_buffer)
        return current_buffer_size + packet.size_bytes <= self.params.transmit_buffer_size
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Simple checksum calculation."""
        return sum(data) % 65536
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get transmission statistics."""
        return {
            'packets_sent': self.packets_sent,
            'packets_retransmitted': self.packets_retransmitted,
            'packets_dropped': self.packets_dropped,
            'retransmission_ratio': self.packets_retransmitted / max(1, self.packets_sent),
            'drop_ratio': self.packets_dropped / max(1, self.packets_sent),
            'total_bytes_sent': self.total_bytes_sent,
            'buffer_utilization': len(self.transmit_buffer),
            'window_size_used': len(self.send_window)
        }


class SatelliteLink:
    """Complete satellite link with ARQ and error modeling."""
    
    def __init__(self, source_id: str, target_id: str, params: LinkParameters):
        self.source_id = source_id
        self.target_id = target_id
        self.params = params
        self.transmitter = ARQTransmitter(params)
        self.is_active = False
        self.current_quality = None
        
        # Link statistics
        self.total_bundles_queued = 0
        self.total_bundles_transmitted = 0
        self.total_transmission_time = 0.0
    
    def activate(self, distance_km: float, weather_conditions: Optional[Dict] = None):
        """Activate the link with current conditions."""
        self.is_active = True
        self.current_quality = self._calculate_link_quality(distance_km, weather_conditions)
        logger.info(f"Link {self.source_id}->{self.target_id} activated: SNR={self.current_quality.signal_to_noise_ratio_db:.1f}dB, BER={self.current_quality.bit_error_rate:.2e}")
    
    def deactivate(self):
        """Deactivate the link."""
        self.is_active = False
        self.current_quality = None
        logger.info(f"Link {self.source_id}->{self.target_id} deactivated")
    
    def queue_bundle(self, bundle: Bundle) -> bool:
        """Queue a bundle for transmission."""
        if not self.is_active:
            return False
        
        self.total_bundles_queued += 1
        return self.transmitter.queue_bundle(bundle)
    
    def process_transmission(self, current_time: datetime) -> List[Bundle]:
        """Process transmission and return successfully transmitted bundles."""
        if not self.is_active or not self.current_quality:
            return []
        
        start_time = current_time
        transmitted_packets = self.transmitter.transmit_packets(self.current_quality, current_time)
        
        # Group packets back into bundles
        completed_bundles = self._reconstruct_bundles(transmitted_packets)
        
        if completed_bundles:
            self.total_bundles_transmitted += len(completed_bundles)
            transmission_duration = (current_time - start_time).total_seconds()
            self.total_transmission_time += transmission_duration
        
        return completed_bundles
    
    def _calculate_link_quality(self, distance_km: float, weather_conditions: Optional[Dict] = None) -> LinkQuality:
        """Calculate current link quality based on distance and conditions."""
        # Free space path loss
        fspl_db = 32.45 + 20 * math.log10(distance_km) + 20 * math.log10(self.params.frequency_ghz)
        
        # Weather effects
        atmospheric_loss = 0.0
        rain_attenuation = 0.0
        
        if weather_conditions:
            # Simplified weather modeling
            rain_rate = weather_conditions.get('rain_rate_mm_hr', 0)
            humidity = weather_conditions.get('humidity_percent', 50)
            
            # Rain attenuation (ITU-R model simplified)
            if rain_rate > 0:
                rain_attenuation = 0.12 * (rain_rate ** 0.633) * (distance_km / 100)
            
            # Atmospheric absorption
            atmospheric_loss = 0.1 * (humidity / 100) * (distance_km / 1000)
        
        # Calculate received power and SNR
        total_loss = fspl_db + atmospheric_loss + rain_attenuation
        received_power_dbm = self.params.transmit_power_dbm + 2 * self.params.antenna_gain_db - total_loss
        
        # Noise power calculation
        noise_power_dbm = 10 * math.log10(1.38e-23 * self.params.noise_temperature_k * self.params.bandwidth_mhz * 1e6 * 1000)
        
        snr_db = received_power_dbm - noise_power_dbm
        
        # BER calculation (simplified QPSK in AWGN)
        snr_linear = 10 ** (snr_db / 10)
        ber = 0.5 * math.erfc(math.sqrt(snr_linear))
        ber = max(ber, 1e-12)  # Minimum BER
        
        return LinkQuality(
            distance_km=distance_km,
            signal_to_noise_ratio_db=snr_db,
            bit_error_rate=ber,
            packet_error_rate=1 - (1 - ber) ** (1400 * 8),  # For 1400-byte packets
            atmospheric_loss_db=atmospheric_loss,
            rain_attenuation_db=rain_attenuation
        )
    
    def _reconstruct_bundles(self, transmitted_packets: List[Tuple[Packet, bool]]) -> List[Bundle]:
        """Reconstruct bundles from successfully transmitted packets."""
        # Simplified: assume all packets for a bundle are transmitted together
        # In reality, this would be more complex with fragmentation handling
        completed_bundles = []
        
        successful_packets = [packet for packet, success in transmitted_packets if success]
        bundle_groups = {}
        
        for packet in successful_packets:
            if packet.bundle_id not in bundle_groups:
                bundle_groups[packet.bundle_id] = []
            bundle_groups[packet.bundle_id].append(packet)
        
        # For simplicity, create a placeholder Bundle object
        for bundle_id, packets in bundle_groups.items():
            # This would need to reconstruct the actual Bundle object
            # For now, just count successful transmissions
            pass
        
        return completed_bundles
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive link statistics."""
        base_stats = {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'is_active': self.is_active,
            'total_bundles_queued': self.total_bundles_queued,
            'total_bundles_transmitted': self.total_bundles_transmitted,
            'total_transmission_time': self.total_transmission_time
        }
        
        if self.current_quality:
            base_stats.update({
                'current_snr_db': self.current_quality.signal_to_noise_ratio_db,
                'current_ber': self.current_quality.bit_error_rate,
                'current_per': self.current_quality.packet_error_rate,
                'distance_km': self.current_quality.distance_km
            })
        
        base_stats.update(self.transmitter.get_statistics())
        
        return base_stats


def calculate_contact_capacity(
    link_params: LinkParameters,
    contact_duration_seconds: float,
    distance_km: float,
    weather_conditions: Optional[Dict] = None
) -> Dict[str, float]:
    """Calculate contact capacity using: rate × (window - handshake)."""
    
    # Create temporary link to calculate quality
    temp_link = SatelliteLink("temp_src", "temp_dst", link_params)
    temp_link.activate(distance_km, weather_conditions)
    
    if not temp_link.current_quality:
        return {'capacity_bits': 0, 'capacity_bytes': 0, 'effective_rate_bps': 0}
    
    # Calculate effective data rate considering BER
    max_rate_bps = link_params.bandwidth_mhz * 1e6 * 2  # QPSK modulation (2 bits/symbol)
    
    # Adjust for BER and ARQ overhead
    ber = temp_link.current_quality.bit_error_rate
    retransmission_overhead = 1 + (ber * 1400 * 8 * link_params.max_retransmissions)
    effective_rate_bps = max_rate_bps / retransmission_overhead
    
    # Account for handshake/protocol overhead
    handshake_time_seconds = 0.5  # Assume 500ms handshake
    effective_contact_time = max(0, contact_duration_seconds - handshake_time_seconds)
    
    # Calculate capacity
    capacity_bits = effective_rate_bps * effective_contact_time
    capacity_bytes = capacity_bits / 8
    
    return {
        'capacity_bits': capacity_bits,
        'capacity_bytes': capacity_bytes,
        'effective_rate_bps': effective_rate_bps,
        'effective_contact_time': effective_contact_time,
        'ber': ber,
        'retransmission_overhead': retransmission_overhead
    }