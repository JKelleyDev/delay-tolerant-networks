"""
Main entry point for DTN Simulator backend.

Run with: python -m src.main
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from dtn.api.app import run_server

if __name__ == "__main__":
    print("Starting DTN Simulator Backend...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    
    run_server(
        host="0.0.0.0",
        port=8000,
        reload=True
    )