import os
import json
import pandas as pd
import numpy as np
import tempfile
from flask import Flask, render_template, request, jsonify
from footprint_model import TransportModel, load_config

app = Flask(__name__)

# Load data from CSV files
def load_data():
    data = {}
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    for filename in os.listdir(results_dir):
        if filename.endswith('.csv'):
            state_name = filename.split('_')[0]
            file_path = os.path.join(results_dir, filename)
            data[state_name] = pd.read_csv(file_path)
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
    # Load common configuration
    common_config = load_config('common.json')
    consumption_rates = common_config['consumption_rates']
    emission_factors = common_config['emission_factors']
    
    # Load state-specific configuration
    state_config = load_config(f'{state}.json')
    initial_data = state_config['initial_data']
    growth_rates = state_config['growth_rates']
    
    return {
        'initial_data': initial_data,
        'growth_rates': growth_rates,
        'consumption_rates': consumption_rates,
        'emission_factors': emission_factors
    }

# Routes
@app.route('/')
def index():
    data = load_data()
    states = list(data.keys())
    columns = get_columns(data)
    
    # Get parameters for the first state to display in the form
    first_state = states[0]
    parameters = load_model_parameters(first_state)
    
    return render_template('index.html', 
                          states=states, 
                          columns=columns, 
                          parameters=parameters)

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
        
        # Run simulation from 2024 to 2080 (56 years)
        simulation_years = request_data.get('years', 56)
        model.run_simulation(years=simulation_years)
        
        # Convert results to DataFrame
        df = pd.DataFrame(model.results)
        
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
                    'borderWidth': 3  # Make the line thicker for better visibility
                })
        
        return jsonify(chart_data)
    
    except Exception as e:
        # Log the error
        print(f"Error in simulation: {str(e)}")
        # Return error message to client
        return jsonify({'error': f"Simulation error: {str(e)}"}), 500

if __name__ == '__main__':
    # Run on 0.0.0.0 to allow external connections, port 8000
    app.run(host='0.0.0.0', port=8000, debug=True)