from flask import Flask, request, jsonify
import requests
import RPi.GPIO as GPIO
import time

# ThingsBoard's setting
THINGSBOARD_SERVER = "http://iot.scu.ac.ir:8080"
ACCESS_TOKEN = "e4xf74a3c9lupmarxnvi"

# set GPIO for raspberry sensors
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# define PINs
sensors = {
    "North": {"trigger": 20, "echo": 21},
    "East": {"trigger": 8, "echo": 7},
    "South": {"trigger": 15, "echo": 14},
    "West": {"trigger": 23, "echo": 24},
}
water_sensor = {"trigger": 17, "echo": 27}

for sensor in sensors.values():
    GPIO.setup(sensor["trigger"], GPIO.OUT)
    GPIO.setup(sensor["echo"], GPIO.IN)
GPIO.setup(water_sensor["trigger"], GPIO.OUT)
GPIO.setup(water_sensor["echo"], GPIO.IN)

app = Flask(__name__)

def get_distance(trigger, echo):
    GPIO.output(trigger, True)
    time.sleep(0.00001)
    GPIO.output(trigger, False)

    start_time = time.time()
    stop_time = time.time()

    while GPIO.input(echo) == 0:
        start_time = time.time()
    while GPIO.input(echo) == 1:
        stop_time = time.time()

    time_elapsed = stop_time - start_time
    distance = (time_elapsed * 34300) / 2
    return distance

def get_raspberry_data():
    distances = {direction: get_distance(pins["trigger"], pins["echo"]) for direction, pins in sensors.items()}
    wind_direction = min(distances, key=distances.get)
    
    water_distance = get_distance(water_sensor["trigger"], water_sensor["echo"])
    water_level = max(0, 255 - round(water_distance))
    return {
        "wind_direction": wind_direction,
        "water_level": water_level,
    }

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        sensor_data = request.json
        raspberry_data = get_raspberry_data()
        combined_data = {**sensor_data, **raspberry_data}
        print("Combined Data:", combined_data)

        url = f"{THINGSBOARD_SERVER}/api/v1/{ACCESS_TOKEN}/telemetry"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=combined_data, headers=headers)

        if response.status_code == 200:
            print("Data sent to ThingsBoard successfully.")
            return jsonify({"message": "Data sent to ThingsBoard successfully."}), 200
        else:
            print(f"Failed to send data: {response.status_code} {response.text}")
            return jsonify({"error": "Failed to send data to ThingsBoard"}), response.status_code

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

if name == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000)
    except KeyboardInterrupt:
        print("Cleaning up GPIO!")
        GPIO.cleanup()