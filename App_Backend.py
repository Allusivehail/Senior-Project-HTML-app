from flask import Flask, request, jsonify, render_template, send_file
import socket
import serial
import csv
import json
import time, traceback
import threading
import datetime
import cv2
import board
import neopixel_spi as neopixel
import os
import glob
import pandas as pd
from paho.mqtt import client as mqtt_client

# ---------------- SERIAL ---------------- #

ser = None
serial_lock = threading.Lock()
current_port = None

# ---------------- MQTT (unchanged placeholders) ---------------- #

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(
        client_id=client_id,
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
    )
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client, msg):
    result = client.publish(topic, msg)
    if result[0] == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

# ---------------- SERIAL FUNCTIONS ---------------- #

def find_arduino_port():
    ports = glob.glob('/dev/ttyACM*')
    return ports[0] if ports else None


def open_serial():
    global ser, current_port

    try:
        port = find_arduino_port()

        if port is None:
            print("No Arduino port found")
            ser = None
            return

        if current_port == port and ser and ser.is_open:
            return

        if ser:
            try:
                ser.close()
            except:
                pass

        ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(2)

        current_port = port
        print(f"Connected to Arduino on {port}")

    except Exception as e:
        print(f"Serial open failed: {e}")
        ser = None
        current_port = None


def get_ser():
    global ser

    if ser is None:
        open_serial()
        return ser

    try:
        ser.in_waiting
    except:
        print("Serial lost — reconnecting...")
        open_serial()

    return ser


def safe_ser_write(data):
    with serial_lock:
        try:
            s = get_ser()
            if s:
                s.write(data)
        except Exception as e:
            print(f"Write failed: {e}")
            open_serial()


def serial_monitor():
    global current_port

    while True:
        try:
            port = find_arduino_port()

            if port is None:
                if ser:
                    print("Arduino disconnected")
                open_serial()
                time.sleep(1)
                continue

            if port != current_port:
                print(f"Port switch detected: {current_port} → {port}")
                open_serial()

        except Exception as e:
            print(f"Serial monitor error: {e}")

        time.sleep(1)


threading.Thread(target=serial_monitor, daemon=True).start()

# ---------------- FLASK APP ---------------- #

app = Flask(__name__)

# =========================
# ✅ FIXED PATHS
# =========================
CSV_PATH = "/home/mert/app_gui/inventory_data/yolo_temp.csv"
ARDUINO_LOG_PATH = "/home/mert/app_gui/inventory_data/arduino_log.csv"  # ✅ NEW

# ---------------- UI ROUTES ---------------- #

@app.route("/")
def root():
    return render_template("newDash.html")


@app.route("/inventory")
def inventory():
    return render_template("inventory.html")

@app.route("/testing")
def testing():
    return render_template("testing.html")

# ---------------- MOTOR ---------------- #

motorFridge = '1\n'
motorRoom = '2\n'
motorStop = '3\n'


@app.route("/motorfridge")
def motor_fridge():
    safe_ser_write(motorFridge.encode())
    return "Running Fridge Motor", 200


@app.route("/motorroom")
def motor_room():
    safe_ser_write(motorRoom.encode())
    return "Running Room Motor", 200


@app.route("/motorstop")
def motor_stop():
    safe_ser_write(motorStop.encode())
    return "Stopping all motors", 200

# ---------------- DEBUG SEQUENCE ---------------- #
@app.route('/api/run-debug', methods=['POST'])
def run_debug():
    data = request.get_json()

    if not data or 'action' not in data:
        return jsonify({"message": "Invalid request"}), 400

    if data['action'] == 'run_program':
        try:
            s = get_ser()
            if not s:
                return jsonify({"message": "Arduino not connected"}), 500

            # -----------------------------
            # STEP 1: FRIDGE MOTOR (5 sec)
            # -----------------------------
            print("Starting fridge motor")
            safe_ser_write(motorFridge.encode())

            for _ in range(50):  # 5 seconds (0.1 * 50)
                time.sleep(0.1)
                if not get_ser():
                    return jsonify({"message": "Arduino disconnected during fridge test"}), 500

            # STOP after fridge
            safe_ser_write(motorStop.encode())
            time.sleep(1)

            # -----------------------------
            # STEP 2: ROOM MOTOR (5 sec)
            # -----------------------------
            print("Starting room motor")
            safe_ser_write(motorRoom.encode())

            for _ in range(50):  # 5 seconds
                time.sleep(0.1)
                if not get_ser():
                    return jsonify({"message": "Arduino disconnected during room test"}), 500

            # STOP after room
            safe_ser_write(motorStop.encode())
            time.sleep(1)

            # -----------------------------
            # FINAL STOP (safety)
            # -----------------------------
            safe_ser_write(motorStop.encode())

            return jsonify({
                "message": "Test has finished or was ended early."
            }), 200

        except Exception as e:
            traceback.print_exc()
            return jsonify({"message": str(e)}), 500

    return jsonify({"message": "Unknown action"}), 400
    
# ---------------- LED ---------------- #

NUM_PIXELS = 16
PIXEL_ORDER = neopixel.RGBW
WHITE = 0xFFFFFF
OFF = 0x000000

spi = board.SPI()
pixels = neopixel.NeoPixel_SPI(
    spi, NUM_PIXELS,
    pixel_order=PIXEL_ORDER,
    auto_write=False
)

# ---------------- CAMERA ---------------- #

def cameraTrigger():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise IOError("Cannot open webcam")

    pixels.fill(WHITE)
    pixels.show()

    ret, frame = cap.read()

    if ret:
        cv2.imwrite('./static/IMG/http_test_image.png', frame)

    pixels.fill(OFF)
    pixels.show()
    cap.release()


@app.route("/imageShow")
def image_show():
    return send_file('./static/IMG/http_test_image.png', mimetype='image/png')


@app.route('/api/capture-image')
def capture_image():
    try:
        cameraTrigger()

        image_url = request.host_url + "static/IMG/http_test_image.png"

        return jsonify({
            "message": "Image captured successfully",
            "image_url": image_url
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": str(e)}), 500

# ---------------- CSV ---------------- #

def read_csv():
    try:
        if not os.path.exists(CSV_PATH):
            print("CSV NOT FOUND:", CSV_PATH)
            return []

        df = pd.read_csv(CSV_PATH)

        # ✅ DEBUG
        print("CSV COLUMNS:", df.columns.tolist())

        expected_cols = ["Item", "Date In", "Expected Expiration"]

        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""

        data = []
        for i, row in df.iterrows():
            data.append({
                "id": int(i),            
                "Item": str(row["Item"]),
                "Date In": str(row["Date In"]),
                "Expected Expiration": str(row["Expected Expiration"])
            })

        return data

    except Exception as e:
        print("CSV ERROR:", e)
        return []

@app.route('/api/get-json')
def get_json():
    return jsonify({"data": read_csv()}), 200

@app.route('/api/add-row', methods=['POST'])
def add_row():
    try:
        data = request.get_json()

        new_row = pd.DataFrame([{
            "Item": data.get("Item", ""),
            "Date In": data.get("Date In", ""),
            "Expected Expiration": data.get("Expected Expiration", "")
        }])

        if os.path.exists(CSV_PATH):
            df = pd.read_csv(CSV_PATH)
        else:
            df = pd.DataFrame(columns=["Item", "Date In", "Expected Expiration"])

        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(CSV_PATH, index=False)

        return jsonify({"message": "added"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "error"}), 500

@app.route('/api/update-row', methods=['POST'])
def update_row():
    try:
        data = request.get_json()

        df = pd.read_csv(CSV_PATH)

        df.at[data["id"], "Item"] = data["Item"]
        df.at[data["id"], "Date In"] = data["Date In"]
        df.at[data["id"], "Expected Expiration"] = data["Expected Expiration"]

        df.to_csv(CSV_PATH, index=False)

        return jsonify({"message": "updated"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "error"}), 500

@app.route('/api/delete-row', methods=['POST'])
def delete_row():
    try:
        data = request.get_json()

        df = pd.read_csv(CSV_PATH)
        df = df.drop(index=data["id"]).reset_index(drop=True)
        df.to_csv(CSV_PATH, index=False)

        return jsonify({"message": "deleted"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "error"}), 500

# ---------------- ✅ FIXED ARDUINO LOGGING ---------------- #

def arduino_output():
    s = get_ser()
    if not s:
        return

    try:
        data = s.readline().decode('utf-8', errors='ignore').strip()

        if data:
            readings = data.split(",")

            # ✅ WRITE TO SEPARATE FILE (FIX)
            with open(ARDUINO_LOG_PATH, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(readings)

    except Exception as e:
        print(f"Read error: {e}")
        open_serial()

# ---------------- DEBUG ROUTE ---------------- #

@app.route('/api/debug-csv')
def debug_csv():
    return jsonify({
        "exists": os.path.exists(CSV_PATH),
        "path": CSV_PATH,
        "cwd": os.getcwd(),
        "dir_contents": os.listdir(os.path.dirname(CSV_PATH)) if os.path.exists(os.path.dirname(CSV_PATH)) else []
    })

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
