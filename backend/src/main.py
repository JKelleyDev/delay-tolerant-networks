"""
Main entry point for DTN simulation.

This module provides the primary interface for running DTN simulations,
experiments, and the web API server.
"""

import argparse
import sys
from typing import Optional

from dtn.api.server import main as api_main
from dtn.orbital.orbital_mechanics import OrbitalMechanics, OrbitalElements
from dtn.experiments.experiment_data import ExperimentDataCollector


def run_simulation():
    """Run a basic DTN simulation."""
    print("=ð  Running DTN Simulation...")
    
    # Initialize orbital mechanics
    orbital_calc = OrbitalMechanics()
    
    # Create sample satellite constellation
    satellites = [
        OrbitalElements(
            semi_major_axis=6793.0,  # ISS-like orbit
            eccentricity=0.0003,
            inclination=51.6,
            raan=180.0,
            arg_perigee=90.0,
            true_anomaly=0.0,
            epoch=0.0,
        ),
        OrbitalElements(
            semi_major_axis=26560.0,  # GPS-like orbit  
            eccentricity=0.01,
            inclination=55.0,
            raan=90.0,
            arg_perigee=45.0,
            true_anomaly=30.0,
            epoch=0.0,
        )
    ]
    
    # Run basic orbital calculations
    for i, sat in enumerate(satellites):
        period = orbital_calc.calculate_orbital_period(sat.semi_major_axis)
        print(f"Satellite {i+1}: Period = {period/60:.1f} minutes")
    
    print(" Simulation complete!")


def run_api_server():
    """Run the web API server."""
    print("< Starting API server...")
    api_main()


def run_experiments():
    """Run DTN experiments."""
    print(">ê Running DTN experiments...")
    # TODO: Implement experiment runner
    print("   Experiments not yet implemented")


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="DTN Satellite Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py sim          # Run basic simulation
  python main.py api          # Start API server
  python main.py experiments  # Run experiments
        """
    )
    
    parser.add_argument(
        "command",
        choices=["sim", "api", "experiments"],
        help="Command to run"
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == "sim":
            run_simulation()
        elif args.command == "api":
            run_api_server()
        elif args.command == "experiments":
            run_experiments()
    except KeyboardInterrupt:
        print("\n=K Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"L Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()