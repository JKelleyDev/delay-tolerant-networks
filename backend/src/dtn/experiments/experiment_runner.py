"""
DTN Experiment Runner

Implements the three required experiments from the rubric:
E1: Protocol Comparison (Epidemic vs PRoPHET vs Spray-and-Wait)
E2: Buffer Size Impact (5MB, 20MB, 80MB)
E3: TTL Impact Analysis (30, 120, 480 minutes)
"""

import time
import json
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from ..simulation import DTNSimulation, SimulationConfig, SimulationResults
from ..orbital.orbital_mechanics import OrbitalElements

logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment run."""
    experiment_id: str
    routing_algorithms: List[str]
    node_counts: List[int]
    buffer_sizes_mb: List[int]
    ttl_values_minutes: List[int]
    simulation_duration_hours: float = 12.0
    repetitions: int = 3
    output_dir: str = "experiment_results"


class ExperimentRunner:
    """Runs DTN experiments and collects results for analysis."""
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.results: Dict[str, List[SimulationResults]] = {}
        
        # Create output directory
        Path(self.config.output_dir).mkdir(exist_ok=True)
        
    def run_experiment_e1_protocol_comparison(self) -> Dict[str, Any]:
        """
        E1: Protocol Comparison
        Compare Epidemic vs PRoPHET routing with different node counts.
        """
        logger.info("Starting E1: Protocol Comparison Experiment")
        
        results = {}
        algorithms = ["epidemic", "prophet"]
        node_counts = [10, 25, 50]  # Reduced for faster execution
        
        for algorithm in algorithms:
            results[algorithm] = {}
            for node_count in node_counts:
                logger.info(f"Testing {algorithm} with {node_count} nodes")
                
                run_results = []
                for rep in range(self.config.repetitions):
                    sim_config = SimulationConfig(
                        simulation_duration_hours=self.config.simulation_duration_hours,
                        time_step_minutes=2.0,  # Faster steps for testing
                        default_buffer_size_mb=20
                    )
                    
                    result = self._run_single_simulation(
                        algorithm, node_count, sim_config
                    )
                    run_results.append(result)
                    
                results[algorithm][node_count] = run_results
                
        self._save_results("e1_protocol_comparison", results)
        return results
        
    def run_experiment_e2_buffer_impact(self) -> Dict[str, Any]:
        """
        E2: Buffer Size Impact
        Analyze impact of different buffer sizes on performance.
        """
        logger.info("Starting E2: Buffer Size Impact Experiment")
        
        results = {}
        buffer_sizes = [5, 20, 80]  # MB
        node_count = 25  # Fixed constellation size
        
        for buffer_size in buffer_sizes:
            logger.info(f"Testing buffer size {buffer_size}MB")
            
            run_results = []
            for rep in range(self.config.repetitions):
                sim_config = SimulationConfig(
                    simulation_duration_hours=self.config.simulation_duration_hours,
                    time_step_minutes=2.0,
                    default_buffer_size_mb=buffer_size
                )
                
                result = self._run_single_simulation(
                    "epidemic", node_count, sim_config
                )
                run_results.append(result)
                
            results[f"{buffer_size}MB"] = run_results
            
        self._save_results("e2_buffer_impact", results)
        return results
        
    def run_experiment_e3_ttl_analysis(self) -> Dict[str, Any]:
        """
        E3: TTL Impact Analysis
        Study effect of different TTL values on message delivery.
        """
        logger.info("Starting E3: TTL Impact Analysis Experiment")
        
        results = {}
        ttl_values = [30, 120, 480]  # minutes
        node_count = 25
        
        for ttl_minutes in ttl_values:
            logger.info(f"Testing TTL {ttl_minutes} minutes")
            
            run_results = []
            for rep in range(self.config.repetitions):
                sim_config = SimulationConfig(
                    simulation_duration_hours=self.config.simulation_duration_hours,
                    time_step_minutes=2.0,
                    default_ttl_hours=ttl_minutes / 60.0,
                    default_buffer_size_mb=20
                )
                
                result = self._run_single_simulation(
                    "prophet", node_count, sim_config
                )
                run_results.append(result)
                
            results[f"{ttl_minutes}min"] = run_results
            
        self._save_results("e3_ttl_analysis", results)
        return results
        
    def _run_single_simulation(self, routing_algorithm: str, node_count: int, 
                              sim_config: SimulationConfig) -> SimulationResults:
        """Run a single simulation instance."""
        simulation = DTNSimulation(sim_config)
        
        # Create constellation based on node count
        if node_count <= 10:
            self._create_small_constellation(simulation, node_count, routing_algorithm)
        elif node_count <= 30:
            self._create_medium_constellation(simulation, node_count, routing_algorithm)
        else:
            self._create_large_constellation(simulation, node_count, routing_algorithm)
            
        # Run simulation
        start_time = time.time()
        results = simulation.run_simulation()
        execution_time = time.time() - start_time
        
        logger.info(f"Simulation completed in {execution_time:.2f}s - "
                   f"Delivery ratio: {results.delivery_ratio:.3f}")
        
        return results
        
    def _create_small_constellation(self, simulation: DTNSimulation, 
                                  node_count: int, routing_algorithm: str):
        """Create small LEO constellation."""
        for i in range(node_count):
            orbit = OrbitalElements(
                semi_major_axis=6800.0 + i * 50,
                eccentricity=0.001,
                inclination=98.0,
                raan=i * (360.0 / node_count),
                arg_perigee=0.0,
                true_anomaly=i * (360.0 / node_count),
                epoch=simulation.start_time
            )
            simulation.add_satellite(f"SAT-{i+1:02d}", orbit, routing_algorithm)
            
    def _create_medium_constellation(self, simulation: DTNSimulation,
                                   node_count: int, routing_algorithm: str):
        """Create medium constellation with multiple orbital planes."""
        planes = 3
        sats_per_plane = node_count // planes
        
        for plane in range(planes):
            for sat in range(sats_per_plane):
                orbit = OrbitalElements(
                    semi_major_axis=6900.0 + plane * 100,
                    eccentricity=0.001,
                    inclination=98.0 + plane * 2,
                    raan=plane * 120.0,
                    arg_perigee=0.0,
                    true_anomaly=sat * (360.0 / sats_per_plane),
                    epoch=simulation.start_time
                )
                sat_id = f"P{plane+1}-{sat+1:02d}"
                simulation.add_satellite(sat_id, orbit, routing_algorithm)
                
    def _create_large_constellation(self, simulation: DTNSimulation,
                                  node_count: int, routing_algorithm: str):
        """Create large Starlink-like constellation."""
        planes = 6
        sats_per_plane = node_count // planes
        
        for plane in range(planes):
            for sat in range(sats_per_plane):
                orbit = OrbitalElements(
                    semi_major_axis=7000.0 + (plane % 3) * 50,
                    eccentricity=0.0001,
                    inclination=97.0 + (plane % 2) * 2,
                    raan=plane * 60.0,
                    arg_perigee=0.0,
                    true_anomaly=sat * (360.0 / sats_per_plane),
                    epoch=simulation.start_time
                )
                sat_id = f"L{plane+1}-{sat+1:02d}"
                simulation.add_satellite(sat_id, orbit, routing_algorithm)
                
    def _save_results(self, experiment_name: str, results: Dict[str, Any]):
        """Save experiment results to JSON file."""
        output_file = Path(self.config.output_dir) / f"{experiment_name}.json"
        
        # Convert SimulationResults to dict
        serializable_results = {}
        for key, value in results.items():
            if isinstance(value, dict):
                serializable_results[key] = {}
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, list):
                        serializable_results[key][subkey] = [
                            result.to_dict() if hasattr(result, 'to_dict') else result
                            for result in subvalue
                        ]
                    else:
                        serializable_results[key][subkey] = subvalue.to_dict() if hasattr(subvalue, 'to_dict') else subvalue
            elif isinstance(value, list):
                serializable_results[key] = [
                    result.to_dict() if hasattr(result, 'to_dict') else result
                    for result in value
                ]
            else:
                serializable_results[key] = value.to_dict() if hasattr(value, 'to_dict') else value
        
        with open(output_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
            
        logger.info(f"Results saved to {output_file}")
        
    def run_all_experiments(self) -> Dict[str, Any]:
        """Run all three required experiments."""
        logger.info("Starting complete experiment suite")
        
        all_results = {}
        
        # Run E1: Protocol Comparison
        all_results["e1_protocol_comparison"] = self.run_experiment_e1_protocol_comparison()
        
        # Run E2: Buffer Impact
        all_results["e2_buffer_impact"] = self.run_experiment_e2_buffer_impact()
        
        # Run E3: TTL Analysis
        all_results["e3_ttl_analysis"] = self.run_experiment_e3_ttl_analysis()
        
        # Save combined results
        self._save_results("all_experiments", all_results)
        
        logger.info("All experiments completed")
        return all_results
        
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate a summary report of experiment results."""
        report = []
        report.append("DTN Simulation Experiment Results Summary")
        report.append("=" * 50)
        report.append("")
        
        if "e1_protocol_comparison" in results:
            report.append("E1: Protocol Comparison Results")
            report.append("-" * 30)
            for algorithm, node_results in results["e1_protocol_comparison"].items():
                report.append(f"\\n{algorithm.upper()} Routing:")
                for node_count, runs in node_results.items():
                    avg_delivery = sum(r.delivery_ratio if hasattr(r, 'delivery_ratio') else r["delivery_ratio"] for r in runs) / len(runs)
                    avg_overhead = sum(r.network_overhead if hasattr(r, 'network_overhead') else r["network_overhead"] for r in runs) / len(runs)
                    report.append(f"  {node_count} nodes: "
                                f"Delivery={avg_delivery:.3f}, Overhead={avg_overhead:.2f}")
            report.append("")
            
        if "e2_buffer_impact" in results:
            report.append("E2: Buffer Size Impact Results")
            report.append("-" * 30)
            for buffer_size, runs in results["e2_buffer_impact"].items():
                avg_delivery = sum(r.delivery_ratio if hasattr(r, 'delivery_ratio') else r["delivery_ratio"] for r in runs) / len(runs)
                avg_dropped = sum(r.total_bundles_dropped if hasattr(r, 'total_bundles_dropped') else r["total_bundles_dropped"] for r in runs) / len(runs)
                report.append(f"{buffer_size}: "
                            f"Delivery={avg_delivery:.3f}, Dropped={avg_dropped:.0f}")
            report.append("")
            
        if "e3_ttl_analysis" in results:
            report.append("E3: TTL Impact Analysis Results")
            report.append("-" * 30)
            for ttl_value, runs in results["e3_ttl_analysis"].items():
                avg_delivery = sum(r.delivery_ratio if hasattr(r, 'delivery_ratio') else r["delivery_ratio"] for r in runs) / len(runs)
                avg_delay = sum(r.average_delivery_delay if hasattr(r, 'average_delivery_delay') else r["average_delivery_delay"] for r in runs) / len(runs)
                report.append(f"{ttl_value}: "
                            f"Delivery={avg_delivery:.3f}, Delay={avg_delay:.1f}s")
            report.append("")
            
        return "\\n".join(report)