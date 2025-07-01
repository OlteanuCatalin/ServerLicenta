# train_model.py

import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib
import os

DB_PATH = "sensor_data.db"
MODEL_PATH = "gas_prediction_model.pkl"
LAGS = 3  

def load_sensor_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM sensor_data ORDER BY timestamp ASC", conn)
    conn.close()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df

def create_lagged_features(df, lags=LAGS):
    for lag in range(1, lags + 1):
        for col in ["LPG", "CO", "Methane"]:
            df[f"{col}_lag{lag}"] = df[col].shift(lag)
    df.dropna(inplace=True)
    return df

def train_model():
    print(" Loading data")
    df = load_sensor_data()

    print(" Creating features")
    df = create_lagged_features(df, LAGS)

    X = df[[col for col in df.columns if "lag" in col]]
    y = df[["LPG", "CO", "Methane"]]

    print(" Splitting data")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    print(" Training Random Forest")
    model = MultiOutputRegressor(RandomForestRegressor(n_estimators=100, random_state=42))
    model.fit(X_train, y_train)

    print(" Evaluating model")
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred, multioutput='raw_values')
    print(f" MAE - LPG: {mae[0]:.2f}, CO: {mae[1]:.2f}, Methane: {mae[2]:.2f}")

    joblib.dump(model, MODEL_PATH)
    print(" Model saved!")

if __name__ == "__main__":
    train_model()
