import os
import json
import pandas as pd
import numpy as np
import tempfile
import time
import datetime
import threading
from flask import Flask, render_template, request, jsonify
from footprint_model import TransportModel, load_config
import sys

app = Flask(__name__)

# Create cache directory for simulation results
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Dictionary to track the latest simulation ID for each state
latest_simulations = {}

# Function to clean up old simulations, keeping only the latest for each state
def cleanup_old_simulations():
    """Remove all simulation files except the latest for each state."""
    try:
        # Get all simulation files
        simulation_files = {}
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(CACHE_DIR, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if 'state' in data and 'timestamp' in data:
                            state = data['state']
                            timestamp = data['timestamp']
                            simulation_id = data['simulation_id']

                            if state not in simulation_files:
                                simulation_files[state] = []

                            simulation_files[state].append({
                                'id': simulation_id,
                                'path': file_path,
                                'timestamp': timestamp
                            })
                except Exception as e:
                    print(f"Error reading simulation file {filename}: {str(e)}")
                    continue

        # Keep only the latest simulation for each state
        for state, simulations in simulation_files.items():
            if len(simulations) <= 1:
                continue

            # Sort by timestamp (newest first)
            simulations.sort(key=lambda x: x['timestamp'], reverse=True)

            # Keep the latest simulation ID
            latest_simulations[state] = simulations[0]['id']

            # Remove all other simulations
            for sim in simulations[1:]:
                try:
                    os.remove(sim['path'])
                    print(f"Removed old simulation for {state}: {sim['id']}")
                except Exception as e:
                    print(f"Error removing simulation file: {str(e)}")

    except Exception as e:
        print(f"Error in cleanup_old_simulations: {str(e)}")

# Function to clean up simulations for a specific state
def cleanup_state_simulations(state, keep_simulation_id=None):
    """Remove all simulation files for a state except the specified one."""
    try:
        count = 0
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(CACHE_DIR, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if data.get('state') == state and data.get('simulation_id') != keep_simulation_id:
                            os.remove(file_path)
                            count += 1
                            print(f"Removed old simulation for {state}: {data.get('simulation_id')}")
                except Exception as e:
                    print(f"Error processing file {filename}: {str(e)}")
                    continue
        return count
    except Exception as e:
        print(f"Error in cleanup_state_simulations: {str(e)}")
        return 0

# Run cache cleanup on startup
cleanup_old_simulations()

# Schedule periodic cache cleanup
def schedule_cache_cleanup():
    """Run cache cleanup every hour."""
    while True:
        time.sleep(1 * 60 * 60)  # Sleep for 1 hour
        cleanup_old_simulations()

# Start the cleanup thread
cleanup_thread = threading.Thread(target=schedule_cache_cleanup, daemon=True)
cleanup_thread.start()

# Get valid states by checking configs directory
def get_valid_states():
    """Get list of valid states by checking config files in configs directory."""
    configs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs')
    valid_states = []
    
    try:
        for filename in os.listdir(configs_dir):
            if filename.endswith('.json'):
                # Remove .json extension to get state name
                state_name = filename[:-5]  # len('.json') == 5
                valid_states.append(state_name)
    except Exception as e:
        print(f"Error reading configs directory: {str(e)}")
        # Fallback to default states if there's an error
        valid_states = ['california', 'ohio', 'us_average']
    
    return valid_states

# Load data from CSV files
def load_data():
    data = {}
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    
    # Get valid states from config files
    valid_states = get_valid_states()
    
    try:
        for filename in os.listdir(results_dir):
            if filename.endswith('_results.csv') and not filename.startswith('yearly_additions_'):
                try:
                    # Extract state name from filename
                    state_name = filename.replace('_results.csv', '')
                    if state_name in valid_states:
                        file_path = os.path.join(results_dir, filename)
                        data[state_name] = pd.read_csv(file_path)
                except Exception as e:
                    print(f"Error loading {filename}: {str(e)}")
                    continue
    except Exception as e:
        print(f"Error accessing results directory: {str(e)}")
    
    return data

# Get available columns for visualization (excluding 'Year' which is used as x-axis)
def get_columns(data):
    # Use the first dataset to get columns
    first_state = list(data.keys())[0]
    columns = list(data[first_state].columns)
    columns.remove('Year')  # Remove Year as it's always the x-axis
    return columns

# Load model parameters for a specific state
def load_model_parameters(state):
    # Load state-specific configuration
    state_config = load_config(f'{state}.json')
    initial_data = state_config['initial_data']
    growth_rates = state_config['growth_rates']
    consumption_rates = state_config['consumption_rates']
    emission_factors = state_config['emission_factors']
    
    return {
        'initial_data': initial_data,
        'growth_rates': growth_rates,
        'consumption_rates': consumption_rates,
        'emission_factors': emission_factors
    }

# Routes
@app.route('/')
def index():
    try:
        data = load_data()
        if not data:
            return "No data available. Please ensure the model has been run and generated results.", 500
        
        states = list(data.keys())
        if not states:
            return "No state data available. Please check the configuration files and model output.", 500
        
        columns = get_columns(data)
        first_state = states[0]
        parameters = load_model_parameters(first_state)
        
        return render_template('index.html', 
                             states=states, 
                             columns=columns, 
                             parameters=parameters)
    except Exception as e:
        return f"Error loading application: {str(e)}", 500

@app.route('/parameters', methods=['POST'])
def get_parameters():
    state = request.json.get('state')
    if not state:
        return jsonify({'error': 'State not specified'}), 400
    
    parameters = load_model_parameters(state)
    return jsonify(parameters)

@app.route('/reset_parameters', methods=['POST'])
def reset_parameters():
    """Reset parameters to default values from config file."""
    try:
        state = request.json.get('state')
        if not state:
            return jsonify({'error': 'State not specified'}), 400
        
        # Load default parameters from config file
        parameters = load_model_parameters(state)
        return jsonify(parameters)
    except Exception as e:
        print(f"Error in reset_parameters: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/data', methods=['POST'])
def get_chart_data():
    data = load_data()
    request_data = request.json
    
    states = request_data.get('states', [])
    columns = request_data.get('columns', [])
    
    if not states:
        return jsonify({'error': 'No states selected'}), 400
    
    # Check if all states exist in data
    for state in states:
        if state not in data:
            return jsonify({'error': f'State {state} not found'}), 404
    
    # Prepare data for each state
    result = {}
    
    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#8AC249']
    
    for state in states:
        df = data[state]
        
        # Prepare data for chart
        chart_data = {
            'labels': df['Year'].tolist(),
            'datasets': []
        }
        
        # Add each selected column as a dataset
        for i, column in enumerate(columns):
            if column in df.columns:
                color_index = i % len(colors)
                chart_data['datasets'].append({
                    'label': column,
                    'data': df[column].tolist(),
                    'borderColor': colors[color_index],
                    'backgroundColor': colors[color_index] + '20',  # Add transparency
                    'fill': False,
                    'tension': 0.1
                })
        
        result[state] = chart_data
    
    return jsonify(result)

@app.route('/simulate', methods=['POST'])
def simulate_model():
    try:
        request_data = request.json
        
        state = request_data.get('state')
        if not state:
            return jsonify({'error': 'State not specified'}), 400
        
        # Get modified parameters from request
        modified_params = request_data.get('parameters', {})
        
        # Load base parameters for the state
        base_params = load_model_parameters(state)
        
        # Update base parameters with modified ones
        for category in modified_params:
            if category in base_params:
                for param, value in modified_params[category].items():
                    if param in base_params[category]:
                        # Convert string values to appropriate types
                        if isinstance(base_params[category][param], (int, float)):
                            # Special handling for retire_year which must be an integer
                            if category == 'growth_rates' and param == 'retire_year':
                                base_params[category][param] = int(float(value))
                            else:
                                base_params[category][param] = float(value)
                        elif isinstance(base_params[category][param], dict):
                            for subparam, subvalue in value.items():
                                if subparam in base_params[category][param]:
                                    base_params[category][param][subparam] = float(subvalue)
        
        # Ensure retire_year is an integer
        if 'growth_rates' in base_params and 'retire_year' in base_params['growth_rates']:
            base_params['growth_rates']['retire_year'] = int(base_params['growth_rates']['retire_year'])
        
        # Run the model with modified parameters
        model = TransportModel(
            base_params['initial_data'],
            base_params['growth_rates'],
            base_params['consumption_rates'],
            base_params['emission_factors']
        )
        
        # Run simulation from 2024 to 2100 (76 years)
        simulation_years = request_data.get('years', 76)
        model.run_simulation(years=simulation_years)
        
        # Convert results to DataFrame
        df = pd.DataFrame(model.results)
        
        # Generate a unique identifier for this simulation
        simulation_id = f"{state}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"

        # Clean up previous simulations for this state before saving the new one
        cleanup_state_simulations(state, keep_simulation_id=simulation_id)

        # Update the latest simulation ID for this state
        latest_simulations[state] = simulation_id

        # Save simulation results to cache
        cache_file = os.path.join(CACHE_DIR, f"{simulation_id}.json")
        
        # Get selected columns for visualization
        columns = request_data.get('columns', [])
        
        # Prepare data for chart
        chart_data = {
            'labels': df['Year'].tolist(),
            'datasets': []
        }
        
        # Add each selected column as a dataset
        colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#8AC249']
        for i, column in enumerate(columns):
            if column in df.columns:
                color_index = i % len(colors)
                chart_data['datasets'].append({
                    'label': f"{column} (Simulated - {state.capitalize()})",
                    'data': df[column].tolist(),
                    'borderColor': colors[color_index],
                    'backgroundColor': colors[color_index] + '20',  # Add transparency
                    'fill': False,
                    'tension': 0.1,
                    'borderDash': [5, 5],  # Add dashed line to distinguish from original data
                    'borderWidth': 3,  # Make the line thicker for better visibility
                    'simulated': True,  # Add flag to identify simulated datasets
                    'pointStyle': 'triangle',  # Use triangles for simulated data points
                    'pointRadius': 4,  # Make points slightly larger
                    'pointHoverRadius': 6,
                    'pointBorderWidth': 2,
                    'pointRotation': 180  # Point triangles downward
                })
        
        # Save both the full results and chart data with timestamp
        with open(cache_file, 'w') as f:
            json.dump({
                'simulation_id': simulation_id,
                'state': state,
                'parameters': base_params,
                'chart_data': chart_data,
                'full_results': df.to_dict(orient='records'),
                'timestamp': time.time(),
                'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, f)
        
        # Return the simulation ID and chart data
        return jsonify({
            'simulation_id': simulation_id,
            'chart_data': chart_data
        })
    
    except Exception as e:
        # Log the error
        print(f"Error in simulation: {str(e)}")
        # Return error message to client
        return jsonify({'error': f"Simulation error: {str(e)}"}), 500

@app.route('/simulation/<simulation_id>', methods=['GET'])
def get_simulation(simulation_id):
    try:
        cache_file = os.path.join(CACHE_DIR, f"{simulation_id}.json")
        if not os.path.exists(cache_file):
            return jsonify({'error': 'Simulation not found'}), 404

        with open(cache_file, 'r') as f:
            simulation_data = json.load(f)

        return jsonify(simulation_data)
    except Exception as e:
        return jsonify({'error': f"Error retrieving simulation: {str(e)}"}), 500

@app.route('/cleanup_simulation', methods=['POST'])
def cleanup_simulation():
    """Clean up a specific simulation cache file or all simulations for a state."""
    try:
        simulation_id = request.json.get('simulation_id')
        state = request.json.get('state')

        # If state is provided, clean up all simulations for that state except the latest
        if state:
            keep_id = latest_simulations.get(state)
            count = cleanup_state_simulations(state, keep_simulation_id=keep_id)
            return jsonify({
                'success': True,
                'message': f'Cleaned up {count} old simulations for {state}',
                'latest_simulation_id': keep_id
            })

        # If simulation_id is provided, clean up that specific simulation
        elif simulation_id:
            cache_file = os.path.join(CACHE_DIR, f"{simulation_id}.json")
            if os.path.exists(cache_file):
                # Read the file to get the state before deleting
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        state = data.get('state')

                        # If this is the latest simulation for this state, don't delete it
                        if state and latest_simulations.get(state) == simulation_id:
                            return jsonify({
                                'success': False,
                                'message': f'Cannot delete the latest simulation for {state}'
                            })
                except Exception as e:
                    print(f"Error reading simulation file: {str(e)}")

                # Delete the file
                os.remove(cache_file)
                return jsonify({
                    'success': True,
                    'message': f'Simulation {simulation_id} cleaned up successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Simulation file not found, may have been already cleaned up'
                })
        else:
            return jsonify({'error': 'Either simulation_id or state must be specified'}), 400
    except Exception as e:
        print(f"Error in cleanup_simulation: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Try different ports if 8000 is in use
    port = 8000
    max_port = 8010  # Try up to port 8010
    while port <= max_port:
        try:
            app.run(host='0.0.0.0', port=port, debug=True)
            break
        except OSError as e:
            if port == max_port:
                print(f"Could not find an available port between {8000} and {max_port}")
                sys.exit(1)
            print(f"Port {port} is in use, trying {port + 1}")
            port += 1