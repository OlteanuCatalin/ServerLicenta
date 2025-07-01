from imports import *
from pins import *
import utime
import urequests
import network
import socket
import os
import ujson

# LPG Thresholds (PPM)
LPG_ALERT = 1000
LPG_CRITICAL = 2000

# CO Thresholds (PPM)
CO_ALERT = 50
CO_CRITICAL = 200

# Methane Thresholds (PPM)
METHANE_ALERT = 5000
METHANE_CRITICAL = 50000
SERVER = "http://172.20.10.6:5000/gas"


def send_data():
    LPG, CO, Methane = get_gas_concentration()
    print(f"DEBUG: Sending - LPG: {LPG:.2f}, CO: {CO:.2f}, Methane: {Methane:.2f}")  # Debug Print
    data = {"LPG": LPG, "CO": CO, "Methane": Methane}
    
    try:
        response = urequests.post(SERVER, json=data, timeout = 40)
        print("Server Response:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send data:", e)


def LED_control():
    
    LPG, CO, Methane = get_gas_concentration()
         # Control LEDs for LPG
    if LPG >= LPG_CRITICAL:
        lpg_led_critical.on()
        lpg_led_alert.on()
        lpg_led_normal.on()
    elif LPG >= LPG_ALERT:
        lpg_led_critical.off()
        lpg_led_alert.on()
        lpg_led_normal.on()
    else:
        lpg_led_critical.off()
        lpg_led_alert.off()
        lpg_led_normal.on()

    # Control LEDs for CO
    if CO >= CO_CRITICAL:
        co_led_critical.on()
        co_led_alert.on()
        co_led_normal.on()
    elif CO >= CO_ALERT:
        co_led_critical.off()
        co_led_alert.on()
        co_led_normal.on()
    else:
        co_led_critical.off()
        co_led_alert.off()
        co_led_normal.on()
        
    # Control LEDs for Methane
    if Methane >= METHANE_CRITICAL:
        methane_led_critical.on()
        methane_led_alert.on()
        methane_led_normal.on()
    elif Methane >= METHANE_ALERT:
        methane_led_critical.off()
        methane_led_alert.on()
        methane_led_normal.on()
    else:
        methane_led_critical.off()
        methane_led_alert.off()
        methane_led_normal.on()
          

def get_gas_concentration(samples = 5):
    total_mq7 = 0
    total_mq6 = 0
    total_mq4 = 0

    for _ in range(samples):
        total_mq7 += mq7.read_u16()
        total_mq6 += mq6.read_u16()
        total_mq4 += mq4.read_u16()
        utime.sleep_ms(50)
        
    raw_value_mq7 = total_mq7 / samples
    raw_value_mq6 = total_mq6 / samples
    raw_value_mq4 = total_mq4 / samples    
    
        
    voltage_mq7 = (raw_value_mq7 / 65535) * 3.3
    voltage_mq6 = (raw_value_mq6 / 65535) * 3.3
    voltage_mq4 = (raw_value_mq4 / 65535) * 3.3
    
    RL_mq47 = 1  # Load resistance in kΩ for MQ4 and MQ7 sensors
    RL_mq6 = 2  # Load resistance in kΩ for MQ6 sensor

    RS_mq7 = (3.3 - voltage_mq7) / voltage_mq7 * RL_mq47
    RS_mq6 = (3.3 - voltage_mq6) / voltage_mq6 * RL_mq6
    RS_mq4 = (3.3 - voltage_mq4) / voltage_mq4 * RL_mq47
    
    R0 = 1  # This should be pre-calibrated in clean air, the same for all the sensors
    
    ratio_mq7 = RS_mq7 / R0
    ratio_mq6 = RS_mq6 / R0
    ratio_mq4 = RS_mq4 / R0

    # Gas estimation (example values, adjust based on datasheet)
    LPG_ppm = 1000 * (ratio_mq6 ** -2.2)
    CO_ppm = 500 * (ratio_mq7 ** -1.9)
    Methane_ppm = 2000 * (ratio_mq4 ** -2.0)

    return LPG_ppm, CO_ppm, Methane_ppm

# Function to Display Sensor Data with Timestamp
def display_sensor_data():
       
    LPG, CO, Methane = get_gas_concentration()
    
    # Get current time
    current_time = utime.localtime()
    time_str = "{:02d}:{:02d}:{:02d}".format(current_time[3], current_time[4], current_time[5])
    
    display.fill_rectangle(0, 0, 160, 240,0x0000)

    # Set cursor and print sensor data
    display.set_pos(10,20)
    display.print(f"Air quality parameters")
    
    # Set cursor and print time
    display.set_pos(10, 80)
    display.print(f"Time: {time_str}")
    
    display.set_pos(10, 110)
    display.print(f"LPG: {LPG:.1f} ppm")
    
    display.set_pos(10, 140)
    display.print(f"CO: {CO:.1f} ppm")

    display.set_pos(10, 170)
    display.print(f"Methane: {Methane:.1f} ppm")
    
    display.set_pos(10,190)
    if LPG >= LPG_CRITICAL or CO >= CO_CRITICAL or Methane >= METHANE_CRITICAL:
        display.print("!CRITICAL GAS LEVEL!")  
    elif LPG >= LPG_ALERT or CO >= CO_ALERT or Methane >= METHANE_ALERT:
        display.print("!ALERT: Elevated Gas Levels!") 

def display_gas_graphs(MAX_PPM):
        
        LPG, CO, Methane = get_gas_concentration()
        def scale_ppm(ppm, max_value):
            return int((ppm/max_value)*200)
        
        lpg_width = scale_ppm(min(LPG, MAX_PPM), MAX_PPM)
        co_width = scale_ppm(min(CO, MAX_PPM), MAX_PPM)
        methane_width = scale_ppm(min(Methane, MAX_PPM), MAX_PPM)

        # Colors based on alert levels
        def get_color(value, alert, critical):
            if value >= critical:
                return 0xF800  # Red
            elif value >= alert:
                return 0xFFE0  # Yellow
            else:
                return 0x07E0  # Green
        LPG_COLOR = get_color(LPG, LPG_ALERT, LPG_CRITICAL)
        CO_COLOR = get_color(CO, CO_ALERT, CO_CRITICAL)
        METHANE_COLOR = get_color(Methane, METHANE_ALERT, METHANE_CRITICAL)
        BACKGROUND_COLOR = 0x0000  # Black

        LPG_Y = 40
        CO_Y = 100
        METHANE_Y = 160

        display.fill_rectangle(160, 0, 160, 240, BACKGROUND_COLOR)
        
        display.set_pos(170,20)
        display.print(f"LPG Concentration")
        display.fill_rectangle(160, LPG_Y, lpg_width, 30, LPG_COLOR)  # LPG bar
        display.set_pos(160+lpg_width, LPG_Y + 10)
        display.print(f"{int(LPG)} ppm")
        
        display.set_pos(170,80)
        display.print(f"CO Concentration")
        display.fill_rectangle(160, CO_Y, co_width, 30, CO_COLOR)  # CO bar
        display.set_pos(160+co_width, CO_Y + 10)
        display.print(f"{int(CO)} ppm")


        display.set_pos(170,140)
        display.print(f"Methane Concentration")
        display.fill_rectangle(160, METHANE_Y, methane_width, 30, METHANE_COLOR)  # Methane bar    
        display.set_pos(160+methane_width, METHANE_Y + 10)
        display.print(f"{int(Methane)} ppm")
        
def init_sdcard():
    try:
        sd = sdcard.SDCard(spi1, cs_sd)
        os.mount(sd, "/sd")
        os.listdir('/')
        print("SD card mounted at /sd")
        return sd
    except Exception as e:
        print("Failed to mount SD card:", e)
        return None
    
def log_to_sd(LPG, CO, Methane):
    try:
        # Check if /sd is mounted
        if "/sd" not in os.listdir("/"):
            print("SD not mounted. Skipping log.")
            return

        # Create log file if not exists (optional)
        log_file = "/sd/gas_log.csv"
        if log_file not in os.listdir("/sd"):
            with open(log_file, "w") as f:
                f.write("Time,LPG,CO,Methane\n")  # Header

        timestamp = utime.localtime()
        time_str = "{:02d}:{:02d}:{:02d}".format(timestamp[3], timestamp[4], timestamp[5])
        with open(log_file, "a") as f:
            f.write(f"{time_str},{LPG:.2f},{CO:.2f},{Methane:.2f}\n")

    except Exception as e:
        print("SD log failed:", e)
        
def handle_request(client):
    req = client.recv(1024)
    req_str = req.decode()
    json_start = req_str.find("\r\n\r\n") + 4
    try:
        data = ujson.loads(req_str[json_start:])
        LPG = float(data.get("LPG", 0))
        CO = float(data.get("CO", 0))
        Methane = float(data.get("Methane", 0))

        if LPG > LPG_ALERT or CO > CO_ALERT or Methane > METHANE_ALERT:
            alert_pin.on()
        else:
            alert_pin.off()
        client.send("HTTP/1.1 200 OK\r\n\r\nOK")
    except Exception as e:
        client.send("HTTP/1.1 400 Bad Request\r\n\r\n")
    client.close()