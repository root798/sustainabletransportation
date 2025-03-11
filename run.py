import os
import subprocess
import sys

def run_model():
    """Run the ATS model to generate CSV files"""
    print("Running ATS model to generate data...")
    try:
        subprocess.run([sys.executable, "footprint_model.py"], check=True)
        print("Model execution completed successfully.")
    except subprocess.CalledProcessError:
        print("Error: Failed to run the model.")
        return False
    return True

def run_app():
    """Run the Flask web application"""
    print("Starting the web application...")
    print("The application will be available at:")
    print("  - Local:   http://localhost:8000")
    print("  - Network: http://<your-ip-address>:8000")
    try:
        # Use the updated app file
        subprocess.run([sys.executable, "app_updated.py"], check=True)
    except subprocess.CalledProcessError:
        print("Error: Failed to start the web application.")
        return False
    return True

def check_results_exist():
    """Check if results directory exists and contains CSV files"""
    if not os.path.exists("results"):
        return False
    
    csv_files = [f for f in os.listdir("results") if f.endswith(".csv")]
    return len(csv_files) > 0

if __name__ == "__main__":
    # Always regenerate the data
    print("Generating model data...")
    if not run_model():
        sys.exit(1)

    # Run the web application
    run_app()