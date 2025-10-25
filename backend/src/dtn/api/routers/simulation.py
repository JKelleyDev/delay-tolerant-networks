"""
Simulation Control Router

Handles simulation lifecycle management including create, start, stop, pause.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
import logging

from ..models.base_models import (
    APIResponse, SimulationConfig, SimulationStatus, 
    NetworkMetrics, SatelliteInfo, GroundStationInfo
)
from ...core.simulation import SimulationManager, Simulation

logger = logging.getLogger(__name__)
router = APIRouter()


def get_simulation_manager() -> SimulationManager:
    """Dependency to get simulation manager."""
    # This will be injected by the main app
    return SimulationManager()


@router.post("/create", response_model=APIResponse)
async def create_simulation(
    config: SimulationConfig,
    background_tasks: BackgroundTasks,
    sim_manager: SimulationManager = Depends(get_simulation_manager)
):
    """Create a new simulation."""
    try:
        simulation_id = await sim_manager.create_simulation(config)
        
        return APIResponse(
            success=True,
            message="Simulation created successfully",
            data={
                "simulation_id": simulation_id,
                "status": SimulationStatus.CREATED,
                "config": config.dict()
            }
        )
    except Exception as e:
        logger.error(f"Failed to create simulation: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list", response_model=APIResponse)
async def list_simulations(
    sim_manager: SimulationManager = Depends(get_simulation_manager)
):
    """List all simulations."""
    try:
        simulations = await sim_manager.list_simulations()
        return APIResponse(
            success=True,
            message="Simulations retrieved successfully",
            data={"simulations": simulations}
        )
    except Exception as e:
        logger.error(f"Failed to list simulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{simulation_id}", response_model=APIResponse)
async def get_simulation(
    simulation_id: str,
    sim_manager: SimulationManager = Depends(get_simulation_manager)
):
    """Get simulation details."""
    try:
        simulation = await sim_manager.get_simulation(simulation_id)
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return APIResponse(
            success=True,
            message="Simulation retrieved successfully",
            data=simulation.to_dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{simulation_id}/start", response_model=APIResponse)
async def start_simulation(
    simulation_id: str,
    background_tasks: BackgroundTasks,
    sim_manager: SimulationManager = Depends(get_simulation_manager)
):
    """Start a simulation."""
    try:
        success = await sim_manager.start_simulation(simulation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return APIResponse(
            success=True,
            message="Simulation started successfully",
            data={"simulation_id": simulation_id, "status": SimulationStatus.RUNNING}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{simulation_id}/pause", response_model=APIResponse)
async def pause_simulation(
    simulation_id: str,
    sim_manager: SimulationManager = Depends(get_simulation_manager)
):
    """Pause a simulation."""
    try:
        success = await sim_manager.pause_simulation(simulation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return APIResponse(
            success=True,
            message="Simulation paused successfully",
            data={"simulation_id": simulation_id, "status": SimulationStatus.PAUSED}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{simulation_id}/stop", response_model=APIResponse)
async def stop_simulation(
    simulation_id: str,
    sim_manager: SimulationManager = Depends(get_simulation_manager)
):
    """Stop a simulation."""
    try:
        success = await sim_manager.stop_simulation(simulation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return APIResponse(
            success=True,
            message="Simulation stopped successfully",
            data={"simulation_id": simulation_id, "status": SimulationStatus.STOPPED}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{simulation_id}", response_model=APIResponse)
async def delete_simulation(
    simulation_id: str,
    sim_manager: SimulationManager = Depends(get_simulation_manager)
):
    """Delete a simulation."""
    try:
        success = await sim_manager.delete_simulation(simulation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return APIResponse(
            success=True,
            message="Simulation deleted successfully",
            data={"simulation_id": simulation_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{simulation_id}/status", response_model=APIResponse)
async def get_simulation_status(
    simulation_id: str,
    sim_manager: SimulationManager = Depends(get_simulation_manager)
):
    """Get current simulation status."""
    try:
        status = await sim_manager.get_simulation_status(simulation_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return APIResponse(
            success=True,
            message="Status retrieved successfully",
            data=status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{simulation_id}/metrics", response_model=APIResponse)
async def get_simulation_metrics(
    simulation_id: str,
    sim_manager: SimulationManager = Depends(get_simulation_manager)
):
    """Get current simulation metrics."""
    try:
        metrics = await sim_manager.get_simulation_metrics(simulation_id)
        if metrics is None:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return APIResponse(
            success=True,
            message="Metrics retrieved successfully",
            data=metrics
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{simulation_id}/satellites", response_model=APIResponse)
async def get_satellites(
    simulation_id: str,
    sim_manager: SimulationManager = Depends(get_simulation_manager)
):
    """Get current satellite positions and status."""
    try:
        satellites = await sim_manager.get_satellite_info(simulation_id)
        if satellites is None:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return APIResponse(
            success=True,
            message="Satellite information retrieved successfully",
            data={"satellites": satellites}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get satellites for simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{simulation_id}/ground_stations", response_model=APIResponse)
async def get_ground_stations(
    simulation_id: str,
    sim_manager: SimulationManager = Depends(get_simulation_manager)
):
    """Get ground station information."""
    try:
        ground_stations = await sim_manager.get_ground_station_info(simulation_id)
        if ground_stations is None:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return APIResponse(
            success=True,
            message="Ground station information retrieved successfully",
            data={"ground_stations": ground_stations}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ground stations for simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))