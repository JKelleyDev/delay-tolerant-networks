"""
Satellite and Ground Station Loader

Handles loading satellites and ground stations from CSV files and manual input.
Supports Earth satellites, Mars satellites, and ground stations.
"""

import csv
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from .orbital_mechanics import OrbitalElements


@dataclass
class GroundStation:
    """Represents a ground station on Earth or Mars."""
    name: str
    latitude: float  # degrees
    longitude: float  # degrees
    altitude_km: float = 0.0
    planet: str = "Earth"  # "Earth" or "Mars"
    antenna_gain_db: float = 30.0
    max_data_rate_bps: int = 1000000
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude_km": self.altitude_km,
            "planet": self.planet,
            "antenna_gain_db": self.antenna_gain_db,
            "max_data_rate_bps": self.max_data_rate_bps
        }


class SatelliteLoader:
    """Loads satellites and ground stations from various sources."""
    
    def __init__(self):
        self.satellites: Dict[str, Dict[str, Any]] = {}
        self.ground_stations: Dict[str, GroundStation] = {}
        
    def load_satellites_from_csv(self, csv_file_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Load satellites from CSV file.
        
        Expected CSV format:
        name,semi_major_axis_km,eccentricity,inclination_deg,raan_deg,arg_perigee_deg,true_anomaly_deg,epoch_unix,reference_body
        ISS,6793.0,0.0003,51.6,180.0,90.0,0.0,1640995200,Earth
        """
        satellites = {}
        
        try:
            with open(csv_file_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        name = row['name']
                        orbital_elements = OrbitalElements(
                            semi_major_axis=float(row['semi_major_axis_km']),
                            eccentricity=float(row['eccentricity']),
                            inclination=float(row['inclination_deg']),
                            raan=float(row['raan_deg']),
                            arg_perigee=float(row['arg_perigee_deg']),
                            true_anomaly=float(row['true_anomaly_deg']),
                            epoch=float(row.get('epoch_unix', 0))
                        )
                        
                        reference_body = row.get('reference_body', 'Earth').upper()
                        
                        satellites[name] = {
                            "name": name,
                            "elements": orbital_elements,
                            "ref": reference_body,
                            "source": "csv"
                        }
                        
                    except (KeyError, ValueError) as e:
                        print(f"Error parsing satellite {row.get('name', 'unknown')}: {e}")
                        continue
                        
        except FileNotFoundError:
            print(f"CSV file not found: {csv_file_path}")
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            
        self.satellites.update(satellites)
        return satellites
        
    def load_ground_stations_from_csv(self, csv_file_path: str) -> Dict[str, GroundStation]:
        """
        Load ground stations from CSV file.
        
        Expected CSV format:
        name,latitude_deg,longitude_deg,altitude_km,planet,antenna_gain_db,max_data_rate_bps
        DSN_Madrid,40.4319,-4.2508,0.834,Earth,70,50000000
        Mars_Base_Alpha,-14.5684,-175.4783,0.0,Mars,50,10000000
        """
        ground_stations = {}
        
        try:
            with open(csv_file_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        station = GroundStation(
                            name=row['name'],
                            latitude=float(row['latitude_deg']),
                            longitude=float(row['longitude_deg']),
                            altitude_km=float(row.get('altitude_km', 0.0)),
                            planet=row.get('planet', 'Earth'),
                            antenna_gain_db=float(row.get('antenna_gain_db', 30.0)),
                            max_data_rate_bps=int(row.get('max_data_rate_bps', 1000000))
                        )
                        
                        ground_stations[station.name] = station
                        
                    except (KeyError, ValueError) as e:
                        print(f"Error parsing ground station {row.get('name', 'unknown')}: {e}")
                        continue
                        
        except FileNotFoundError:
            print(f"Ground stations CSV file not found: {csv_file_path}")
        except Exception as e:
            print(f"Error loading ground stations CSV: {e}")
            
        self.ground_stations.update(ground_stations)
        return ground_stations
        
    def add_satellite_manual(self, name: str, semi_major_axis_km: float, 
                           eccentricity: float, inclination_deg: float,
                           raan_deg: float, arg_perigee_deg: float, 
                           true_anomaly_deg: float, reference_body: str = "Earth",
                           epoch_unix: float = 0) -> bool:
        """Add a satellite manually with orbital parameters."""
        try:
            orbital_elements = OrbitalElements(
                semi_major_axis=semi_major_axis_km,
                eccentricity=eccentricity,
                inclination=inclination_deg,
                raan=raan_deg,
                arg_perigee=arg_perigee_deg,
                true_anomaly=true_anomaly_deg,
                epoch=epoch_unix
            )
            
            self.satellites[name] = {
                "name": name,
                "elements": orbital_elements,
                "ref": reference_body.upper(),
                "source": "manual"
            }
            
            return True
            
        except Exception as e:
            print(f"Error adding satellite {name}: {e}")
            return False
            
    def add_ground_station_manual(self, name: str, latitude: float, longitude: float,
                                 altitude_km: float = 0.0, planet: str = "Earth",
                                 antenna_gain_db: float = 30.0, 
                                 max_data_rate_bps: int = 1000000) -> bool:
        """Add a ground station manually."""
        try:
            station = GroundStation(
                name=name,
                latitude=latitude,
                longitude=longitude,
                altitude_km=altitude_km,
                planet=planet,
                antenna_gain_db=antenna_gain_db,
                max_data_rate_bps=max_data_rate_bps
            )
            
            self.ground_stations[name] = station
            return True
            
        except Exception as e:
            print(f"Error adding ground station {name}: {e}")
            return False
            
    def create_default_constellation(self):
        """Create default constellation if no satellites loaded."""
        if not self.satellites:
            # ISS
            self.add_satellite_manual(
                "ISS", 6793.0, 0.0003, 51.6, 180.0, 90.0, 0.0, "Earth"
            )
            
            # GPS constellation
            for i in range(3):
                self.add_satellite_manual(
                    f"GPS-{i+1}", 26560.0, 0.01, 55.0, 
                    90.0 + i * 120, 45.0, i * 120.0, "Earth"
                )
                
            # Mars satellites
            self.add_satellite_manual(
                "Mars-Relay-1", 3800.0, 0.02, 25.0, 0.0, 0.0, 90.0, "Mars"
            )
            
        if not self.ground_stations:
            # Earth ground stations
            self.add_ground_station_manual(
                "DSN_Goldstone", 35.2393, -116.8903, 1.071, "Earth", 70, 50000000
            )
            self.add_ground_station_manual(
                "DSN_Madrid", 40.4319, -4.2508, 0.834, "Earth", 70, 50000000
            )
            self.add_ground_station_manual(
                "DSN_Canberra", -35.4005, 148.9813, 0.691, "Earth", 70, 50000000
            )
            
            # Mars ground stations (future missions)
            self.add_ground_station_manual(
                "Mars_Base_Alpha", -14.5684, -175.4783, 0.0, "Mars", 50, 10000000
            )
            
    def get_all_satellites(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded satellites."""
        return self.satellites.copy()
        
    def get_all_ground_stations(self) -> Dict[str, GroundStation]:
        """Get all loaded ground stations."""
        return self.ground_stations.copy()
        
    def get_satellites_by_reference(self, reference_body: str) -> Dict[str, Dict[str, Any]]:
        """Get satellites orbiting a specific body (Earth, Mars, etc)."""
        return {
            name: sat for name, sat in self.satellites.items() 
            if sat["ref"].upper() == reference_body.upper()
        }
        
    def get_ground_stations_by_planet(self, planet: str) -> Dict[str, GroundStation]:
        """Get ground stations on a specific planet."""
        return {
            name: station for name, station in self.ground_stations.items()
            if station.planet.upper() == planet.upper()
        }
        
    def export_to_csv(self, satellites_file: str = None, stations_file: str = None):
        """Export current satellites and ground stations to CSV files."""
        if satellites_file and self.satellites:
            with open(satellites_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'name', 'semi_major_axis_km', 'eccentricity', 'inclination_deg',
                    'raan_deg', 'arg_perigee_deg', 'true_anomaly_deg', 'epoch_unix', 'reference_body'
                ])
                
                for name, sat in self.satellites.items():
                    elements = sat['elements']
                    writer.writerow([
                        name, elements.semi_major_axis, elements.eccentricity,
                        elements.inclination, elements.raan, elements.arg_perigee,
                        elements.true_anomaly, elements.epoch, sat['ref']
                    ])
                    
        if stations_file and self.ground_stations:
            with open(stations_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'name', 'latitude_deg', 'longitude_deg', 'altitude_km',
                    'planet', 'antenna_gain_db', 'max_data_rate_bps'
                ])
                
                for name, station in self.ground_stations.items():
                    writer.writerow([
                        name, station.latitude, station.longitude, station.altitude_km,
                        station.planet, station.antenna_gain_db, station.max_data_rate_bps
                    ])
                    
    def to_json(self) -> Dict[str, Any]:
        """Export configuration to JSON format."""
        return {
            "satellites": {
                name: {
                    "name": sat["name"],
                    "orbital_elements": {
                        "semi_major_axis": sat["elements"].semi_major_axis,
                        "eccentricity": sat["elements"].eccentricity,
                        "inclination": sat["elements"].inclination,
                        "raan": sat["elements"].raan,
                        "arg_perigee": sat["elements"].arg_perigee,
                        "true_anomaly": sat["elements"].true_anomaly,
                        "epoch": sat["elements"].epoch
                    },
                    "reference_body": sat["ref"],
                    "source": sat["source"]
                }
                for name, sat in self.satellites.items()
            },
            "ground_stations": {
                name: station.to_dict()
                for name, station in self.ground_stations.items()
            }
        }