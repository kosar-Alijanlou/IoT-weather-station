import network
import urequests
import time
import json
from machine import Pin, ADC
import dht

# WiFi setting
SSID = "username"
PASSWORD = "password"

SERVER_URL = "http://192.168.0.0:5000/data"  # Flask server address

# sensors PINs
ldr_pin = 35
mq135_pin = 32
flame_pin = 33
dht_pin = 18

# PIN settings
ldr = ADC(Pin(ldr_pin))
ldr.atten(ADC.ATTN_11DB)
mq135 = ADC(Pin(mq135_pin))
mq135.atten(ADC.ATTN_11DB)
flame = Pin(flame_pin, Pin.IN)
dht_sensor = dht.DHT11(Pin(dht_pin))

# WiFi connection
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print("Connected to WiFi")
    print("IP Address:", wlan.ifconfig()[0])

# reading sensors' data
def get_sensor_data():
    try:
        #read data from DHT11
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
        
        # read data from LDR and MQ135
        ldr_value = ldr.read()
        mq135_value = mq135.read()
        
        # read data from flame sensor
        flame_detected = flame.value() == 0  # 0 means flame detected
        
        return {
            "sensor_id": "ESP32_1",
            "ldr": ldr_value,
            "mq135": mq135_value,
            "flame": flame_detected,
            "temperature": temperature,
            "humidity": humidity
        }
    except Exception as e:
        print("Error reading sensors:", e)
        return None

# sending data to server
def send_data(data):
    try:
        headers = {'Content-Type': 'application/json'}
        response = urequests.post(SERVER_URL, data=json.dumps(data), headers=headers)
        print("Response:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send data:", e)

# Run program
def main():
    connect_wifi()
    while True:
        sensor_data = get_sensor_data()
        if sensor_data:
            print("Sending data:", sensor_data)
            send_data(sensor_data)
        time.sleep(2)  

if __name__ == "__main__":
    main()

