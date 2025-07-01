from imports import *

# Network Config Parameters
SSID = "DESKTOP-6VVSH47 7430"
PASSWORD = "2Wf6>683"
SERVER = "http://172.20.10.6:5000/gas"

# Initialize WIFI

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

print("Connecting to Wi-Fi...")
while not wlan.isconnected():
    time.sleep(1)
print("Connected! IP Address:", wlan.ifconfig()[0])
while not wlan.isconnected():
    time.sleep(1)

sd = functions.init_sdcard()
# Loop to Read Sensor and Update Display
while True:
    LPG, CO, Methane = functions.get_gas_concentration()
    print(f"LPG: {LPG:.2f} ppm, CO: {CO:.2f} ppm, Methane: {Methane:.2f} ppm")
    functions.LED_control()
    functions.display_gas_graphs(1500)
    functions.display_sensor_data()
    functions.send_data()
    functions.log_to_sd(LPG, CO, Methane)   
    utime.sleep(1)  # Update every second
    
