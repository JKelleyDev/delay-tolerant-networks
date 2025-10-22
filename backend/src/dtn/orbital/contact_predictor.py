"""
Contact Prediction System

Generates realistic satellite contact windows based on orbital mechanics.
Integrates with DTN simulation for dynamic topology changes.
"""

import math
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from .orbital_mechanics import OrbitalMechanics, OrbitalElements, Position3D
from ..core.bundle import Contact


@dataclass
class ContactWindow:
    """Represents a predicted contact opportunity between two satellites."""
    source_sat: str
    dest_sat: str
    start_time: float
    end_time: float
    max_elevation_deg: float
    min_range_km: float
    data_rate_bps: int
    
    def to_contact(self) -> Contact:
        """Convert to DTN Contact object."""
        return Contact(
            source=self.source_sat,
            destination=self.dest_sat,
            start_time=self.start_time,
            end_time=self.end_time,
            data_rate_bps=self.data_rate_bps
        )


class ContactPredictor:
    """Predicts satellite contact windows using orbital mechanics."""
    
    def __init__(self, orbital_calc: OrbitalMechanics):
        self.orbital_calc = orbital_calc
        self.min_elevation_deg = 10.0  # Minimum elevation for valid contact
        self.max_range_km = 2000.0     # Maximum communication range
        self.base_data_rate_bps = 1000000  # 1 Mbps base rate
        
    def predict_contacts(self, satellite_orbits: Dict[str, OrbitalElements], 
                        start_time: float, duration_hours: float = 24.0,
                        time_step_minutes: float = 1.0) -> List[ContactWindow]:
        """
        Predict all contact windows between satellites over a time period.
        
        Args:
            satellite_orbits: Dictionary of satellite_id -> orbital elements
            start_time: Start time for prediction (Unix timestamp)
            duration_hours: How far ahead to predict
            time_step_minutes: Temporal resolution for prediction
            
        Returns:
            List of predicted contact windows
        """
        contacts = []
        end_time = start_time + (duration_hours * 3600)
        time_step = time_step_minutes * 60
        
        satellite_ids = list(satellite_orbits.keys())
        
        for i, sat1_id in enumerate(satellite_ids):
            for sat2_id in satellite_ids[i+1:]:
                # Predict contacts between this pair
                pair_contacts = self._predict_satellite_pair_contacts(
                    sat1_id, satellite_orbits[sat1_id],
                    sat2_id, satellite_orbits[sat2_id],
                    start_time, end_time, time_step
                )
                contacts.extend(pair_contacts)
                
        return sorted(contacts, key=lambda c: c.start_time)
        
    def _predict_satellite_pair_contacts(self, sat1_id: str, sat1_orbit: OrbitalElements,
                                       sat2_id: str, sat2_orbit: OrbitalElements,
                                       start_time: float, end_time: float, 
                                       time_step: float) -> List[ContactWindow]:
        """Predict contacts between a specific pair of satellites."""
        contacts = []
        current_time = start_time
        in_contact = False
        contact_start = None
        min_range = float('inf')
        max_elevation = 0.0
        
        while current_time <= end_time:
            # Get satellite positions
            try:
                state1 = self.orbital_calc.propagate_orbit(sat1_orbit, current_time)
                state2 = self.orbital_calc.propagate_orbit(sat2_orbit, current_time)
                
                # Calculate range between satellites
                range_km = self._calculate_range(state1.position, state2.position)
                
                # Calculate elevation (simplified - assumes line of sight)
                elevation_deg = self._calculate_elevation(state1.position, state2.position)
                
                # Check if satellites are in contact
                contact_possible = (range_km <= self.max_range_km and 
                                  elevation_deg >= self.min_elevation_deg)
                
                if contact_possible and not in_contact:
                    # Contact starts
                    in_contact = True
                    contact_start = current_time
                    min_range = range_km
                    max_elevation = elevation_deg
                    
                elif contact_possible and in_contact:
                    # Contact continues - update metrics
                    min_range = min(min_range, range_km)
                    max_elevation = max(max_elevation, elevation_deg)
                    
                elif not contact_possible and in_contact:
                    # Contact ends
                    in_contact = False
                    if contact_start is not None:
                        # Calculate data rate based on range
                        data_rate = self._calculate_data_rate(min_range, max_elevation)
                        
                        # Create contact window
                        contact = ContactWindow(
                            source_sat=sat1_id,
                            dest_sat=sat2_id,
                            start_time=contact_start,
                            end_time=current_time,
                            max_elevation_deg=max_elevation,
                            min_range_km=min_range,
                            data_rate_bps=data_rate
                        )
                        contacts.append(contact)
                        
                        # Also create reverse direction contact
                        reverse_contact = ContactWindow(
                            source_sat=sat2_id,
                            dest_sat=sat1_id,
                            start_time=contact_start,
                            end_time=current_time,
                            max_elevation_deg=max_elevation,
                            min_range_km=min_range,
                            data_rate_bps=data_rate
                        )
                        contacts.append(reverse_contact)
                        
            except Exception as e:
                # Skip this time step if orbital propagation fails
                pass
                
            current_time += time_step
            
        # Handle contact that's still active at end time
        if in_contact and contact_start is not None:
            data_rate = self._calculate_data_rate(min_range, max_elevation)
            contact = ContactWindow(
                source_sat=sat1_id,
                dest_sat=sat2_id,
                start_time=contact_start,
                end_time=current_time,
                max_elevation_deg=max_elevation,
                min_range_km=min_range,
                data_rate_bps=data_rate
            )
            contacts.append(contact)
            
            reverse_contact = ContactWindow(
                source_sat=sat2_id,
                dest_sat=sat1_id,
                start_time=contact_start,
                end_time=current_time,
                max_elevation_deg=max_elevation,
                min_range_km=min_range,
                data_rate_bps=data_rate
            )
            contacts.append(reverse_contact)
            
        return contacts
        
    def _calculate_range(self, pos1: Position3D, pos2: Position3D) -> float:
        """Calculate distance between two satellite positions."""
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        dz = pos1.z - pos2.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
        
    def _calculate_elevation(self, pos1: Position3D, pos2: Position3D) -> float:
        """Simplified elevation calculation."""
        # For inter-satellite links, elevation is less relevant
        # Use a simplified metric based on relative position
        range_km = self._calculate_range(pos1, pos2)
        
        # Assume better "elevation" (link quality) for closer satellites
        if range_km <= 500:
            return 90.0  # Excellent link
        elif range_km <= 1000:
            return 45.0  # Good link
        elif range_km <= 1500:
            return 20.0  # Marginal link
        else:
            return 5.0   # Poor link
            
    def _calculate_data_rate(self, range_km: float, elevation_deg: float) -> int:
        """Calculate link data rate based on range and elevation."""
        # Simple link budget calculation
        # Better elevation and shorter range = higher data rate
        
        range_factor = max(0.1, (2000.0 - range_km) / 2000.0)  # 0.1 to 1.0
        elevation_factor = max(0.1, elevation_deg / 90.0)       # 0.1 to 1.0
        
        combined_factor = range_factor * elevation_factor
        data_rate = int(self.base_data_rate_bps * combined_factor)
        
        return max(10000, data_rate)  # Minimum 10 kbps
        
    def get_contact_plan_csv(self, contacts: List[ContactWindow]) -> str:
        """Export contact plan in CSV format for analysis."""
        header = "start_time,end_time,source,destination,range_km,elevation_deg,data_rate_bps\\n"
        lines = [header]
        
        for contact in contacts:
            line = f"{contact.start_time},{contact.end_time},{contact.source_sat}," \
                   f"{contact.dest_sat},{contact.min_range_km:.2f}," \
                   f"{contact.max_elevation_deg:.2f},{contact.data_rate_bps}\\n"
            lines.append(line)
            
        return "".join(lines)