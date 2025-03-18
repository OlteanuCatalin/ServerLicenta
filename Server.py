from flask import Flask, request, render_template, jsonify
import sqlite3
from datetime import datetime
import pytz

app = Flask(__name__)

# Function to get local timestamp
def get_local_time():
    local_tz = pytz.timezone("Europe/Bucharest") 
    return datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")

@app.route("/")
def home():
    return render_template("index.html")  
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

@app.route("/gas", methods=["POST"])  
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

@app.route("/search_data", methods=["GET"])
def search_data():
    search_date = request.args.get("date")  
    page = int(request.args.get("page", 1)) 
    limit = 10  
    offset = (page - 1) * limit 

    conn = sqlite3.connect("sensor_data.db")
    cursor = conn.cursor()

    
    cursor.execute("""
        SELECT strftime('%H:%M', timestamp), LPG, CO, Methane 
        FROM mq2_sensor_data 
        WHERE DATE(timestamp) = ? 
        ORDER BY timestamp ASC 
        LIMIT ? OFFSET ?
    """, (search_date, limit, offset))
    mq2_data = cursor.fetchall()

   
    cursor.execute("SELECT COUNT(*) FROM mq2_sensor_data WHERE DATE(timestamp) = ?", (search_date,))
    total_records = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "mq2_sensor": [{"time": row[0], "LPG": row[1], "CO": row[2], "Methane": row[3]} for row in mq2_data],
        "total_records": total_records,
        "page": page,
        "total_pages": (total_records // limit) + (1 if total_records % limit > 0 else 0)
    })



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)