# CLEAR-ATS Visualization Web Application

This web application provides an interactive visualization interface for the CLEAR-ATS (Automated Transport System) model data. It allows users to select different states/regions and variables to display in a line chart.

## Features

- Interactive line charts for visualizing ATS model data
- Support for multiple states/regions (California, Ohio, US Average)
- Ability to select multiple variables for comparison
- Toggle between linear and logarithmic scales
- Responsive design for desktop and mobile devices

## Project Structure

```
CLEAR-ATS-VIS/
├── app.py                  # Flask application
├── footprint_model.py      # ATS model implementation
├── requirements.txt        # Python dependencies
├── configs/                # Configuration files for different states
│   ├── california.json
│   ├── ohio.json
│   ├── us_average.json
│   └── common.json
├── results/                # CSV output from the model
│   ├── california_ats_model_2024_2124.csv
│   ├── ohio_ats_model_2024_2124.csv
│   └── us_average_ats_model_2024_2124.csv
├── static/                 # Static assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── templates/              # HTML templates
    └── index.html
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd CLEAR-ATS-VIS
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. Make sure you have generated the model results:
   ```
   python footprint_model.py
   ```

2. Start the Flask application:
   ```
   python app.py
   ```

3. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Deployment

For production deployment, you can use Gunicorn:

```
gunicorn app:app
```

Or deploy to platforms like Heroku, AWS, or Google Cloud Platform.

## Customization

- To add new states/regions, create a new JSON configuration file in the `configs` directory and update the model.
- To modify the chart appearance, edit the CSS and JavaScript files in the `static` directory.
- To change the page layout, modify the HTML templates in the `templates` directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.