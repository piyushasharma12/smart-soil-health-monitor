Author Piyusha sharma 
Smart Soil Health Monitor 

from flask import Flask, request, jsonify, render_template, Response
from datetime import datetime, timezone
import sqlite3
import math
import json
import urllib.request
import urllib.error
import csv
import io
import threading
import time

app = Flask(__name__)


API_KEY = "soil-demo-change-this-to-a-long-random-secret"
DATABASE = "soil_data.db"

LOCATION = "Amritsar, Punjab"
LATITUDE = 31.6223
LONGITUDE = 74.8753

WEATHER_UPDATE_INTERVAL = 100  # seconds


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS soil_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                moisture_raw REAL,
                ph_raw REAL,
                ec_raw REAL,
                soil_temperature REAL,
                air_temperature REAL,
                humidity REAL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS weather_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                location TEXT,
                air_temperature REAL,
                humidity REAL,
                soil_temperature REAL,
                soil_moisture REAL,
                source TEXT
            )
        """)

        connection.commit()

    finally:
        connection.close()




def current_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def check_api_key():
    return request.headers.get("X-API-Key") == API_KEY


def get_open_meteo_data():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}"
        f"&longitude={LONGITUDE}"
        "&current=temperature_2m,relative_humidity_2m"
        "&hourly=temperature_2m,relative_humidity_2m,"
        "soil_temperature_0cm,soil_moisture_0_to_1cm"
        "&timezone=Asia%2FKolkata"
        "&forecast_days=1"
    )

    api_request = urllib.request.Request(
        url,
        headers={"User-Agent": "Punjab-Soil-Monitor/1.0"}
    )

    with urllib.request.urlopen(api_request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_and_save_weather():
    data = get_open_meteo_data()

    current = data.get("current", {})
    hourly = data.get("hourly", {})

    # Prefer the current hour's soil estimates.
    hourly_times = hourly.get("time", [])
    current_time = current.get("time")

    if current_time in hourly_times:
        index = hourly_times.index(current_time)
    else:
        index = 0

    def hourly_value(key):
        values = hourly.get(key, [])
        if index < len(values):
            return values[index]
        return None

    air_temperature = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    soil_temperature = hourly_value("soil_temperature_0cm")
    soil_moisture = hourly_value("soil_moisture_0_to_1cm")

    # Save the weather response time when available.
    timestamp = current.get("time") or current_timestamp()

    connection = get_db_connection()

    try:
        connection.execute("""
            INSERT INTO weather_readings (
                timestamp,
                location,
                air_temperature,
                humidity,
                soil_temperature,
                soil_moisture,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            LOCATION,
            air_temperature,
            humidity,
            soil_temperature,
            soil_moisture,
            "Open-Meteo estimate"
        ))

        connection.commit()

    finally:
        connection.close()

    return {
        "success": True,
        "message": "Weather estimate saved successfully",
        "timestamp": timestamp,
        "location": LOCATION,
        "air_temperature": air_temperature,
        "humidity": humidity,
        "soil_temperature": soil_temperature,
        "soil_moisture": soil_moisture,
        "source": "Open-Meteo estimate"
    }



@app.route("/")
def index():
    return render_template("index.html")




@app.route("/api/readings", methods=["POST"])
def add_reading():
    if not check_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized: invalid API key"
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "A valid JSON object is required"
        }), 400

    allowed_fields = [
        "moisture_raw",
        "ph_raw",
        "ec_raw",
        "soil_temperature",
        "air_temperature",
        "humidity"
    ]

    values = {}

    for field in allowed_fields:
        value = data.get(field)

        if value is None or value == "":
            values[field] = None
            continue

        try:
            number = float(value)
            if not math.isfinite(number):
                raise ValueError
            values[field] = number
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "error": f"{field} must be a valid number or null"
            }), 400

    connection = get_db_connection()

    try:
        cursor = connection.execute("""
            INSERT INTO soil_readings (
                timestamp,
                moisture_raw,
                ph_raw,
                ec_raw,
                soil_temperature,
                air_temperature,
                humidity
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            current_timestamp(),
            values["moisture_raw"],
            values["ph_raw"],
            values["ec_raw"],
            values["soil_temperature"],
            values["air_temperature"],
            values["humidity"]
        ))

        connection.commit()
        reading_id = cursor.lastrowid

    finally:
        connection.close()

    return jsonify({
        "success": True,
        "message": "Sensor reading saved",
        "id": reading_id
    }), 201



@app.route("/manual-reading", methods=["POST"])
def manual_reading():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "A valid JSON object is required"
        }), 400

    allowed_fields = [
        "moisture_raw",
        "ph_raw",
        "ec_raw",
        "soil_temperature",
        "air_temperature",
        "humidity"
    ]

    values = {}

    for field in allowed_fields:
        value = data.get(field)

        if value is None or value == "":
            values[field] = None
            continue

        try:
            number = float(value)
            if not math.isfinite(number):
                raise ValueError
            values[field] = number
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "error": f"{field} must be a valid number or null"
            }), 400

    connection = get_db_connection()

    try:
        cursor = connection.execute("""
            INSERT INTO soil_readings (
                timestamp,
                moisture_raw,
                ph_raw,
                ec_raw,
                soil_temperature,
                air_temperature,
                humidity
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            current_timestamp(),
            values["moisture_raw"],
            values["ph_raw"],
            values["ec_raw"],
            values["soil_temperature"],
            values["air_temperature"],
            values["humidity"]
        ))

        connection.commit()
        reading_id = cursor.lastrowid

    finally:
        connection.close()

    return jsonify({
        "success": True,
        "message": "Manual sensor reading saved",
        "id": reading_id
    }), 201



@app.route("/api/readings", methods=["GET"])
def get_readings():
    connection = get_db_connection()

    try:
        rows = connection.execute("""
            SELECT *
            FROM soil_readings
            ORDER BY id DESC
            LIMIT 100
        """).fetchall()

        readings = [dict(row) for row in rows]

    finally:
        connection.close()

    return jsonify(readings)




@app.route("/api/readings.csv", methods=["GET"])
def export_readings_csv():
    connection = get_db_connection()

    try:
        rows = connection.execute("""
            SELECT *
            FROM soil_readings
            ORDER BY id DESC
        """).fetchall()

    finally:
        connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Timestamp",
        "Moisture Raw",
        "pH Raw",
        "EC Raw",
        "Soil Temperature",
        "Air Temperature",
        "Humidity"
    ])

    for row in rows:
        writer.writerow([
            row["id"],
            row["timestamp"],
            row["moisture_raw"],
            row["ph_raw"],
            row["ec_raw"],
            row["soil_temperature"],
            row["air_temperature"],
            row["humidity"]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=sensor_readings.csv"
        }
    )




@app.route("/api/fetch-weather", methods=["POST"])
def fetch_weather():
    if not check_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized: invalid API key"
        }), 401

    try:
        result = fetch_and_save_weather()
        return jsonify(result), 200

    except Exception as error:
        app.logger.exception("Weather fetch failed")

        return jsonify({
            "success": False,
            "error": "Could not fetch weather data",
            "details": str(error)
        }), 502



@app.route("/api/weather-readings", methods=["GET"])
def get_weather_readings():
    connection = get_db_connection()

    try:
        rows = connection.execute("""
            SELECT *
            FROM weather_readings
            ORDER BY id DESC
            LIMIT 100
        """).fetchall()

        readings = [dict(row) for row in rows]

    finally:
        connection.close()

    return jsonify(readings)



@app.route("/api/weather-readings.csv", methods=["GET"])
def export_weather_csv():
    connection = get_db_connection()

    try:
        rows = connection.execute("""
            SELECT *
            FROM weather_readings
            ORDER BY id DESC
        """).fetchall()

    finally:
        connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Timestamp",
        "Location",
        "Air Temperature",
        "Humidity",
        "Soil Temperature",
        "Soil Moisture",
        "Source"
    ])

    for row in rows:
        writer.writerow([
            row["id"],
            row["timestamp"],
            row["location"],
            row["air_temperature"],
            row["humidity"],
            row["soil_temperature"],
            row["soil_moisture"],
            row["source"]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=weather_readings.csv"
        }
    )



def automatic_weather_updates():
    while True:
        time.sleep(WEATHER_UPDATE_INTERVAL)

        try:
            # Fetch directly rather than calling the local HTTP endpoint.
            result = fetch_and_save_weather()
            print(
                "Automatic weather update successful:",
                result
            )

        except Exception:
            app.logger.exception(
                "Automatic weather update failed"
            )




initialize_database()


if __name__ == "__main__":
    threading.Thread(
        target=automatic_weather_updates,
        daemon=True
    ).start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )
