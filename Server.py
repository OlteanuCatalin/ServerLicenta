from flask import Flask, request, render_template, jsonify
import sqlite3
from datetime import datetime
import pandas as pd
import pytz
from sklearn.model_selection import train_test_split
import joblib
import requests

PICO_IP = "http://192.168.137.206" 


def init_db():
    conn = sqlite3.connect("sensor_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            timestamp TEXT,
            LPG REAL,
            CO REAL,
            Methane REAL
        )
    """)
    conn.commit()
    conn.close()

app = Flask(__name__)
model = joblib.load("gas_prediction_model.pkl")
init_db()



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

    cursor.execute("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10")
    mq2_data = cursor.fetchall()

    conn.close()

    return render_template("display.html", mq2_data=mq2_data)
@app.route("/gas", methods=["POST"])  
def mq2_receive_data():
    data = request.json
    print(f"DEBUG: Received Gas Sensor Data - {data}")

    timestamp = get_local_time()
    LPG, CO, Methane = float(data["LPG"]), float(data["CO"]), float(data["Methane"])

    conn = sqlite3.connect("sensor_data.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sensor_data VALUES (?, ?, ?, ?)", (timestamp, LPG, CO, Methane))
    conn.commit()
    conn.close()

    print(f"Stored: Timestamp={timestamp}, LPG={LPG}, CO={CO}, Methane={Methane}")
    return "Gas Data Stored", 200
#
@app.route("/data")
def get_all_sensor_data():
    limit = int(request.args.get("limit", 10))  
    conn = sqlite3.connect("sensor_data.db")
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT {limit}")
    mq2_data = cursor.fetchall()

    conn.close()

    return jsonify({
        "mq2_sensor": [{"timestamp": row[0], "LPG": row[1], "CO": row[2], "Methane": row[3]} for row in mq2_data]
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
        FROM sensor_data 
        WHERE DATE(timestamp) = ? 
        ORDER BY timestamp ASC 
        LIMIT ? OFFSET ?
    """, (search_date, limit, offset))
    mq2_data = cursor.fetchall()

   
    cursor.execute("SELECT COUNT(*) FROM sensor_data WHERE DATE(timestamp) = ?", (search_date,))
    total_records = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "mq2_sensor": [{"time": row[0], "LPG": row[1], "CO": row[2], "Methane": row[3]} for row in mq2_data],
        "total_records": total_records,
        "page": page,
        "total_pages": (total_records // limit) + (1 if total_records % limit > 0 else 0)
    })

@app.route("/predict")
def predict_next():
    import pandas as pd
    import joblib

    model = joblib.load("gas_prediction_model.pkl")

    def load_data():
        conn = sqlite3.connect("sensor_data.db")
        df = pd.read_sql_query("SELECT * FROM sensor_data ORDER BY timestamp ASC", conn)
        conn.close()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        return df

    def create_lagged_features(df, lags=3):
        for lag in range(1, lags + 1):
            for col in ["LPG", "CO", "Methane"]:
                df[f"{col}_lag{lag}"] = df[col].shift(lag)
        df.dropna(inplace=True)
        return df

    df = load_data()
    df = create_lagged_features(df)
    input_row = df[[col for col in df.columns if 'lag' in col]].iloc[-1:]
    prediction = model.predict(input_row)[0]

    try:
        data_to_send = {
            "LPG": round(prediction[0], 2),
            "CO": round(prediction[1], 2),
            "Methane": round(prediction[2], 2)
        }
        response = requests.post(f"{PICO_IP}/", json=data_to_send, timeout=5)
        print("Sent to Pico W:", response.text)
    except Exception as e:
        print("Failed to send to Pico W:", e)


    return jsonify({
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "LPG": round(prediction[0], 2),
        "CO": round(prediction[1], 2),
        "Methane": round(prediction[2], 2)
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)