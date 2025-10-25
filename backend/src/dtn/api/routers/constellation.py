"""
Constellation Management Router

Handles satellite constellation loading, management, and configuration.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional
import csv
import io
import logging

from ..models.base_models import APIResponse, ConstellationType, SatelliteInfo

logger = logging.getLogger(__name__)
router = APIRouter()

# Built-in constellation library
CONSTELLATION_LIBRARY = {
    "starlink": {
        "name": "Starlink (Phase 1)",
        "type": ConstellationType.LEO,
        "satellites": 1584,
        "shells": [
            {"altitude": 550, "inclination": 53.0, "count": 1584}
        ],
        "description": "SpaceX Starlink constellation Phase 1"
    },
    "kuiper": {
        "name": "Project Kuiper",
        "type": ConstellationType.LEO,
        "satellites": 3236,
        "shells": [
            {"altitude": 630, "inclination": 51.9, "count": 1296},
            {"altitude": 610, "inclination": 42.0, "count": 1156},
            {"altitude": 590, "inclination": 33.0, "count": 784}
        ],
        "description": "Amazon Project Kuiper constellation"
    },
    "gps": {
        "name": "GPS",
        "type": ConstellationType.MEO,
        "satellites": 31,
        "shells": [
            {"altitude": 20200, "inclination": 55.0, "count": 31}
        ],
        "description": "Global Positioning System constellation"
    },
    "geo_minimal": {
        "name": "GEO Minimal",
        "type": ConstellationType.GEO,
        "satellites": 3,
        "shells": [
            {"altitude": 35786, "inclination": 0.0, "count": 3}
        ],
        "description": "Minimal 3-satellite geostationary coverage"
    },
    "molniya": {
        "name": "Molniya",
        "type": ConstellationType.HEO,
        "satellites": 12,
        "shells": [
            {"altitude": 26600, "inclination": 63.4, "count": 12, "eccentricity": 0.74}
        ],
        "description": "Molniya-type highly elliptical orbit constellation"
    }
}


@router.get("/library", response_model=APIResponse)
async def get_constellation_library():
    """Get available constellation configurations."""
    return APIResponse(
        success=True,
        message="Constellation library retrieved successfully",
        data={"constellations": CONSTELLATION_LIBRARY}
    )


@router.get("/{constellation_id}", response_model=APIResponse)
async def get_constellation(constellation_id: str):
    """Get specific constellation configuration."""
    if constellation_id not in CONSTELLATION_LIBRARY:
        raise HTTPException(status_code=404, detail="Constellation not found")
    
    constellation = CONSTELLATION_LIBRARY[constellation_id]
    return APIResponse(
        success=True,
        message="Constellation retrieved successfully",
        data={"constellation": constellation}
    )


@router.post("/upload", response_model=APIResponse)
async def upload_constellation(
    name: str,
    description: str = "",
    file: UploadFile = File(...)
):
    """Upload a custom constellation from CSV file.
    
    Expected CSV format:
    satellite_id,name,altitude,inclination,raan,eccentricity,arg_perigee,mean_anomaly
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be CSV format")
        
        # Read CSV content
        content = await file.read()
        csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
        
        # Parse satellites
        satellites = []
        required_fields = ['satellite_id', 'name', 'altitude', 'inclination']
        
        for row in csv_reader:
            # Check required fields
            missing_fields = [field for field in required_fields if field not in row]
            if missing_fields:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required fields: {missing_fields}"
                )
            
            satellite = {
                "id": row['satellite_id'],
                "name": row['name'],
                "altitude": float(row['altitude']),
                "inclination": float(row['inclination']),
                "raan": float(row.get('raan', 0)),
                "eccentricity": float(row.get('eccentricity', 0)),
                "arg_perigee": float(row.get('arg_perigee', 0)),
                "mean_anomaly": float(row.get('mean_anomaly', 0))
            }
            satellites.append(satellite)
        
        if not satellites:
            raise HTTPException(status_code=400, detail="No valid satellites found in file")
        
        # Create constellation ID
        constellation_id = f"custom_{name.lower().replace(' ', '_')}"
        
        # Store custom constellation
        constellation = {
            "name": name,
            "type": ConstellationType.CUSTOM,
            "satellites": len(satellites),
            "description": description,
            "satellite_data": satellites,
            "uploaded": True
        }
        
        # Add to library (in memory for now)
        CONSTELLATION_LIBRARY[constellation_id] = constellation
        
        return APIResponse(
            success=True,
            message="Constellation uploaded successfully",
            data={
                "constellation_id": constellation_id,
                "satellite_count": len(satellites),
                "constellation": constellation
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data format: {e}")
    except Exception as e:
        logger.error(f"Failed to upload constellation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{constellation_id}/satellites", response_model=APIResponse)
async def get_constellation_satellites(
    constellation_id: str,
    limit: Optional[int] = None
):
    """Get satellite list for a constellation."""
    if constellation_id not in CONSTELLATION_LIBRARY:
        raise HTTPException(status_code=404, detail="Constellation not found")
    
    constellation = CONSTELLATION_LIBRARY[constellation_id]
    
    # For custom constellations, return actual satellite data
    if "satellite_data" in constellation:
        satellites = constellation["satellite_data"]
        if limit:
            satellites = satellites[:limit]
        
        return APIResponse(
            success=True,
            message="Satellites retrieved successfully",
            data={"satellites": satellites}
        )
    
    # For built-in constellations, generate placeholder data
    satellites = []
    total_sats = constellation["satellites"]
    if limit:
        total_sats = min(total_sats, limit)
    
    for i in range(total_sats):
        satellite = {
            "id": f"{constellation_id}_sat_{i:03d}",
            "name": f"{constellation['name']} Satellite {i+1}",
            "shell_index": 0,  # Simplified for now
            "orbital_elements": constellation["shells"][0] if constellation["shells"] else {}
        }
        satellites.append(satellite)
    
    return APIResponse(
        success=True,
        message="Satellites retrieved successfully",
        data={
            "satellites": satellites,
            "total_count": constellation["satellites"],
            "returned_count": len(satellites)
        }
    )


@router.delete("/{constellation_id}", response_model=APIResponse)
async def delete_constellation(constellation_id: str):
    """Delete a custom constellation."""
    if constellation_id not in CONSTELLATION_LIBRARY:
        raise HTTPException(status_code=404, detail="Constellation not found")
    
    constellation = CONSTELLATION_LIBRARY[constellation_id]
    
    # Only allow deletion of custom constellations
    if not constellation.get("uploaded", False):
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete built-in constellation"
        )
    
    del CONSTELLATION_LIBRARY[constellation_id]
    
    return APIResponse(
        success=True,
        message="Constellation deleted successfully",
        data={"constellation_id": constellation_id}
    )


@router.get("/{constellation_id}/generate", response_model=APIResponse)
async def generate_constellation_tle(constellation_id: str):
    """Generate TLE (Two-Line Element) data for constellation.
    
    This would typically interface with orbital mechanics to generate
    proper TLE format data for the constellation.
    """
    if constellation_id not in CONSTELLATION_LIBRARY:
        raise HTTPException(status_code=404, detail="Constellation not found")
    
    # Placeholder - would implement TLE generation here
    return APIResponse(
        success=True,
        message="TLE generation not yet implemented",
        data={
            "constellation_id": constellation_id,
            "note": "TLE generation will be implemented with orbital mechanics module"
        }
    )