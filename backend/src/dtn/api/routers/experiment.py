"""
Experiment Management Router

Handles experiment configuration, execution, and results analysis.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime

from ..models.base_models import (
    APIResponse, ExperimentConfig, RoutingAlgorithm, 
    NetworkMetrics, SimulationConfig
)

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory experiment storage (would use database in production)
experiments: Dict[str, Dict[str, Any]] = {}


@router.post("/create", response_model=APIResponse)
async def create_experiment(
    config: ExperimentConfig,
    background_tasks: BackgroundTasks
):
    """Create a new experiment."""
    try:
        experiment_id = str(uuid.uuid4())
        
        experiment = {
            "id": experiment_id,
            "config": config.dict(),
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "simulations": [],
            "results": None
        }
        
        experiments[experiment_id] = experiment
        
        # Schedule experiment execution in background
        background_tasks.add_task(execute_experiment, experiment_id)
        
        return APIResponse(
            success=True,
            message="Experiment created successfully",
            data={
                "experiment_id": experiment_id,
                "status": "created",
                "algorithms": config.routing_algorithms,
                "constellation": config.constellation_id
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create experiment: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list", response_model=APIResponse)
async def list_experiments():
    """List all experiments."""
    experiment_list = []
    for exp_id, exp_data in experiments.items():
        experiment_list.append({
            "id": exp_id,
            "name": exp_data["config"]["name"],
            "status": exp_data["status"],
            "created_at": exp_data["created_at"],
            "algorithms": exp_data["config"]["routing_algorithms"],
            "constellation": exp_data["config"]["constellation_id"]
        })
    
    return APIResponse(
        success=True,
        message="Experiments retrieved successfully",
        data={"experiments": experiment_list}
    )


@router.get("/{experiment_id}", response_model=APIResponse)
async def get_experiment(experiment_id: str):
    """Get experiment details."""
    if experiment_id not in experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment = experiments[experiment_id]
    return APIResponse(
        success=True,
        message="Experiment retrieved successfully",
        data=experiment
    )


@router.get("/{experiment_id}/status", response_model=APIResponse)
async def get_experiment_status(experiment_id: str):
    """Get experiment execution status."""
    if experiment_id not in experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment = experiments[experiment_id]
    
    status_data = {
        "id": experiment_id,
        "status": experiment["status"],
        "simulation_count": len(experiment["simulations"]),
        "completed_simulations": len([
            s for s in experiment["simulations"] 
            if s.get("status") == "completed"
        ])
    }
    
    return APIResponse(
        success=True,
        message="Status retrieved successfully",
        data=status_data
    )


@router.get("/{experiment_id}/results", response_model=APIResponse)
async def get_experiment_results(experiment_id: str):
    """Get experiment results and analysis."""
    if experiment_id not in experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment = experiments[experiment_id]
    
    if experiment["status"] != "completed":
        return APIResponse(
            success=False,
            message="Experiment not yet completed",
            data={"status": experiment["status"]}
        )
    
    return APIResponse(
        success=True,
        message="Results retrieved successfully",
        data=experiment["results"]
    )


@router.get("/{experiment_id}/metrics", response_model=APIResponse)
async def get_experiment_metrics(experiment_id: str):
    """Get detailed performance metrics for experiment."""
    if experiment_id not in experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment = experiments[experiment_id]
    
    # Calculate metrics from simulation results
    metrics_data = calculate_experiment_metrics(experiment)
    
    return APIResponse(
        success=True,
        message="Metrics retrieved successfully",
        data=metrics_data
    )


@router.post("/{experiment_id}/export", response_model=APIResponse)
async def export_experiment_results(
    experiment_id: str,
    format: str = "csv"
):
    """Export experiment results in specified format."""
    if experiment_id not in experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    if format not in ["csv", "json", "xlsx"]:
        raise HTTPException(status_code=400, detail="Unsupported export format")
    
    experiment = experiments[experiment_id]
    
    if experiment["status"] != "completed":
        return APIResponse(
            success=False,
            message="Cannot export incomplete experiment",
            data={"status": experiment["status"]}
        )
    
    # Generate export data (placeholder)
    export_data = {
        "experiment_id": experiment_id,
        "format": format,
        "download_url": f"/api/v2/experiment/{experiment_id}/download/{format}",
        "note": "Export functionality to be implemented"
    }
    
    return APIResponse(
        success=True,
        message=f"Export prepared in {format} format",
        data=export_data
    )


@router.delete("/{experiment_id}", response_model=APIResponse)
async def delete_experiment(experiment_id: str):
    """Delete an experiment."""
    if experiment_id not in experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    experiment = experiments[experiment_id]
    
    # Stop experiment if running
    if experiment["status"] == "running":
        experiment["status"] = "cancelled"
    
    del experiments[experiment_id]
    
    return APIResponse(
        success=True,
        message="Experiment deleted successfully",
        data={"experiment_id": experiment_id}
    )


async def execute_experiment(experiment_id: str):
    """Execute experiment by running simulations for each algorithm."""
    try:
        experiment = experiments[experiment_id]
        config = ExperimentConfig(**experiment["config"])
        
        experiment["status"] = "running"
        experiment["started_at"] = datetime.now().isoformat()
        
        simulation_results = []
        
        # Run simulation for each routing algorithm
        for algorithm in config.routing_algorithms:
            logger.info(f"Running simulation for algorithm: {algorithm}")
            
            # Create simulation config
            sim_config = SimulationConfig(
                name=f"{config.name}_{algorithm}",
                constellation_id=config.constellation_id,
                routing_algorithm=algorithm,
                duration=config.duration,
                ground_stations=["gs_la", "gs_tokyo"]  # Default ground stations
            )
            
            # Simulate running the simulation (placeholder)
            # In real implementation, this would create and run actual simulations
            simulation_result = {
                "algorithm": algorithm,
                "status": "completed",
                "metrics": {
                    "delivery_ratio": 0.85 + (hash(algorithm) % 100) / 1000,  # Mock data
                    "average_delay": 120 + (hash(algorithm) % 60),
                    "hop_count_avg": 3 + (hash(algorithm) % 3),
                    "network_overhead": 0.1 + (hash(algorithm) % 50) / 1000,
                    "bundles_generated": 1000,
                    "bundles_delivered": int(850 + (hash(algorithm) % 100)),
                    "bundles_expired": int(50 + (hash(algorithm) % 20))
                }
            }
            simulation_results.append(simulation_result)
        
        # Analyze results
        experiment["simulations"] = simulation_results
        experiment["results"] = analyze_experiment_results(simulation_results)
        experiment["status"] = "completed"
        experiment["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"Experiment {experiment_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Experiment {experiment_id} failed: {e}")
        experiment["status"] = "error"
        experiment["error"] = str(e)


def analyze_experiment_results(simulation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze experiment results and generate insights."""
    
    # Calculate comparative metrics
    algorithms = [result["algorithm"] for result in simulation_results]
    delivery_ratios = [result["metrics"]["delivery_ratio"] for result in simulation_results]
    delays = [result["metrics"]["average_delay"] for result in simulation_results]
    
    # Find best performing algorithm
    best_delivery_idx = delivery_ratios.index(max(delivery_ratios))
    best_delay_idx = delays.index(min(delays))
    
    analysis = {
        "summary": {
            "algorithms_tested": len(algorithms),
            "best_delivery_algorithm": algorithms[best_delivery_idx],
            "best_delay_algorithm": algorithms[best_delay_idx],
            "avg_delivery_ratio": sum(delivery_ratios) / len(delivery_ratios),
            "avg_delay": sum(delays) / len(delays)
        },
        "comparative_results": simulation_results,
        "insights": [
            f"{algorithms[best_delivery_idx]} achieved highest delivery ratio: {delivery_ratios[best_delivery_idx]:.3f}",
            f"{algorithms[best_delay_idx]} achieved lowest average delay: {delays[best_delay_idx]:.1f}s",
            f"Delivery ratio variance: {max(delivery_ratios) - min(delivery_ratios):.3f}",
            f"Delay variance: {max(delays) - min(delays):.1f}s"
        ]
    }
    
    return analysis


def calculate_experiment_metrics(experiment: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate detailed metrics for an experiment."""
    if not experiment.get("simulations"):
        return {"error": "No simulation data available"}
    
    metrics = {
        "algorithm_comparison": {},
        "statistical_analysis": {},
        "performance_trends": {}
    }
    
    for sim in experiment["simulations"]:
        algorithm = sim["algorithm"]
        sim_metrics = sim["metrics"]
        
        metrics["algorithm_comparison"][algorithm] = sim_metrics
    
    return metrics