import os
import subprocess
import sys
import logging
import socket
from pathlib import Path

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
    required_configs = ["common.json", "california.json", "ohio.json", "us_average.json"]
    
    if not config_dir.exists():
        logger.error(f"Config directory '{config_dir}' does not exist.")
        return False
    
    missing = [cfg for cfg in required_configs if not (config_dir / cfg).exists()]
    if missing:
        logger.error(f"Missing configuration files: {', '.join(missing)}")
        return False
    
    logger.info("All required configuration files found.")
    return True

def run_model():
    """Run the ATS model to generate CSV files."""
    logger.info("Generating model data by running ATS model...")
    model_script = Path("footprint_model.py")
    
    if not model_script.exists():
        logger.error(f"Model script '{model_script}' not found.")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(model_script)],
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
    app_script = Path("app_updated.py")

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
    """Main execution flow."""
    # Check for config files first
    if not check_configs_exist():
        logger.error("Aborting due to missing configuration files.")
        sys.exit(1)

    # Run the model
    if not run_model():
        logger.error("Aborting due to model execution failure.")
        sys.exit(1)

    # Verify results
    if not check_results_exist():
        logger.warning("Model ran but no results were generated. Proceeding anyway.")

    # Run the Flask app
    if not run_app():
        logger.error("Web application failed to start.")
        sys.exit(1)

    logger.info("Execution completed successfully.")

if __name__ == "__main__":
    main()