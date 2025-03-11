// Global variables
let charts = {};
let currentScaleType = 'linear';
let originalChartData = {};
let simulatedChartData = null;
let currentState = '';
let currentParameters = {};
const MAX_STATES = 3;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Set up visualization form submission
    const visualizationForm = document.getElementById('visualization-form');
    visualizationForm.addEventListener('submit', function(e) {
        e.preventDefault();
        updateChart();
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
        const input = document.querySelector(`[name="growth_rates.${key}"]`);
        if (input) {
            input.value = value;
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

    // Show loading indicator
    const simulationStatus = document.getElementById('simulation-status');
    simulationStatus.innerHTML = '<p class="text-info">Resetting parameters to default values...</p>';

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

        // Update status
        simulationStatus.innerHTML =
            `<p class="text-success">Parameters for ${paramState.charAt(0).toUpperCase() + paramState.slice(1)} have been reset to default values.</p>`;
    })
    .catch(error => {
        console.error('Error resetting parameters:', error);
        simulationStatus.innerHTML =
            `<p class="text-danger">Error resetting parameters: ${error.message}</p>`;
    });
}

// Function to update the charts based on form selections
function updateChart() {
    // Get all checked states
    const stateCheckboxes = document.querySelectorAll('.state-checkbox:checked');
    const selectedStates = Array.from(stateCheckboxes).map(cb => cb.value);

    // Enforce maximum of 3 states
    if (selectedStates.length > MAX_STATES) {
        document.getElementById('state-selection-warning').textContent =
            `Maximum ${MAX_STATES} states can be selected. Please deselect some states.`;
        return;
    } else {
        document.getElementById('state-selection-warning').textContent = '';
    }

    // If no states selected, show message
    if (selectedStates.length === 0) {
        document.getElementById('charts-container').innerHTML =
            '<div class="col-md-12 text-center py-5 text-muted"><p>Please select at least one state to display data.</p></div>';
        return;
    }

    // Set current state for parameter tweaking (use the first selected state)
    currentState = selectedStates[0];

    // Get all checked variables
    const checkboxes = document.querySelectorAll('.variable-checkbox:checked');
    const selectedColumns = Array.from(checkboxes).map(cb => cb.value);

    // If no variables selected, show message
    if (selectedColumns.length === 0) {
        document.getElementById('charts-container').innerHTML =
            '<div class="col-md-12 text-center py-5 text-muted"><p>Please select at least one variable to display.</p></div>';
        return;
    }

    // Show loading message
    document.getElementById('charts-container').innerHTML =
        '<div class="col-md-12 text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Loading data...</p></div>';

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
        renderCharts(data, selectedStates);

        // Reset simulation status
        document.getElementById('simulation-status').innerHTML =
            '<p class="text-muted">Run a simulation with modified parameters to see results.</p>';
        simulatedChartData = null;
    })
    .catch(error => {
        console.error('Error fetching data:', error);
        document.getElementById('charts-container').innerHTML =
            `<div class="col-md-12 text-center py-5 text-danger"><p>Error loading data: ${error.message || 'Unknown error'}</p></div>`;
    });
}

// Function to run a simulation with modified parameters
function runSimulation() {
    // Show loading message
    document.getElementById('simulation-status').innerHTML =
        '<p class="text-primary">Running simulation... This may take a moment.</p>';

    // Get all checked variables
    const checkboxes = document.querySelectorAll('.variable-checkbox:checked');
    const selectedColumns = Array.from(checkboxes).map(cb => cb.value);

    // If no variables selected, show message
    if (selectedColumns.length === 0) {
        document.getElementById('simulation-status').innerHTML =
            '<p class="text-danger">Please select at least one variable to display in the chart.</p>';
        return;
    }

    // Get all checked states
    const stateCheckboxes = document.querySelectorAll('.state-checkbox:checked');
    const selectedStates = Array.from(stateCheckboxes).map(cb => cb.value);

    // If no states selected, show message
    if (selectedStates.length === 0) {
        document.getElementById('simulation-status').innerHTML =
            '<p class="text-danger">Please select at least one state to display data.</p>';
        return;
    }

    // Get the state selected for parameter modification
    const paramStateSelect = document.getElementById('parameter-state-select');
    const paramState = paramStateSelect ? paramStateSelect.value : currentState;

    // Check if the parameter state is among the selected states for display
    if (!selectedStates.includes(paramState)) {
        document.getElementById('simulation-status').innerHTML =
            `<p class="text-warning">The state selected for parameter modification (${paramState.charAt(0).toUpperCase() + paramState.slice(1)}) is not selected for display. Please select it in the chart settings.</p>`;
        return;
    }

    // Collect parameters from form
    const parameters = collectParameters();

    // Run simulation for the selected parameter state
    fetch(window.location.origin + '/simulate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            state: paramState,
            columns: selectedColumns,
            parameters: parameters,
            years: 76 // Simulation from 2024 to 2100
        }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Error running simulation');
            });
        }
        return response.json();
    })
    .then(data => {
        // Check if there's an error message in the response
        if (data.error) {
            throw new Error(data.error);
        }

        simulatedChartData = data;

        // Get the state selected for parameter modification
        const paramStateSelect = document.getElementById('parameter-state-select');
        const paramState = paramStateSelect ? paramStateSelect.value : currentState;

        // Group simulated datasets by unit type
        const simulatedDatasetGroups = groupDatasetsByUnit(simulatedChartData.datasets);

        // Update the energy & emissions chart
        const energyEmissionsChartId = `chart-${paramState}-energy_emissions`;
        if (charts[energyEmissionsChartId]) {
            // Get power and emissions datasets from simulated data
            const powerDatasets = simulatedDatasetGroups['power']?.datasets || [];
            const emissionsDatasets = simulatedDatasetGroups['emissions']?.datasets || [];

            // Assign each dataset to its appropriate y-axis
            powerDatasets.forEach(dataset => {
                dataset.yAxisID = 'y';
            });

            emissionsDatasets.forEach(dataset => {
                dataset.yAxisID = 'y1';
            });

            // Get only the original datasets (not previous simulations)
            // Filter out any datasets that have "Simulated" in their label
            const originalDatasets = charts[energyEmissionsChartId].data.datasets.filter(
                dataset => !dataset.label.includes('Simulated')
            );

            // Merge with simulated datasets
            const mergedDatasets = [...originalDatasets, ...powerDatasets, ...emissionsDatasets];

            // Update the chart
            charts[energyEmissionsChartId].data.datasets = mergedDatasets;
            charts[energyEmissionsChartId].update();
        }

        // Update the quantities chart
        const quantitiesChartId = `chart-${paramState}-quantities`;
        if (charts[quantitiesChartId] && simulatedDatasetGroups['vehicles'] && simulatedDatasetGroups['vehicles'].datasets.length > 0) {
            // Get only the original datasets (not previous simulations)
            // Filter out any datasets that have "Simulated" in their label
            const originalDatasets = charts[quantitiesChartId].data.datasets.filter(
                dataset => !dataset.label.includes('Simulated')
            );

            // Merge with simulated datasets
            const mergedDatasets = [...originalDatasets, ...simulatedDatasetGroups['vehicles'].datasets];

            // Update the chart
            charts[quantitiesChartId].data.datasets = mergedDatasets;
            charts[quantitiesChartId].update();
        }

        // Update simulation status
        document.getElementById('simulation-status').innerHTML =
            `<p class="text-success">Simulation complete for ${paramState.charAt(0).toUpperCase() + paramState.slice(1)} (2024-2100)! Dashed lines show simulated data with modified parameters.</p>`;
    })
    .catch(error => {
        console.error('Error running simulation:', error);
        document.getElementById('simulation-status').innerHTML =
            `<p class="text-danger">Error running simulation: ${error.message || 'Please try again with different parameters.'}</p>`;
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
        const datasetGroups = groupDatasetsByUnit(datasets);

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

            // Create chart
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
                  label.includes('icecav') || label.includes('sti') || label.includes('infra')) {
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