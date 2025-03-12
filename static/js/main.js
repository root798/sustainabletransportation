// Global variables
let charts = {};
let currentScaleType = 'linear';
let originalChartData = null;
let simulatedChartData = null;
let currentState = '';
let currentParameters = {};
let originalParameters = {};  // Store original parameters for each state
const MAX_STATES = 3;
let simulationResults = {};  // Store simulation results by simulation ID
let latestSimulationByState = {};  // Track the latest simulation ID for each state
let isRealtimeEnabled = false;  // Flag for real-time simulation mode
let realtimeSimulationTimeout = null;  // Timeout for debouncing real-time simulations

// Function to show status message
function showStatusMessage(message, type = 'info') {
    // Create or get status container
    let statusContainer = document.getElementById('status-message');
    if (!statusContainer) {
        statusContainer = document.createElement('div');
        statusContainer.id = 'status-message';
        statusContainer.className = 'alert alert-dismissible fade show mt-2';
        statusContainer.style.display = 'none';
        
        // Add close button
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close';
        closeButton.setAttribute('data-bs-dismiss', 'alert');
        closeButton.setAttribute('aria-label', 'Close');
        statusContainer.appendChild(closeButton);
        
        // Insert after the charts container
        const chartsContainer = document.getElementById('charts-container');
        chartsContainer.parentNode.insertBefore(statusContainer, chartsContainer.nextSibling);
    }

    // Update message and type
    statusContainer.className = `alert alert-${type} alert-dismissible fade show mt-2`;
    statusContainer.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
    statusContainer.style.display = 'block';

    // Auto-hide after 5 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            statusContainer.style.display = 'none';
        }, 5000);
    }
}

// Function to clean up all simulations on page load
function cleanupAllSimulations() {
    // Get all states
    const states = Array.from(document.querySelectorAll('.state-checkbox')).map(cb => cb.value);

    // Clean up simulations for each state
    states.forEach(state => {
        fetch(window.location.origin + '/cleanup_simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                state: state
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.latest_simulation_id) {
                // If there's a latest simulation, track it
                latestSimulationByState[state] = data.latest_simulation_id;
                console.log(`Latest simulation for ${state}: ${data.latest_simulation_id}`);
            }
        })
        .catch(error => {
            console.warn(`Error cleaning up simulations for ${state}:`, error);
        });
    });
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Clean up simulations on page load
    cleanupAllSimulations();

    // Set up visualization form submission
    const visualizationForm = document.getElementById('visualization-form');
    visualizationForm.addEventListener('submit', function(e) {
        e.preventDefault();
        updateChart();
    });

    // Set up toggle buttons for collapsible sections
    const toggleButtons = document.querySelectorAll('[data-bs-toggle="collapse"]');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const icon = this.querySelector('i');
            if (icon) {
                if (icon.classList.contains('bi-chevron-up')) {
                    icon.classList.replace('bi-chevron-up', 'bi-chevron-down');
                } else {
                    icon.classList.replace('bi-chevron-down', 'bi-chevron-up');
                }
            }
        });
    });

    // Initialize Bootstrap tabs
    const variableTabs = document.querySelectorAll('#variableTabs .nav-link');
    variableTabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            // Remove active class from all tabs
            variableTabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            this.classList.add('active');

            // Hide all tab panes
            const tabPanes = document.querySelectorAll('#variableTabsContent .tab-pane');
            tabPanes.forEach(pane => {
                pane.classList.remove('show', 'active');
            });

            // Show the target tab pane
            const targetId = this.getAttribute('data-bs-target');
            const targetPane = document.querySelector(targetId);
            if (targetPane) {
                targetPane.classList.add('show', 'active');
            }
        });
    });

    // Set up scale type buttons
    document.getElementById('btn-linear').addEventListener('click', function() {
        setScaleType('linear');
    });

    document.getElementById('btn-logarithmic').addEventListener('click', function() {
        setScaleType('logarithmic');
    });

    // Set up state checkbox change events
    const stateCheckboxes = document.querySelectorAll('.state-checkbox');
    stateCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Enforce maximum of 3 states
            const checkedStates = document.querySelectorAll('.state-checkbox:checked');
            if (checkedStates.length > MAX_STATES) {
                this.checked = false;
                document.getElementById('state-selection-warning').textContent =
                    `Maximum ${MAX_STATES} states can be selected.`;
            } else {
                document.getElementById('state-selection-warning').textContent = '';

                // If this is the first checked state, load its parameters
                if (checkedStates.length === 1) {
                    loadStateParameters(checkedStates[0].value);
                }
            }
        });
    });

    // Set up parameter state selection change event
    const paramStateSelect = document.getElementById('parameter-state-select');
    if (paramStateSelect) {
        paramStateSelect.addEventListener('change', function() {
            currentState = this.value;
            loadStateParameters(currentState);
        });
    }

    // Set up simulate button
    document.getElementById('simulate-btn').addEventListener('click', function() {
        runSimulation();
    });

    // Set up reset parameters button
    document.getElementById('reset-params-btn').addEventListener('click', function() {
        resetParameters();
    });

    // Set up real-time toggle
    const realtimeToggle = document.getElementById('realtime-toggle');
    realtimeToggle.addEventListener('change', function() {
        isRealtimeEnabled = this.checked;

        // Show/hide simulate button based on real-time mode
        document.getElementById('simulate-btn').style.display = isRealtimeEnabled ? 'none' : 'block';

        if (isRealtimeEnabled) {
            showStatusMessage('Real-time simulation mode enabled. Adjust sliders to see immediate results.', 'info');
        } else {
            showStatusMessage('Real-time simulation mode disabled. Use "Simulate with New Parameters" button to run simulations.', 'info');
        }
    });

    // Set up parameter sliders
    setupParameterSliders();

    // Initial chart load - use the first state as default
    const firstStateCheckbox = document.querySelector('.state-checkbox');
    if (firstStateCheckbox) {
        currentState = firstStateCheckbox.value;
        loadStateParameters(currentState);
    }

    // Ensure we have default variables selected
    const defaultVariables = [
        "ATS Total Power (kWh)",
        "ATS Emissions (kg CO2)",
        "Total CAV",
        "Total STI"
    ];

    defaultVariables.forEach(variable => {
        const checkbox = document.querySelector(`.variable-checkbox[value="${variable}"]`);
        if (checkbox) {
            checkbox.checked = true;
        }
    });

    // Update chart with default selections
    updateChart();
});

// Function to set up parameter sliders
function setupParameterSliders() {
    // Get all sliders
    const sliders = document.querySelectorAll('.param-slider');

    // For each slider, set up event listeners
    sliders.forEach(slider => {
        const inputId = slider.id.replace('-slider', '');
        const input = document.getElementById(inputId);
        const valueDisplay = document.getElementById(`${inputId}-value`);

        if (input) {
            // Update input and value display when slider changes
            slider.addEventListener('input', function() {
                const value = this.value;
                input.value = value;

                // Update value display
                if (valueDisplay) {
                    // Format the value for display (show fewer decimal places for small numbers)
                    valueDisplay.textContent = formatParameterValue(value);
                }

                // If real-time mode is enabled, run simulation after a short delay
                if (isRealtimeEnabled) {
                    // Clear any existing timeout
                    if (realtimeSimulationTimeout) {
                        clearTimeout(realtimeSimulationTimeout);
                    }

                    // Set a new timeout to run simulation after 300ms of no slider movement
                    realtimeSimulationTimeout = setTimeout(() => {
                        runRealtimeSimulation();
                    }, 300);
                }
            });

            // Update slider and value display when input changes
            input.addEventListener('input', function() {
                const value = this.value;
                slider.value = value;

                // Update value display
                if (valueDisplay) {
                    // Format the value for display
                    valueDisplay.textContent = formatParameterValue(value);
                }

                // If real-time mode is enabled, run simulation after a short delay
                if (isRealtimeEnabled) {
                    // Clear any existing timeout
                    if (realtimeSimulationTimeout) {
                        clearTimeout(realtimeSimulationTimeout);
                    }

                    // Set a new timeout to run simulation after 300ms of no input changes
                    realtimeSimulationTimeout = setTimeout(() => {
                        runRealtimeSimulation();
                    }, 300);
                }
            });
        }
    });
}

// Helper function to format parameter values for display
function formatParameterValue(value) {
    // Convert to number to ensure proper formatting
    const numValue = parseFloat(value);

    // Format based on the value's magnitude
    if (numValue >= 1) {
        // For values >= 1, show up to 1 decimal place
        return numValue.toFixed(1).replace(/\.0$/, '');
    } else if (numValue >= 0.1) {
        // For values between 0.1 and 1, show up to 2 decimal places
        return numValue.toFixed(2);
    } else {
        // For very small values, show up to 3 decimal places
        return numValue.toFixed(3);
    }
}

// Function to run real-time simulation
function runRealtimeSimulation() {
    // Get the state selected for parameter modification
    const paramStateSelect = document.getElementById('parameter-state-select');
    const paramState = paramStateSelect ? paramStateSelect.value : currentState;

    // Get all checked states
    const stateCheckboxes = document.querySelectorAll('.state-checkbox:checked');
    const selectedStates = Array.from(stateCheckboxes).map(cb => cb.value);

    // Check if the parameter state is among the selected states for display
    if (!selectedStates.includes(paramState)) {
        showStatusMessage(`Please select ${paramState.charAt(0).toUpperCase() + paramState.slice(1)} in the chart settings to view simulation results.`, 'warning');
        return;
    }

    // Collect current parameters
    const parameters = collectParameters();
    const selectedColumns = getSelectedVariables();

    // Run simulation without showing loading message
    runSimulation(true);
}

// Function to load parameters for a selected state
function loadStateParameters(state) {
    fetch(window.location.origin + '/parameters', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            state: state
        }),
    })
    .then(response => response.json())
    .then(data => {
        currentParameters = data;
        originalParameters[state] = JSON.parse(JSON.stringify(data)); // Deep copy for reference
        updateParameterForm(data);

        // Update the parameter state select dropdown
        const paramStateSelect = document.getElementById('parameter-state-select');
        if (paramStateSelect) {
            paramStateSelect.value = state;
        }
    })
    .catch(error => {
        console.error('Error fetching parameters:', error);
    });
}

// Function to update the parameter form with values from the server
function updateParameterForm(parameters) {
    // Update growth rates
    for (const [key, value] of Object.entries(parameters.growth_rates)) {
        // Update input field
        const input = document.querySelector(`[name="growth_rates.${key}"]`);
        if (input) {
            input.value = value;
        }

        // Update slider
        const slider = document.getElementById(`${input?.id}-slider`);
        if (slider) {
            slider.value = value;
        }

        // Update value display
        const valueDisplay = document.getElementById(`${input?.id}-value`);
        if (valueDisplay) {
            valueDisplay.textContent = formatParameterValue(value);
        }
    }

    // Update initial data
    for (const [key, value] of Object.entries(parameters.initial_data)) {
        const input = document.querySelector(`[name="initial_data.${key}"]`);
        if (input) {
            input.value = value;
        }
    }

    // Update emission factors
    for (const [key, value] of Object.entries(parameters.emission_factors)) {
        const input = document.querySelector(`[name="emission_factors.${key}"]`);
        if (input) {
            input.value = value;
        }
    }
}

// Function to collect parameters from the form
function collectParameters() {
    const parameters = {
        growth_rates: {},
        initial_data: {},
        emission_factors: {}
    };

    // Collect all parameter inputs
    const inputs = document.querySelectorAll('.param-input');
    inputs.forEach(input => {
        const nameParts = input.name.split('.');
        const category = nameParts[0];
        const param = nameParts[1];

        if (parameters[category]) {
            // Special handling for retire_year to ensure it's an integer
            if (category === 'growth_rates' && param === 'retire_year') {
                parameters[category][param] = parseInt(input.value);
            } else {
                parameters[category][param] = parseFloat(input.value);
            }
        }
    });

    return parameters;
}

// Function to reset parameters to default values
function resetParameters() {
    // Get the state selected for parameter modification
    const paramStateSelect = document.getElementById('parameter-state-select');
    const paramState = paramStateSelect ? paramStateSelect.value : currentState;

    // Show loading message
    showStatusMessage('Resetting parameters to default values...', 'info');

    // Fetch default parameters from server
    fetch(window.location.origin + '/reset_parameters', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            state: paramState
        }),
    })
    .then(response => {
        if (!response.ok) {
            console.error('Server response not OK:', response.status, response.statusText);
            throw new Error(`Failed to reset parameters: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        // Update form with default values
        updateParameterForm(data);
        currentParameters = data;
        originalParameters[paramState] = JSON.parse(JSON.stringify(data)); // Update original parameters

        // If in real-time mode, run a simulation with the reset parameters
        if (isRealtimeEnabled) {
            runRealtimeSimulation();
        }

        // Show success message
        showStatusMessage(`Parameters for ${paramState.charAt(0).toUpperCase() + paramState.slice(1)} have been reset to default values.`, 'success');
    })
    .catch(error => {
        console.error('Error resetting parameters:', error);
        showStatusMessage(`Error resetting parameters: ${error.message}`, 'danger');
    });
}

// Function to update the charts based on form selections
function updateChart() {
    // Get all checked states
    const stateCheckboxes = document.querySelectorAll('.state-checkbox:checked');
    const selectedStates = Array.from(stateCheckboxes).map(cb => cb.value);

    // Get all checked variables
    const variableCheckboxes = document.querySelectorAll('.variable-checkbox:checked');
    const selectedColumns = Array.from(variableCheckboxes).map(cb => cb.value);

    // Show loading message
    showStatusMessage('Loading data...', 'info');

    // Fetch data from server
    fetch(window.location.origin + '/data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            states: selectedStates,
            columns: selectedColumns
        }),
    })
    .then(response => response.json())
    .then(data => {
        originalChartData = data;
        
        // Prepare display data with any active simulations
        const displayData = { ...data };
        
        // Add any active simulation results for selected states
        for (const simId in simulationResults) {
            const sim = simulationResults[simId];
            if (selectedStates.includes(sim.state)) {
                displayData[sim.state] = {
                    labels: data[sim.state].labels,
                    datasets: [
                        ...data[sim.state].datasets,
                        ...sim.chart_data.datasets
                    ]
                };
            }
        }
        
        renderCharts(displayData, selectedStates);
        showStatusMessage('Charts updated successfully.', 'success');
    })
    .catch(error => {
        console.error('Error fetching data:', error);
        showStatusMessage(`Error loading data: ${error.message || 'Unknown error'}`, 'danger');
        document.getElementById('charts-container').innerHTML =
            `<div class="col-md-12 text-center py-5 text-danger"><p>Error loading data: ${error.message || 'Unknown error'}</p></div>`;
    });
}

// Function to run simulation
function runSimulation(isRealtime = false) {
    // Get the state selected for parameter modification
    const paramStateSelect = document.getElementById('parameter-state-select');
    const paramState = paramStateSelect ? paramStateSelect.value : currentState;

    // Get all checked states
    const stateCheckboxes = document.querySelectorAll('.state-checkbox:checked');
    const selectedStates = Array.from(stateCheckboxes).map(cb => cb.value);

    // Check if the parameter state is among the selected states for display
    if (!selectedStates.includes(paramState)) {
        showStatusMessage(`Please select ${paramState.charAt(0).toUpperCase() + paramState.slice(1)} in the chart settings to view simulation results.`, 'warning');
        return;
    }

    // Collect current parameters
    const parameters = collectParameters();
    const selectedColumns = getSelectedVariables();

    // Show loading message if not in real-time mode
    if (!isRealtime) {
        showStatusMessage('Running simulation...', 'info');
    }

    // Send simulation request
    fetch(window.location.origin + '/simulate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            state: paramState,
            parameters: parameters,
            columns: selectedColumns,
            years: 76  // Simulation period (2024 to 2100)
        }),
    })
    .then(response => {
        if (!response.ok) {
            console.error('Server response not OK:', response.status, response.statusText);
            throw new Error(`Failed to run simulation: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        const { simulation_id, chart_data } = data;

        // Clean up previous simulation for this state
        cleanupPreviousSimulation(paramState);

        // Store simulation results
        simulationResults[simulation_id] = {
            state: paramState,
            chart_data: chart_data,
            timestamp: Date.now()
        };

        // Track this as the latest simulation for this state
        latestSimulationByState[paramState] = simulation_id;

        // Log the simulation tracking
        console.log(`New simulation for ${paramState}: ${simulation_id}`);
        console.log('Latest simulations by state:', latestSimulationByState);

        // Prepare data for rendering
        const displayData = {};
        for (const state in originalChartData) {
            if (state === paramState) {
                // For the simulated state, show both original and simulated data
                displayData[state] = {
                    labels: originalChartData[state].labels,
                    datasets: [
                        ...originalChartData[state].datasets,
                        ...chart_data.datasets
                    ]
                };
            } else {
                // For other states, show only original data
                displayData[state] = originalChartData[state];
            }
        }

        // Render charts
        renderCharts(displayData, selectedStates);

        // Show success message if not in real-time mode
        if (!isRealtime) {
            showStatusMessage(`Simulation completed successfully for ${paramState.charAt(0).toUpperCase() + paramState.slice(1)}. Dashed lines show simulated results.`, 'success');
        }
    })
    .catch(error => {
        console.error('Error running simulation:', error);
        if (!isRealtime) {
            showStatusMessage(`Error running simulation: ${error.message}`, 'danger');
        }
    });
}

// Function to merge original and simulated chart data
function mergeChartData(original, simulated) {
    if (!simulated) return original;

    // If original is an object with state keys
    if (typeof original === 'object' && !Array.isArray(original) && original !== null) {
        const merged = {};

        // For each state in original
        for (const state in original) {
            merged[state] = {
                labels: original[state].labels,
                datasets: [...original[state].datasets]
            };
        }

        // Add simulated datasets to the current state
        if (currentState in merged && simulated.datasets) {
            merged[currentState].datasets = merged[currentState].datasets.concat(simulated.datasets);
        }

        return merged;
    } else {
        // Legacy support for single chart
        const merged = {
            labels: original.labels,
            datasets: [...original.datasets]
        };

        // Add simulated datasets
        if (simulated.datasets) {
            merged.datasets = merged.datasets.concat(simulated.datasets);
        }

        return merged;
    }
}

// Function to render multiple charts with the fetched data
function renderCharts(data, states) {
    // Clear existing charts
    for (const chartId in charts) {
        if (charts[chartId]) {
            charts[chartId].destroy();
            delete charts[chartId];
        }
    }

    // Clear the container
    const chartsContainer = document.getElementById('charts-container');
    chartsContainer.innerHTML = '';

    // Define chart types
    const chartTypes = ['energy_emissions', 'quantities'];
    const chartTitles = {
        'energy_emissions': 'Energy & Emissions',
        'quantities': 'Vehicle & Infrastructure Counts'
    };

    // Create a row for each state
    states.forEach(state => {
        if (!data[state] || !data[state].datasets || data[state].datasets.length === 0) {
            return;
        }

        // Create a row for this state
        const stateRow = document.createElement('div');
        stateRow.className = 'row mb-4 state-charts-row';

        // Add state header
        const stateHeader = document.createElement('div');
        stateHeader.className = 'col-12 mb-2';
        stateHeader.innerHTML = `<h4 class="state-title">${state.charAt(0).toUpperCase() + state.slice(1)}</h4>`;
        stateRow.appendChild(stateHeader);

        // Group datasets by unit type
        const datasets = data[state].datasets;

        // Debug: Log the datasets before grouping
        console.log(`Datasets for ${state} before grouping:`, datasets.map(d => d.label));

        const datasetGroups = groupDatasetsByUnit(datasets);

        // Debug: Log the grouped datasets
        console.log(`Dataset groups for ${state}:`, {
            power: datasetGroups['power']?.datasets?.map(d => d.label) || [],
            emissions: datasetGroups['emissions']?.datasets?.map(d => d.label) || [],
            vehicles: datasetGroups['vehicles']?.datasets?.map(d => d.label) || [],
            other: datasetGroups['other']?.datasets?.map(d => d.label) || []
        });

        // Create two charts for each state: one for energy/emissions, one for quantities
        chartTypes.forEach(chartType => {
            // Create column for this chart type
            const colDiv = document.createElement('div');
            colDiv.className = 'col-md-6 mb-3';

            // Create card
            const cardDiv = document.createElement('div');
            cardDiv.className = 'card chart-card';

            // Create card header
            const cardHeader = document.createElement('div');
            cardHeader.className = 'card-header';

            // Count datasets for this chart type
            let datasetCount = 0;
            if (chartType === 'energy_emissions') {
                datasetCount = (datasetGroups['power']?.datasets?.length || 0) +
                              (datasetGroups['emissions']?.datasets?.length || 0);
            } else if (chartType === 'quantities') {
                datasetCount = datasetGroups['vehicles']?.datasets?.length || 0;
            }

            cardHeader.innerHTML = `<h5>${chartTitles[chartType]} (${datasetCount})</h5>`;

            // Create card body
            const cardBody = document.createElement('div');
            cardBody.className = 'card-body';

            // Create chart container
            const chartContainer = document.createElement('div');
            chartContainer.className = 'chart-container';

            // Create canvas
            const canvas = document.createElement('canvas');
            const chartId = `chart-${state}-${chartType}`;
            canvas.id = chartId;

            // Append elements
            chartContainer.appendChild(canvas);
            cardBody.appendChild(chartContainer);
            cardDiv.appendChild(cardHeader);
            cardDiv.appendChild(cardBody);
            colDiv.appendChild(cardDiv);
            stateRow.appendChild(colDiv);

            // Prepare datasets for this chart type
            let chartDatasets = [];
            let scales = {};

            if (chartType === 'energy_emissions') {
                // Combine power and emissions datasets
                const powerDatasets = datasetGroups['power']?.datasets || [];
                const emissionsDatasets = datasetGroups['emissions']?.datasets || [];

                // Assign each dataset to its appropriate y-axis
                powerDatasets.forEach(dataset => {
                    dataset.yAxisID = 'y';
                });

                emissionsDatasets.forEach(dataset => {
                    dataset.yAxisID = 'y1';
                });

                chartDatasets = [...powerDatasets, ...emissionsDatasets];

                // Create scales with two y-axes
                scales = {
                    x: {
                        title: {
                            display: true,
                            text: 'Year'
                        }
                    },
                    y: {
                        type: currentScaleType,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Power (TWh)'
                        },
                        ticks: {
                            callback: function(value) {
                                return formatAxisLabel(value, 'power');
                            }
                        },
                        grid: {
                            drawOnChartArea: true
                        }
                    },
                    y1: {
                        type: currentScaleType,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Emissions (kiloton CO₂)'
                        },
                        ticks: {
                            callback: function(value) {
                                return formatAxisLabel(value, 'emissions');
                            }
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                };
            } else if (chartType === 'quantities') {
                // Use only vehicle datasets
                chartDatasets = datasetGroups['vehicles']?.datasets || [];

                // Create scales with a single y-axis
                scales = {
                    x: {
                        title: {
                            display: true,
                            text: 'Year'
                        }
                    },
                    y: {
                        type: currentScaleType,
                        title: {
                            display: true,
                            text: 'Count'
                        },
                        ticks: {
                            callback: function(value) {
                                return formatAxisLabel(value, 'vehicles');
                            }
                        }
                    }
                };
            }

            // Skip if no datasets for this chart type
            if (chartDatasets.length === 0) {
                colDiv.remove();
                return;
            }

            // Create chart with updated options
            const ctx = canvas.getContext('2d');
            charts[chartId] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data[state].labels,
                    datasets: chartDatasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null) {
                                        // Format large numbers with commas
                                        label += new Intl.NumberFormat().format(context.parsed.y);
                                    }
                                    return label;
                                }
                            }
                        },
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                boxWidth: 6
                            }
                        }
                    },
                    scales: scales
                }
            });
        });

        // Add the state row to the container
        chartsContainer.appendChild(stateRow);
    });
}

// Function to group datasets by unit type
function groupDatasetsByUnit(datasets) {
    const groups = {
        'power': { // kWh
            datasets: [],
            maxValue: 0
        },
        'emissions': { // kg CO2
            datasets: [],
            maxValue: 0
        },
        'vehicles': { // count
            datasets: [],
            maxValue: 0
        },
        'other': { // other units
            datasets: [],
            maxValue: 0
        }
    };

    datasets.forEach(dataset => {
        const label = dataset.label.toLowerCase();
        let group = 'other';

        // Determine the group based on the dataset label
        if (label.includes('power') || label.includes('kwh') || label.includes('electricity') || label.includes('consumption')) {
            group = 'power';
        } else if (label.includes('emission') || label.includes('co2')) {
            group = 'emissions';
        } else if (label.includes('vehicle') || label.includes('car') || label.includes('cav') || label.includes('ecav') ||
                  label.includes('icecav') || label.includes('sti') || label.includes('infra') ||
                  label.includes(' ev') || label.includes('total ev') || label.includes('icev') ||
                  label.includes('fraction') || label.includes('cumulative')) {
            group = 'vehicles';
        }

        // Special case handling for specific variables
        if (label === 'total ev' || label === 'total icev' || label.includes('incremented car')) {
            group = 'vehicles';
        }

        // Fallback: If it contains "Total" and isn't already categorized as power or emissions,
        // it's likely a count/quantity
        if (label.includes('total') && group !== 'power' && group !== 'emissions') {
            group = 'vehicles';
        }

        // Add dataset to the appropriate group
        groups[group].datasets.push(dataset);

        // Update max value for the group
        const maxInDataset = Math.max(...dataset.data.filter(val => !isNaN(val)));
        if (maxInDataset > groups[group].maxValue) {
            groups[group].maxValue = maxInDataset;
        }
    });

    return groups;
}

// Function to create scales configuration for Chart.js
function createScalesConfiguration(datasetGroups) {
    const scales = {
        x: {
            title: {
                display: true,
                text: 'Year'
            }
        }
    };

    // Create a y-axis for each group that has datasets
    let axisIndex = 0;
    const axisIds = {};

    for (const [groupName, group] of Object.entries(datasetGroups)) {
        if (group.datasets.length > 0) {
            const axisId = axisIndex === 0 ? 'y' : `y${axisIndex + 1}`;
            axisIds[groupName] = axisId;

            scales[axisId] = {
                type: currentScaleType,
                position: axisIndex === 0 ? 'left' : 'right',
                title: {
                    display: true,
                    text: getAxisTitle(groupName)
                },
                ticks: {
                    callback: function(value) {
                        return formatAxisLabel(value, groupName);
                    }
                },
                grid: {
                    drawOnChartArea: axisIndex === 0 // Only draw grid for the first axis
                }
            };

            // Assign each dataset to its axis
            group.datasets.forEach(dataset => {
                dataset.yAxisID = axisId;
            });

            axisIndex++;

            // Only use up to 2 y-axes to avoid cluttering
            if (axisIndex >= 2) break;
        }
    }

    // If we have more than 2 groups with datasets, assign the remaining ones to existing axes
    if (axisIndex >= 2) {
        let remainingAxisId = 0;
        for (const [groupName, group] of Object.entries(datasetGroups)) {
            if (group.datasets.length > 0 && !axisIds[groupName]) {
                const axisId = remainingAxisId === 0 ? 'y' : 'y2';
                group.datasets.forEach(dataset => {
                    dataset.yAxisID = axisId;
                });
                remainingAxisId = (remainingAxisId + 1) % 2;
            }
        }
    }

    return scales;
}

// Function to get axis title based on group name
function getAxisTitle(groupName) {
    switch (groupName) {
        case 'power':
            return 'Power (TWh)';
        case 'emissions':
            return 'Emissions (kiloton CO₂)';
        case 'vehicles':
            return 'Count';
        default:
            return 'Value';
    }
}

// Function to format axis labels based on group
function formatAxisLabel(value, groupName) {
    if (groupName === 'power') {
        // Convert kWh to TWh (1 TWh = 1,000,000,000 kWh)
        return (value / 1000000000).toFixed(2) + ' TWh';
    } else if (groupName === 'emissions') {
        // Convert kg CO2 to kiloton CO2 (1 kiloton = 1,000,000 kg)
        return (value / 1000000).toFixed(2) + ' kt';
    } else {
        // For other values (like vehicle counts), use K, M, B suffixes
        if (value >= 1000000000) {
            return (value / 1000000000).toFixed(1) + 'B';
        } else if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M';
        } else if (value >= 1000) {
            return (value / 1000).toFixed(1) + 'K';
        } else {
            return value.toFixed(0);
        }
    }
}

// Function to render a single chart (for backward compatibility)
function renderChart(data, chartId = 'atsChart') {
    // For backward compatibility, we'll convert the single chart to our new multi-chart layout
    const chartsContainer = document.getElementById('charts-container');
    chartsContainer.innerHTML = '';

    // Create a single state row
    const stateRow = document.createElement('div');
    stateRow.className = 'row mb-4 state-charts-row';
    chartsContainer.appendChild(stateRow);

    // Group datasets by unit type
    const datasetGroups = groupDatasetsByUnit(data.datasets || []);

    // Define chart types
    const chartTypes = ['energy_emissions', 'quantities'];
    const chartTitles = {
        'energy_emissions': 'Energy & Emissions',
        'quantities': 'Vehicle & Infrastructure Counts'
    };

    // Create two charts: one for energy/emissions, one for quantities
    chartTypes.forEach(chartType => {
        // Create column for this chart type
        const colDiv = document.createElement('div');
        colDiv.className = 'col-md-6 mb-3';
        stateRow.appendChild(colDiv);

        // Create card
        const cardDiv = document.createElement('div');
        cardDiv.className = 'card chart-card';
        colDiv.appendChild(cardDiv);

        // Create card header
        const cardHeader = document.createElement('div');
        cardHeader.className = 'card-header';

        // Count datasets for this chart type
        let datasetCount = 0;
        if (chartType === 'energy_emissions') {
            datasetCount = (datasetGroups['power']?.datasets?.length || 0) +
                          (datasetGroups['emissions']?.datasets?.length || 0);
        } else if (chartType === 'quantities') {
            datasetCount = datasetGroups['vehicles']?.datasets?.length || 0;
        }

        cardHeader.innerHTML = `<h5>${chartTitles[chartType]} (${datasetCount})</h5>`;
        cardDiv.appendChild(cardHeader);

        // Create card body
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        cardDiv.appendChild(cardBody);

        // Create chart container
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';
        cardBody.appendChild(chartContainer);

        // Create canvas
        const canvas = document.createElement('canvas');
        const unitChartId = `${chartId}-${chartType}`;
        canvas.id = unitChartId;
        chartContainer.appendChild(canvas);

        // Prepare datasets for this chart type
        let chartDatasets = [];
        let scales = {};

        if (chartType === 'energy_emissions') {
            // Combine power and emissions datasets
            const powerDatasets = datasetGroups['power']?.datasets || [];
            const emissionsDatasets = datasetGroups['emissions']?.datasets || [];

            // Skip if no datasets for this chart type
            if (powerDatasets.length === 0 && emissionsDatasets.length === 0) {
                colDiv.remove();
                return;
            }

            // Assign each dataset to its appropriate y-axis
            powerDatasets.forEach(dataset => {
                dataset.yAxisID = 'y';
            });

            emissionsDatasets.forEach(dataset => {
                dataset.yAxisID = 'y1';
            });

            chartDatasets = [...powerDatasets, ...emissionsDatasets];

            // Create scales with two y-axes
            scales = {
                x: {
                    title: {
                        display: true,
                        text: 'Year'
                    }
                },
                y: {
                    type: currentScaleType,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Power (TWh)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatAxisLabel(value, 'power');
                        }
                    },
                    grid: {
                        drawOnChartArea: true
                    }
                },
                y1: {
                    type: currentScaleType,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Emissions (kiloton CO₂)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatAxisLabel(value, 'emissions');
                        }
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            };
        } else if (chartType === 'quantities') {
            // Use only vehicle datasets
            chartDatasets = datasetGroups['vehicles']?.datasets || [];

            // Skip if no datasets for this chart type
            if (chartDatasets.length === 0) {
                colDiv.remove();
                return;
            }

            // Create scales with a single y-axis
            scales = {
                x: {
                    title: {
                        display: true,
                        text: 'Year'
                    }
                },
                y: {
                    type: currentScaleType,
                    title: {
                        display: true,
                        text: 'Count'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatAxisLabel(value, 'vehicles');
                        }
                    }
                }
            };
        }

        // Create chart
        const ctx = canvas.getContext('2d');
        charts[unitChartId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: chartDatasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    // Format large numbers with commas
                                    label += new Intl.NumberFormat().format(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    },
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            boxWidth: 6
                        }
                    }
                },
                scales: scales
            }
        });
    });
}

// Function to change the scale type (linear or logarithmic)
function setScaleType(type) {
    if (type === currentScaleType) return;

    currentScaleType = type;

    // Update button states
    document.getElementById('btn-linear').classList.toggle('btn-outline-secondary', type !== 'linear');
    document.getElementById('btn-linear').classList.toggle('btn-secondary', type === 'linear');
    document.getElementById('btn-logarithmic').classList.toggle('btn-outline-secondary', type !== 'logarithmic');
    document.getElementById('btn-logarithmic').classList.toggle('btn-secondary', type === 'logarithmic');

    // Update all charts
    for (const chartId in charts) {
        if (charts[chartId] && charts[chartId].options && charts[chartId].options.scales) {
            // Update primary y-axis
            if (charts[chartId].options.scales.y) {
                charts[chartId].options.scales.y.type = type;
            }

            // Update secondary y-axis if it exists (for energy & emissions charts)
            if (charts[chartId].options.scales.y1) {
                charts[chartId].options.scales.y1.type = type;
            }

            charts[chartId].update();
        }
    }
}

// Function to get selected variables
function getSelectedVariables() {
    const checkboxes = document.querySelectorAll('.variable-checkbox:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// Function to clean up previous simulation for a state
function cleanupPreviousSimulation(state) {
    // If there's a previous simulation for this state
    if (latestSimulationByState[state]) {
        const previousSimId = latestSimulationByState[state];

        // Remove it from the client-side simulation results
        delete simulationResults[previousSimId];
    }

    // Send a request to the server to clean up all old simulations for this state
    // The server will keep only the latest simulation
    fetch(window.location.origin + '/cleanup_simulation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            state: state
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`Cleaned up old simulations for ${state}: ${data.message}`);
        } else {
            console.warn(`Failed to clean up simulations: ${data.message}`);
        }
    })
    .catch(error => {
        console.warn('Error cleaning up simulations on server:', error);
    });
}