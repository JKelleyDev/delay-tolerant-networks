"""
Synthetic Mobility Models for DTN Simulation

Implements various mobility models for DTN nodes including Random Waypoint
and community-based movement patterns.
"""

import math
import random
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Any
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

# Earth parameters
EARTH_RADIUS_KM = 6371.0


@dataclass
class Position:
    """3D position in Earth-Centered Inertial coordinates."""
    x: float  # km
    y: float  # km
    z: float  # km
    timestamp: datetime
    
    def distance_to(self, other: 'Position') -> float:
        """Calculate distance to another position."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def to_lat_lon_alt(self) -> Tuple[float, float, float]:
        """Convert to latitude, longitude, altitude."""
        r = math.sqrt(self.x**2 + self.y**2 + self.z**2)
        lat = math.degrees(math.asin(self.z / r))
        lon = math.degrees(math.atan2(self.y, self.x))
        alt = r - EARTH_RADIUS_KM
        return lat, lon, alt
    
    @classmethod
    def from_lat_lon_alt(cls, lat: float, lon: float, alt: float, timestamp: datetime = None) -> 'Position':
        """Create position from latitude, longitude, altitude."""
        if timestamp is None:
            timestamp = datetime.now()
            
        r = EARTH_RADIUS_KM + alt
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        x = r * math.cos(lat_rad) * math.cos(lon_rad)
        y = r * math.cos(lat_rad) * math.sin(lon_rad)
        z = r * math.sin(lat_rad)
        
        return cls(x, y, z, timestamp)


@dataclass
class Waypoint:
    """Waypoint for mobility models."""
    position: Position
    arrival_time: datetime
    departure_time: datetime
    pause_duration: timedelta
    
    @property
    def is_paused(self) -> bool:
        return self.pause_duration > timedelta(0)


class MobilityModel(ABC):
    """Abstract base class for mobility models."""
    
    def __init__(self, node_id: str, initial_position: Position):
        self.node_id = node_id
        self.current_position = initial_position
        self.waypoints: List[Waypoint] = []
        self.movement_history: List[Position] = [initial_position]
    
    @abstractmethod
    def generate_next_waypoint(self, current_time: datetime) -> Waypoint:
        """Generate the next waypoint for the node."""
        pass
    
    @abstractmethod
    def update_position(self, current_time: datetime) -> Position:
        """Update node position based on current time."""
        pass
    
    def get_position_at_time(self, time: datetime) -> Position:
        """Get position at a specific time."""
        if time <= self.current_position.timestamp:
            return self.current_position
        
        # Find the relevant waypoints
        for i, waypoint in enumerate(self.waypoints):
            if waypoint.arrival_time <= time <= waypoint.departure_time:
                # Node is at this waypoint
                return waypoint.position
            elif i > 0 and self.waypoints[i-1].departure_time <= time <= waypoint.arrival_time:
                # Node is moving between waypoints
                prev_waypoint = self.waypoints[i-1]
                return self._interpolate_position(prev_waypoint, waypoint, time)
        
        # If no waypoints or time is beyond last waypoint, update
        return self.update_position(time)
    
    def _interpolate_position(self, start_waypoint: Waypoint, end_waypoint: Waypoint, time: datetime) -> Position:
        """Interpolate position between two waypoints."""
        total_time = (end_waypoint.arrival_time - start_waypoint.departure_time).total_seconds()
        elapsed_time = (time - start_waypoint.departure_time).total_seconds()
        
        if total_time <= 0:
            return start_waypoint.position
        
        progress = elapsed_time / total_time
        progress = max(0, min(1, progress))  # Clamp to [0, 1]
        
        # Linear interpolation
        start_pos = start_waypoint.position
        end_pos = end_waypoint.position
        
        x = start_pos.x + (end_pos.x - start_pos.x) * progress
        y = start_pos.y + (end_pos.y - start_pos.y) * progress
        z = start_pos.z + (end_pos.z - start_pos.z) * progress
        
        return Position(x, y, z, time)


class RandomWaypointModel(MobilityModel):
    """Random Waypoint mobility model."""
    
    def __init__(
        self,
        node_id: str,
        initial_position: Position,
        movement_area_bounds: Dict[str, Tuple[float, float]],  # {'lat': (min, max), 'lon': (min, max), 'alt': (min, max)}
        min_speed_km_h: float = 5.0,
        max_speed_km_h: float = 50.0,
        min_pause_seconds: float = 0.0,
        max_pause_seconds: float = 300.0,
        random_seed: Optional[int] = None
    ):
        super().__init__(node_id, initial_position)
        self.movement_area = movement_area_bounds
        self.min_speed = min_speed_km_h / 3.6  # Convert to m/s
        self.max_speed = max_speed_km_h / 3.6  # Convert to m/s
        self.min_pause = min_pause_seconds
        self.max_pause = max_pause_seconds
        
        if random_seed is not None:
            random.seed(random_seed)
        
        self.current_speed = 0.0
        self.is_paused = False
        self.pause_end_time = None
    
    def generate_next_waypoint(self, current_time: datetime) -> Waypoint:
        """Generate next random waypoint."""
        # Generate random destination within bounds
        lat_min, lat_max = self.movement_area['lat']
        lon_min, lon_max = self.movement_area['lon']
        alt_min, alt_max = self.movement_area['alt']
        
        dest_lat = random.uniform(lat_min, lat_max)
        dest_lon = random.uniform(lon_min, lon_max)
        dest_alt = random.uniform(alt_min, alt_max)
        
        dest_position = Position.from_lat_lon_alt(dest_lat, dest_lon, dest_alt)
        
        # Calculate travel time based on random speed
        distance_km = self.current_position.distance_to(dest_position)
        speed_km_h = random.uniform(self.min_speed * 3.6, self.max_speed * 3.6)
        self.current_speed = speed_km_h / 3.6  # Store in m/s
        
        travel_time_hours = distance_km / speed_km_h
        travel_time = timedelta(hours=travel_time_hours)
        
        arrival_time = current_time + travel_time
        
        # Generate random pause duration
        pause_seconds = random.uniform(self.min_pause, self.max_pause)
        pause_duration = timedelta(seconds=pause_seconds)
        departure_time = arrival_time + pause_duration
        
        waypoint = Waypoint(
            position=dest_position,
            arrival_time=arrival_time,
            departure_time=departure_time,
            pause_duration=pause_duration
        )
        
        self.waypoints.append(waypoint)
        return waypoint
    
    def update_position(self, current_time: datetime) -> Position:
        """Update position using Random Waypoint model."""
        # Clean up old waypoints
        self._cleanup_old_waypoints(current_time)
        
        # Check if we need to generate new waypoints
        if not self.waypoints or current_time >= self.waypoints[-1].departure_time:
            self.generate_next_waypoint(current_time)
        
        # Find current position
        new_position = self.get_position_at_time(current_time)
        self.current_position = new_position
        self.movement_history.append(new_position)
        
        # Limit history size
        if len(self.movement_history) > 1000:
            self.movement_history = self.movement_history[-500:]
        
        return new_position
    
    def _cleanup_old_waypoints(self, current_time: datetime):
        """Remove waypoints that are no longer needed."""
        cutoff_time = current_time - timedelta(hours=1)
        self.waypoints = [wp for wp in self.waypoints if wp.departure_time > cutoff_time]


class CommunityBasedModel(MobilityModel):
    """Community-based mobility model where nodes tend to move within communities."""
    
    def __init__(
        self,
        node_id: str,
        initial_position: Position,
        communities: List[Dict[str, Any]],  # List of community definitions
        community_id: int,
        inter_community_probability: float = 0.1,
        min_speed_km_h: float = 5.0,
        max_speed_km_h: float = 30.0,
        min_pause_seconds: float = 30.0,
        max_pause_seconds: float = 600.0,
        random_seed: Optional[int] = None
    ):
        super().__init__(node_id, initial_position)
        self.communities = communities
        self.current_community_id = community_id
        self.inter_community_prob = inter_community_probability
        self.min_speed = min_speed_km_h / 3.6
        self.max_speed = max_speed_km_h / 3.6
        self.min_pause = min_pause_seconds
        self.max_pause = max_pause_seconds
        
        if random_seed is not None:
            random.seed(random_seed)
    
    def generate_next_waypoint(self, current_time: datetime) -> Waypoint:
        """Generate waypoint within current community or move to another community."""
        # Decide whether to stay in current community or move to another
        if random.random() < self.inter_community_prob and len(self.communities) > 1:
            # Move to different community
            available_communities = [i for i, _ in enumerate(self.communities) if i != self.current_community_id]
            self.current_community_id = random.choice(available_communities)
        
        # Get current community bounds
        community = self.communities[self.current_community_id]
        bounds = community['bounds']
        
        # Generate destination within community
        lat_min, lat_max = bounds['lat']
        lon_min, lon_max = bounds['lon']
        alt_min, alt_max = bounds['alt']
        
        dest_lat = random.uniform(lat_min, lat_max)
        dest_lon = random.uniform(lon_min, lon_max)
        dest_alt = random.uniform(alt_min, alt_max)
        
        dest_position = Position.from_lat_lon_alt(dest_lat, dest_lon, dest_alt)
        
        # Calculate travel time
        distance_km = self.current_position.distance_to(dest_position)
        speed_km_h = random.uniform(self.min_speed * 3.6, self.max_speed * 3.6)
        
        # Adjust speed based on community type
        speed_multiplier = community.get('speed_multiplier', 1.0)
        speed_km_h *= speed_multiplier
        
        travel_time_hours = distance_km / speed_km_h
        travel_time = timedelta(hours=travel_time_hours)
        arrival_time = current_time + travel_time
        
        # Pause duration influenced by community characteristics
        base_pause = random.uniform(self.min_pause, self.max_pause)
        pause_multiplier = community.get('pause_multiplier', 1.0)
        pause_seconds = base_pause * pause_multiplier
        
        pause_duration = timedelta(seconds=pause_seconds)
        departure_time = arrival_time + pause_duration
        
        waypoint = Waypoint(
            position=dest_position,
            arrival_time=arrival_time,
            departure_time=departure_time,
            pause_duration=pause_duration
        )
        
        self.waypoints.append(waypoint)
        return waypoint
    
    def update_position(self, current_time: datetime) -> Position:
        """Update position using community-based model."""
        self._cleanup_old_waypoints(current_time)
        
        if not self.waypoints or current_time >= self.waypoints[-1].departure_time:
            self.generate_next_waypoint(current_time)
        
        new_position = self.get_position_at_time(current_time)
        self.current_position = new_position
        self.movement_history.append(new_position)
        
        if len(self.movement_history) > 1000:
            self.movement_history = self.movement_history[-500:]
        
        return new_position
    
    def _cleanup_old_waypoints(self, current_time: datetime):
        """Remove old waypoints."""
        cutoff_time = current_time - timedelta(hours=1)
        self.waypoints = [wp for wp in self.waypoints if wp.departure_time > cutoff_time]


class MobilityManager:
    """Manager for multiple mobility models."""
    
    def __init__(self):
        self.mobility_models: Dict[str, MobilityModel] = {}
        self.node_positions: Dict[str, Position] = {}
        self.position_history: Dict[str, List[Position]] = {}
    
    def add_node(self, node_id: str, mobility_model: MobilityModel):
        """Add a node with its mobility model."""
        self.mobility_models[node_id] = mobility_model
        self.node_positions[node_id] = mobility_model.current_position
        self.position_history[node_id] = [mobility_model.current_position]
    
    def update_all_positions(self, current_time: datetime) -> Dict[str, Position]:
        """Update positions for all nodes."""
        for node_id, model in self.mobility_models.items():
            new_position = model.update_position(current_time)
            self.node_positions[node_id] = new_position
            
            # Update history
            if node_id not in self.position_history:
                self.position_history[node_id] = []
            self.position_history[node_id].append(new_position)
            
            # Limit history size
            if len(self.position_history[node_id]) > 1000:
                self.position_history[node_id] = self.position_history[node_id][-500:]
        
        return self.node_positions.copy()
    
    def get_node_position(self, node_id: str, time: datetime) -> Optional[Position]:
        """Get position of a specific node at a specific time."""
        if node_id in self.mobility_models:
            return self.mobility_models[node_id].get_position_at_time(time)
        return None
    
    def calculate_contact_opportunities(
        self,
        time: datetime,
        max_distance_km: float = 2000.0
    ) -> List[Tuple[str, str, float]]:
        """Calculate potential contacts between nodes."""
        contacts = []
        node_ids = list(self.node_positions.keys())
        
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                node1_id = node_ids[i]
                node2_id = node_ids[j]
                
                pos1 = self.get_node_position(node1_id, time)
                pos2 = self.get_node_position(node2_id, time)
                
                if pos1 and pos2:
                    distance = pos1.distance_to(pos2)
                    if distance <= max_distance_km:
                        contacts.append((node1_id, node2_id, distance))
        
        return contacts
    
    def get_mobility_statistics(self) -> Dict[str, Any]:
        """Get statistics about node mobility."""
        stats = {
            'total_nodes': len(self.mobility_models),
            'node_stats': {}
        }
        
        for node_id, model in self.mobility_models.items():
            if len(model.movement_history) > 1:
                # Calculate average speed
                total_distance = 0
                total_time = 0
                
                for i in range(1, len(model.movement_history)):
                    prev_pos = model.movement_history[i-1]
                    curr_pos = model.movement_history[i]
                    
                    distance = prev_pos.distance_to(curr_pos)
                    time_diff = (curr_pos.timestamp - prev_pos.timestamp).total_seconds()
                    
                    total_distance += distance
                    total_time += time_diff
                
                avg_speed_km_h = (total_distance / max(total_time, 1)) * 3.6
                
                # Calculate movement area
                lats = []
                lons = []
                alts = []
                
                for pos in model.movement_history:
                    lat, lon, alt = pos.to_lat_lon_alt()
                    lats.append(lat)
                    lons.append(lon)
                    alts.append(alt)
                
                movement_area = {
                    'lat_range': max(lats) - min(lats) if lats else 0,
                    'lon_range': max(lons) - min(lons) if lons else 0,
                    'alt_range': max(alts) - min(alts) if alts else 0
                }
                
                stats['node_stats'][node_id] = {
                    'model_type': model.__class__.__name__,
                    'average_speed_km_h': avg_speed_km_h,
                    'total_distance_km': total_distance,
                    'movement_area': movement_area,
                    'waypoint_count': len(model.waypoints),
                    'position_history_length': len(model.movement_history)
                }
        
        return stats


def create_random_waypoint_scenario(
    node_count: int,
    area_bounds: Dict[str, Tuple[float, float]],
    simulation_duration_hours: float = 24.0,
    random_seed: Optional[int] = None
) -> MobilityManager:
    """Create a scenario with Random Waypoint mobility."""
    if random_seed is not None:
        random.seed(random_seed)
    
    manager = MobilityManager()
    start_time = datetime.now()
    
    for i in range(node_count):
        # Random initial position within bounds
        lat = random.uniform(*area_bounds['lat'])
        lon = random.uniform(*area_bounds['lon'])
        alt = random.uniform(*area_bounds['alt'])
        
        initial_pos = Position.from_lat_lon_alt(lat, lon, alt, start_time)
        
        # Create Random Waypoint model
        model = RandomWaypointModel(
            node_id=f"mobile_node_{i}",
            initial_position=initial_pos,
            movement_area_bounds=area_bounds,
            min_speed_km_h=5.0,
            max_speed_km_h=25.0,
            min_pause_seconds=30.0,
            max_pause_seconds=300.0,
            random_seed=random_seed + i if random_seed else None
        )
        
        manager.add_node(f"mobile_node_{i}", model)
    
    return manager


def create_community_based_scenario(
    communities: List[Dict[str, Any]],
    nodes_per_community: List[int],
    simulation_duration_hours: float = 24.0,
    random_seed: Optional[int] = None
) -> MobilityManager:
    """Create a scenario with community-based mobility."""
    if random_seed is not None:
        random.seed(random_seed)
    
    manager = MobilityManager()
    start_time = datetime.now()
    node_counter = 0
    
    for community_id, (community, node_count) in enumerate(zip(communities, nodes_per_community)):
        bounds = community['bounds']
        
        for i in range(node_count):
            # Random initial position within community bounds
            lat = random.uniform(*bounds['lat'])
            lon = random.uniform(*bounds['lon'])
            alt = random.uniform(*bounds['alt'])
            
            initial_pos = Position.from_lat_lon_alt(lat, lon, alt, start_time)
            
            # Create community-based model
            model = CommunityBasedModel(
                node_id=f"community_node_{node_counter}",
                initial_position=initial_pos,
                communities=communities,
                community_id=community_id,
                inter_community_probability=0.1,
                random_seed=random_seed + node_counter if random_seed else None
            )
            
            manager.add_node(f"community_node_{node_counter}", model)
            node_counter += 1
    
    return manager