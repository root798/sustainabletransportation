import os
import subprocess
import sys
import logging
import socket
import argparse
from typing import Optional, List
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_configs_exist():
    """Check if required configuration files exist in the configs directory."""
    config_dir = Path("configs")
    required_configs = ["california.json", "ohio.json", "us_average.json"]
    
    if not config_dir.exists():
        logger.error(f"Config directory '{config_dir}' does not exist.")
        return False
    
    missing = [cfg for cfg in required_configs if not (config_dir / cfg).exists()]
    if missing:
        logger.error(f"Missing configuration files: {', '.join(missing)}")
        return False
    
    logger.info("All required configuration files found.")
    return True

def run_model(mc: int = 0, policy: str = "baseline", seed: int = 0, scenarios: Optional[List[str]] = None, years: Optional[int] = None):
    """Run the ATS model to generate CSV files."""
    logger.info("Generating model data by running ATS model...")
    model_script = Path("footprint_model.py")
    
    if not model_script.exists():
        logger.error(f"Model script '{model_script}' not found.")
        return False
    
    try:
        cmd = [sys.executable, str(model_script)]
        if scenarios:
            cmd += ["--scenarios"] + scenarios
        if years is not None:
            cmd += ["--years", str(years)]
        if mc and mc > 0:
            cmd += ["--mc", str(mc)]
        if policy:
            cmd += ["--policy", policy]
        if seed is not None:
            cmd += ["--seed", str(seed)]

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Model execution completed successfully.")
        logger.debug(f"Model output:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Model warnings/errors:\n{result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run the model. Exit code: {e.returncode}")
        logger.error(f"Error output:\n{e.stderr}")
        return False

def get_network_ip():
    """Get the local network IP address for Flask app access."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Use Google's DNS to get local IP
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.warning(f"Could not determine network IP: {e}")
        return "unknown"

def run_app():
    """Run the Flask web application."""
    app_script = Path("app.py")

    if not app_script.exists():
        logger.error(f"Web app script '{app_script}' not found.")
        return False

    network_ip = get_network_ip()
    port = 8000

    logger.info("Starting the web application...")
    logger.info(f"The application will be available at:")
    logger.info(f"  - Local:   http://localhost:{port}")
    logger.info(f"  - Network: http://{network_ip}:{port}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(app_script)],
            check=True,
            capture_output=True,
            text=True
        )
        logger.debug(f"App output:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"App warnings/errors:\n{result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start the web application. Exit code: {e.returncode}")
        logger.error(f"Error output:\n{e.stderr}")
        return False

def check_results_exist():
    """Check if results directory exists and contains CSV files."""
    results_dir = Path("results")
    if not results_dir.exists():
        logger.warning(f"Results directory '{results_dir}' does not exist.")
        return False
    
    csv_files = list(results_dir.glob("*.csv"))
    if not csv_files:
        logger.warning(f"No CSV files found in '{results_dir}'.")
        return False
    
    logger.info(f"Found {len(csv_files)} CSV files in '{results_dir}'.")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-app", action="store_true", help="Run model only, do not start Flask app.")
    parser.add_argument("--mc", type=int, default=0)
    parser.add_argument("--policy", type=str, default="baseline")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--scenarios", nargs="*", default=None)
    parser.add_argument("--years", type=int, default=None)
    args = parser.parse_args()

    if not check_configs_exist():
        logger.error("Aborting due to missing configuration files.")
        sys.exit(1)

    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    if not run_model(mc=args.mc, policy=args.policy, seed=args.seed, scenarios=args.scenarios, years=args.years):
        logger.error("Aborting due to model execution failure.")
        sys.exit(1)

    if not check_results_exist():
        logger.error("Model ran but no results were generated. Cannot proceed without results files.")
        sys.exit(1)

    if not args.no_app:
        if not run_app():
            logger.error("Web application failed to start.")
            sys.exit(1)
    else:
        logger.info("Skipping web app (--no-app).")

    logger.info("Execution completed successfully.")


if __name__ == "__main__":
    main()
