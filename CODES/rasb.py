from flask import Flask, request, jsonify, render_template
import requests
import RPi.GPIO as GPIO
import time

# set GPIO for raspberry sensors
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#define PINs
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

esp32_data = {}

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
    water_level = max(0, 260 - water_distance)
    return {
        "wind_direction": wind_direction,
        "water_level": water_level,
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        global esp32_data
        esp32_data = request.json
        print("Received ESP32 Data:", esp32_data)
        return jsonify({"message": "Data received successfully"}), 200
    except Exception as e:
        print("Error receiving data:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/live-data', methods=['GET'])
def live_data():
    try:
        raspberry_data = get_raspberry_data()
        combined_data = {**esp32_data, **raspberry_data}
        print("Live Data Sent to Web:", combined_data)  # sended data's log
        return jsonify(combined_data)
    except Exception as e:
        print("Error in /live-data:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except KeyboardInterrupt:
        print("Cleaning up GPIO!")
        GPIO.cleanup()
