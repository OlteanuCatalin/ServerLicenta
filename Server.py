from flask import Flask, request, render_template, jsonify
import sqlite3
from datetime import datetime
import pytz

app = Flask(__name__)

# Function to get local timestamp
def get_local_time():
    local_tz = pytz.timezone("Europe/Bucharest")  # Change this to your local timezone
    return datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")

@app.route("/")
def home():
    return render_template("index.html")  # ✅ Graphs will be displayed here

@app.route("/display")
def display_data():
    conn = sqlite3.connect("sensor_data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM mq2_sensor_data ORDER BY timestamp DESC LIMIT 10")
    mq2_data = cursor.fetchall()

    cursor.execute("SELECT * FROM LPG_sensor_data ORDER BY timestamp DESC LIMIT 10")
    lpg_data = cursor.fetchall()

    cursor.execute("SELECT * FROM CO_sensor_data ORDER BY timestamp DESC LIMIT 10")
    co_data = cursor.fetchall()

    cursor.execute("SELECT * FROM Methane_sensor_data ORDER BY timestamp DESC LIMIT 10")
    methane_data = cursor.fetchall()

    conn.close()

    return render_template("display.html", mq2_data=mq2_data, lpg_data=lpg_data, co_data=co_data, methane_data=methane_data)

@app.route("/gas", methods=["POST"])  # ✅ Ensure "POST" is listed
def mq2_receive_data():
    data = request.json
    print(f"DEBUG: Received Gas Sensor Data - {data}")

    timestamp = get_local_time()
    LPG, CO, Methane = float(data["LPG"]), float(data["CO"]), float(data["Methane"])

    conn = sqlite3.connect("sensor_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mq2_sensor_data VALUES (?, ?, ?, ?)", (timestamp, LPG, CO, Methane))
    conn.commit()
    conn.close()

    print(f"Stored: Timestamp={timestamp}, LPG={LPG}, CO={CO}, Methane={Methane}")
    return "Gas Data Stored", 200

@app.route("/data")
def get_all_sensor_data():
    conn = sqlite3.connect("sensor_data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM mq2_sensor_data ORDER BY timestamp DESC LIMIT 10")
    mq2_data = cursor.fetchall()

    cursor.execute("SELECT * FROM LPG_sensor_data ORDER BY timestamp DESC LIMIT 10")
    lpg_data = cursor.fetchall()

    cursor.execute("SELECT * FROM CO_sensor_data ORDER BY timestamp DESC LIMIT 10")
    co_data = cursor.fetchall()

    cursor.execute("SELECT * FROM Methane_sensor_data ORDER BY timestamp DESC LIMIT 10")
    methane_data = cursor.fetchall()

    conn.close()

    return jsonify({
        "mq2_sensor": [{"timestamp": row[0], "LPG": row[1], "CO": row[2], "Methane": row[3]} for row in mq2_data],
        "lpg_sensor": [{"timestamp": row[0], "LPG": row[1]} for row in lpg_data],
        "co_sensor": [{"timestamp": row[0], "CO": row[1]} for row in co_data],
        "methane_sensor": [{"timestamp": row[0], "Methane": row[1]} for row in methane_data],
    })
