

**Author:** Piyusha Sharma  
**Project:** IoT-Based Real-Time Soil Health Monitoring System for Agricultural Fields in Punjab

## About the Project

The Smart Soil Health Monitor is a software prototype designed to support real-time soil and environmental monitoring for agricultural fields in Punjab. It uses a Flask-based web dashboard and an SQLite database to store and display readings.

The project also integrates Open-Meteo weather data to provide environmental estimates for the Amritsar region.

## Features

- Web-based monitoring dashboard
- Manual entry of soil readings
- SQLite database for storing records
- Weather data integration using Open-Meteo
- Automatic weather data updates
- CSV export for collected readings
- REST API endpoints for accessing data

## Technologies Used

- Python
- Flask
- SQLite
- HTML, CSS and JavaScript
- Open-Meteo API

## Project Structure

```text
smart-soil-health-monitor/
├── app.py
├── requirements.txt
├── README.md
└── templates/
    └── index.html
```

## How to Run the Project

1. Install Python on your computer.
2. Clone or download this repository.
3. Open a terminal in the project folder.
4. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

5. Run the application:

   ```bash
   python app.py
   ```

6. Open the local address shown in the terminal, usually `http://127.0.0.1:5000`.

## Current Project Status

**Completed:** Flask dashboard, SQLite storage, manual reading entry, weather data integration and CSV export.

