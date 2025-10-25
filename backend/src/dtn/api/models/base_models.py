"""
Base API Models

Common Pydantic models used across API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List
from datetime import datetime
from enum import Enum


class APIResponse(BaseModel):
    """Standard API response format."""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SimulationStatus(str, Enum):
    """Simulation status enumeration."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


class RoutingAlgorithm(str, Enum):
    """Available routing algorithms."""
    EPIDEMIC = "epidemic"
    PROPHET = "prophet"
    SPRAY_AND_WAIT = "spray_and_wait"
    CONTACT_GRAPH = "contact_graph"
    ADAPTIVE = "adaptive"


class ConstellationType(str, Enum):
    """Satellite constellation types."""
    LEO = "leo"
    MEO = "meo"
    GEO = "geo"
    HEO = "heo"
    MIXED = "mixed"
    CUSTOM = "custom"


class Position3D(BaseModel):
    """3D position coordinates."""
    x: float = Field(..., description="X coordinate (km)")
    y: float = Field(..., description="Y coordinate (km)")
    z: float = Field(..., description="Z coordinate (km)")


class GeodeticPosition(BaseModel):
    """Geodetic position (lat, lon, alt)."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    altitude: float = Field(..., ge=0, description="Altitude in km")


class SatelliteInfo(BaseModel):
    """Satellite information."""
    id: str = Field(..., description="Unique satellite identifier")
    name: str = Field(..., description="Satellite name")
    position: Position3D = Field(..., description="Current position")
    velocity: Position3D = Field(..., description="Current velocity")
    geodetic: GeodeticPosition = Field(..., description="Geodetic coordinates")
    active_contacts: List[str] = Field(default=[], description="Active contact IDs")
    buffer_usage: float = Field(default=0.0, ge=0, le=100, description="Buffer usage percentage")


class GroundStationInfo(BaseModel):
    """Ground station information."""
    id: str = Field(..., description="Unique ground station identifier")
    name: str = Field(..., description="Ground station name")
    position: GeodeticPosition = Field(..., description="Ground station location")
    elevation_mask: float = Field(default=10.0, description="Minimum elevation angle (degrees)")
    active_contacts: List[str] = Field(default=[], description="Active contact IDs")


class ContactWindow(BaseModel):
    """Communication contact window."""
    id: str = Field(..., description="Unique contact identifier")
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    start_time: datetime = Field(..., description="Contact start time")
    end_time: datetime = Field(..., description="Contact end time")
    max_elevation: float = Field(..., description="Maximum elevation angle (degrees)")
    data_rate: float = Field(..., description="Data rate (Mbps)")
    is_active: bool = Field(default=False, description="Is contact currently active")


class NetworkMetrics(BaseModel):
    """Network performance metrics."""
    delivery_ratio: float = Field(..., ge=0, le=1, description="Bundle delivery ratio")
    average_delay: float = Field(..., ge=0, description="Average end-to-end delay (seconds)")
    hop_count_avg: float = Field(..., ge=0, description="Average hop count")
    network_overhead: float = Field(..., ge=0, description="Network overhead ratio")
    buffer_utilization: float = Field(..., ge=0, le=100, description="Average buffer utilization (%)")
    bundles_generated: int = Field(..., ge=0, description="Total bundles generated")
    bundles_delivered: int = Field(..., ge=0, description="Total bundles delivered")
    bundles_expired: int = Field(..., ge=0, description="Total bundles expired")


class ExperimentConfig(BaseModel):
    """Experiment configuration."""
    name: str = Field(..., description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    duration: float = Field(..., gt=0, description="Experiment duration (hours)")
    routing_algorithms: List[RoutingAlgorithm] = Field(..., description="Algorithms to compare")
    constellation_id: str = Field(..., description="Constellation to use")
    traffic_pattern: str = Field(default="uniform", description="Traffic generation pattern")
    bundle_size: int = Field(default=1024, gt=0, description="Bundle payload size (bytes)")
    bundle_rate: float = Field(default=1.0, gt=0, description="Bundle generation rate (bundles/second)")
    buffer_size: int = Field(default=10*1024*1024, gt=0, description="Node buffer size (bytes)")


class SimulationConfig(BaseModel):
    """Simulation configuration."""
    name: str = Field(..., description="Simulation name")
    constellation_id: str = Field(..., description="Constellation identifier")
    routing_algorithm: RoutingAlgorithm = Field(..., description="Routing algorithm")
    duration: float = Field(..., gt=0, description="Simulation duration (hours)")
    time_step: float = Field(default=1.0, gt=0, description="Simulation time step (seconds)")
    start_time: Optional[datetime] = Field(None, description="Simulation start time")
    ground_stations: List[str] = Field(default=[], description="Ground station IDs to include")
    experiment_config: Optional[ExperimentConfig] = Field(None, description="Experiment configuration")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


class TimeRange(BaseModel):
    """Time range filter."""
    start: Optional[datetime] = Field(None, description="Start time")
    end: Optional[datetime] = Field(None, description="End time")