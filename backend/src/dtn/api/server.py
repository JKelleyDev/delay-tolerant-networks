"""
DTN API Server

Flask web server providing REST API for frontend communication.
Separated from simulation logic for better architecture.
"""

import time
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

from ..orbital.orbital_mechanics import OrbitalMechanics, OrbitalElements
from ..orbital.satellite_loader import SatelliteLoader, GroundStation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    CORS(app)
    
    # Initialize orbital mechanics calculator and satellite loader
    orbital_calc = OrbitalMechanics()
    satellite_loader = SatelliteLoader()
    
    # Create default constellation
    satellite_loader.create_default_constellation()
    
    # Global time speed multiplier for simulation
    time_speed_multiplier = 120.0
    
    @app.route("/api/satellites")
    def get_satellites():
        """Get current satellite positions."""
        try:
            result = []
            current_time = time.time()
            
            # Get speed multiplier from request or global setting
            speed_multiplier = float(request.args.get('speed', str(time_speed_multiplier)))
            
            # Get satellites from loader
            satellites = satellite_loader.get_all_satellites()
            
            for sat_name, sat_data in satellites.items():
                try:
                    # Apply time acceleration for more dynamic visualization
                    accelerated_time = current_time * speed_multiplier
                    
                    # Propagate orbit to accelerated time
                    state = orbital_calc.propagate_orbit(sat_data["elements"], accelerated_time)
                    
                    result.append({
                        "name": sat_name,
                        "x": state.position.x,
                        "y": state.position.y, 
                        "z": state.position.z,
                        "ref": sat_data["ref"],
                        "frame": "ECI",
                        "timestamp": current_time,
                        "source": sat_data.get("source", "unknown")
                    })
                except Exception as e:
                    logger.warning(f"Failed to propagate orbit for {sat_name}: {e}")
                    
            logger.info(f"Returned {len(result)} satellite positions")
            return jsonify({
                "satellites": result,
                "timestamp": current_time,
                "speed_multiplier": speed_multiplier
            })
            
        except Exception as e:
            logger.error(f"Error in get_satellites: {e}")
            return jsonify({"error": "Failed to fetch satellite data"}), 500
    
    @app.route("/api/health")
    def health():
        """Health check endpoint."""
        try:
            satellites = satellite_loader.get_all_satellites()
            return jsonify({
                "status": "ok", 
                "satellites": len(satellites),
                "time": time.time(),
                "version": "0.1.0"
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error"}), 500
    
    @app.route("/api/run-simulation")
    def run_simulation():
        """Run a quick DTN simulation demonstration."""
        try:
            from ..simulation import DTNSimulation, SimulationConfig
            from ..experiments.experiment_runner import ExperimentRunner, ExperimentConfig
            
            # Quick simulation for demo
            sim_config = SimulationConfig(
                simulation_duration_hours=1.0,  # Short demo
                time_step_minutes=5.0,
                bundle_generation_rate_per_hour=20
            )
            
            simulation = DTNSimulation(sim_config)
            simulation.create_default_constellation()
            
            results = simulation.run_simulation()
            
            return jsonify({
                "status": "completed",
                "results": results.to_dict(),
                "summary": {
                    "delivery_ratio": f"{results.delivery_ratio:.3f}",
                    "total_nodes": len(simulation.nodes),
                    "bundles_created": results.total_bundles_created,
                    "bundles_delivered": results.total_bundles_delivered,
                    "network_overhead": f"{results.network_overhead:.2f}"
                }
            })
            
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            return jsonify({"error": f"Simulation failed: {str(e)}"}), 500
    
    @app.route("/api/run-experiments", methods=["GET", "POST"])
    def run_experiments():
        """Run configurable DTN experiments."""
        try:
            # Get parameters from request or use defaults
            if request.method == "POST":
                params = request.get_json() or {}
            else:
                params = request.args.to_dict()
            
            # Parse experiment parameters
            algorithms = params.get("algorithms", "epidemic,prophet").split(",")
            node_counts = [int(x) for x in params.get("node_counts", "5,10").split(",")]
            buffer_sizes = [int(x) for x in params.get("buffer_sizes", "10,20").split(",")]
            ttl_minutes = [int(x) for x in params.get("ttl_minutes", "60,120").split(",")]
            duration_hours = float(params.get("duration_hours", "0.1"))
            bundle_rate = int(params.get("bundle_rate", "30"))
            
            from ..experiments.experiment_runner import ExperimentRunner, ExperimentConfig
            
            config = ExperimentConfig(
                experiment_id=f"api_exp_{int(time.time())}",
                routing_algorithms=algorithms,
                node_counts=node_counts,
                buffer_sizes_mb=buffer_sizes,
                ttl_values_minutes=ttl_minutes,
                simulation_duration_hours=duration_hours,
                repetitions=1,
                output_dir="experiment_results"
            )
            
            runner = ExperimentRunner(config)
            
            # Run just E1 for speed, or all if requested
            run_all = params.get("run_all", "false").lower() == "true"
            
            if run_all:
                results = runner.run_all_experiments()
            else:
                results = {"e1_protocol_comparison": runner.run_experiment_e1_protocol_comparison()}
            
            summary = runner.generate_summary_report(results)
            
            return jsonify({
                "status": "completed",
                "summary": summary,
                "parameters_used": {
                    "algorithms": algorithms,
                    "node_counts": node_counts,
                    "buffer_sizes": buffer_sizes,
                    "ttl_minutes": ttl_minutes,
                    "duration_hours": duration_hours,
                    "bundle_rate": bundle_rate
                },
                "detailed_results_saved": True
            })
            
        except Exception as e:
            logger.error(f"Experiments failed: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Experiments failed: {str(e)}"}), 500
    
    @app.route("/api/constellation-info")
    def constellation_info():
        """Get information about current satellite constellation."""
        try:
            # Get current satellite data
            current_time = time.time()
            result = []
            satellites = satellite_loader.get_all_satellites()
            
            for sat_name, sat_data in satellites.items():
                try:
                    state = orbital_calc.propagate_orbit(sat_data["elements"], current_time)
                    
                    # Calculate orbital period
                    period_seconds = orbital_calc.calculate_orbital_period(sat_data["elements"].semi_major_axis)
                    
                    # Calculate altitude (distance from surface)
                    if sat_data["ref"].upper() == "MARS":
                        surface_radius = 3390  # Mars radius
                    else:
                        surface_radius = 6371  # Earth radius
                        
                    altitude_km = sat_data["elements"].semi_major_axis - surface_radius
                    
                    result.append({
                        "name": sat_name,
                        "orbital_period_minutes": period_seconds / 60,
                        "altitude_km": altitude_km,
                        "inclination_deg": sat_data["elements"].inclination,
                        "eccentricity": sat_data["elements"].eccentricity,
                        "reference_body": sat_data["ref"],
                        "source": sat_data.get("source", "unknown"),
                        "current_position": {
                            "x": state.position.x,
                            "y": state.position.y,
                            "z": state.position.z
                        }
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to get info for {sat_name}: {e}")
                    
            return jsonify({
                "constellation": result,
                "total_satellites": len(result),
                "constellation_types": {
                    "LEO": len([s for s in result if s["altitude_km"] < 2000 and s["reference_body"] != "MARS"]),
                    "MEO": len([s for s in result if 2000 <= s["altitude_km"] < 35000 and s["reference_body"] != "MARS"]),
                    "GEO": len([s for s in result if s["altitude_km"] >= 35000 and s["reference_body"] != "MARS"]),
                    "MARS": len([s for s in result if s["reference_body"] == "MARS"])
                },
                "ground_stations": {
                    "total": len(satellite_loader.get_all_ground_stations()),
                    "earth": len(satellite_loader.get_ground_stations_by_planet("Earth")),
                    "mars": len(satellite_loader.get_ground_stations_by_planet("Mars"))
                }
            })
            
        except Exception as e:
            logger.error(f"Constellation info failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/satellites/add", methods=["POST"])
    def add_satellite():
        """Add a new satellite manually."""
        try:
            data = request.get_json()
            
            success = satellite_loader.add_satellite_manual(
                name=data["name"],
                semi_major_axis_km=float(data["semi_major_axis_km"]),
                eccentricity=float(data["eccentricity"]),
                inclination_deg=float(data["inclination_deg"]),
                raan_deg=float(data["raan_deg"]),
                arg_perigee_deg=float(data["arg_perigee_deg"]),
                true_anomaly_deg=float(data["true_anomaly_deg"]),
                reference_body=data.get("reference_body", "Earth"),
                epoch_unix=float(data.get("epoch_unix", time.time()))
            )
            
            if success:
                return jsonify({"status": "success", "message": f"Satellite {data['name']} added"})
            else:
                return jsonify({"error": "Failed to add satellite"}), 400
                
        except Exception as e:
            logger.error(f"Error adding satellite: {e}")
            return jsonify({"error": str(e)}), 400
    
    @app.route("/api/satellites/load-csv", methods=["POST"])
    def load_satellites_csv():
        """Load satellites from uploaded CSV file."""
        try:
            if 'file' not in request.files:
                return jsonify({"error": "No file uploaded"}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
                
            # Save uploaded file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as tmp:
                file.save(tmp.name)
                satellites = satellite_loader.load_satellites_from_csv(tmp.name)
                
            return jsonify({
                "status": "success",
                "message": f"Loaded {len(satellites)} satellites from CSV",
                "satellites": list(satellites.keys())
            })
            
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return jsonify({"error": str(e)}), 400
    
    @app.route("/api/ground-stations")
    def get_ground_stations():
        """Get all ground stations."""
        try:
            stations = satellite_loader.get_all_ground_stations()
            result = []
            
            for name, station in stations.items():
                station_data = station.to_dict()
                station_data["id"] = name
                result.append(station_data)
                
            return jsonify({
                "ground_stations": result,
                "total": len(result)
            })
            
        except Exception as e:
            logger.error(f"Error getting ground stations: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/ground-stations/add", methods=["POST"])
    def add_ground_station():
        """Add a new ground station."""
        try:
            data = request.get_json()
            
            success = satellite_loader.add_ground_station_manual(
                name=data["name"],
                latitude=float(data["latitude"]),
                longitude=float(data["longitude"]),
                altitude_km=float(data.get("altitude_km", 0.0)),
                planet=data.get("planet", "Earth"),
                antenna_gain_db=float(data.get("antenna_gain_db", 30.0)),
                max_data_rate_bps=int(data.get("max_data_rate_bps", 1000000))
            )
            
            if success:
                return jsonify({"status": "success", "message": f"Ground station {data['name']} added"})
            else:
                return jsonify({"error": "Failed to add ground station"}), 400
                
        except Exception as e:
            logger.error(f"Error adding ground station: {e}")
            return jsonify({"error": str(e)}), 400
    
    @app.route("/api/time-speed", methods=["GET", "POST"])
    def time_speed_control():
        """Get or set simulation time speed multiplier."""
        nonlocal time_speed_multiplier
        
        if request.method == "POST":
            try:
                data = request.get_json()
                new_speed = float(data.get("speed", time_speed_multiplier))
                time_speed_multiplier = max(0.1, min(10000.0, new_speed))  # Clamp between 0.1x and 10000x
                
                return jsonify({
                    "status": "success",
                    "speed_multiplier": time_speed_multiplier
                })
                
            except Exception as e:
                return jsonify({"error": str(e)}), 400
        else:
            return jsonify({"speed_multiplier": time_speed_multiplier})
    
    @app.route("/api/constellation/export")
    def export_constellation():
        """Export current constellation configuration."""
        try:
            config = satellite_loader.to_json()
            return jsonify({
                "status": "success",
                "configuration": config,
                "satellites_count": len(config["satellites"]),
                "ground_stations_count": len(config["ground_stations"])
            })
            
        except Exception as e:
            logger.error(f"Error exporting constellation: {e}")
            return jsonify({"error": str(e)}), 500
    
    return app


def main():
    """Run the API server."""
    app = create_app()
    
    print("=" * 60)
    print("🛰  DTN Satellite API Server")  
    print("=" * 60)
    print("GET  /api/health        -> status")
    print("GET  /api/satellites    -> positions (ECI km)")
    print("Note: 'ref' == 'MARS' will render near your Mars mesh.")
    print("=" * 60)
    
    app.run(host="127.0.0.1", port=5001, debug=True)


if __name__ == "__main__":
    main()