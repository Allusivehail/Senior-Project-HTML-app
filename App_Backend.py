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

app = Flask(__name__, template_folder="/home/mert/app_gui/templates")

# ---------------- SERIAL ---------------- #

ser = None
serial_lock = threading.Lock()
current_port = None

# ---------------- FILE ---------------- #

fileName = os.path.join(os.getcwd(), "do_not_touch.csv")

# Ensure CSV exists with headers
if not os.path.exists(fileName):
    df = pd.DataFrame(columns=["Item", "Date In", "Expected Expiration"])
    df.to_csv(fileName, index=False)

# ---------------- SERIAL FUNCTIONS ---------------- #

def find_arduino_port():
    ports = glob.glob('/dev/ttyACM*')
    return ports[0] if ports else None


def open_serial():
    global ser, current_port

    try:
        port = find_arduino_port()

        if port is None:
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


# ---------------- MOTOR COMMANDS ---------------- #

motorFridge = '1\n'
motorRoom = '2\n'
motorStop = '3\n'

# ---------------- FLASK ROUTES ---------------- #
@app.route("/")
def root():
    return render_template("dashboard.html")   # default landing page


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/inventory")
def inventory():
    return render_template("inventory.html")


@app.route("/logs")
def logs():
    return render_template("logs.html")


@app.route("/testing")
def testing():
    return render_template("testing.html")


# ---------------- GET CSV ---------------- #

@app.route('/api/get-json')
def send_table():
    try:
        if not os.path.exists(fileName):
            return jsonify([]), 200

        df = pd.read_csv(fileName)

        data = df.to_dict(orient="records")

        # add runtime index (NO CSV ID NEEDED)
        for i, row in enumerate(data):
            row["rowIndex"] = i

        return jsonify(data), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "JSON failed"}), 500


# ---------------- ADD ROW ---------------- #

@app.route('/api/add-row', methods=['POST'])
def add_row():
    try:
        data = request.get_json()

        new_row = pd.DataFrame([{
            "Item": data["Item"],
            "Date In": data["Date In"],
            "Expected Expiration": data["Expected Expiration"]
        }])

        df = pd.read_csv(fileName)
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(fileName, index=False)

        return jsonify({"message": "added"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "error"}), 500


# ---------------- UPDATE ROW ---------------- #

@app.route('/api/update-row', methods=['POST'])
def update_row():
    try:
        data = request.get_json()
        index = data['id']

        df = pd.read_csv(fileName)

        df.at[index, "Item"] = data["Item"]
        df.at[index, "Date In"] = data["Date In"]
        df.at[index, "Expected Expiration"] = data["Expected Expiration"]

        df.to_csv(fileName, index=False)

        return jsonify({"message": "updated"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "error"}), 500


# ---------------- DELETE ROW ---------------- #

@app.route('/api/delete-row', methods=['POST'])
def delete_row():
    try:
        data = request.get_json()
        index = data['id']

        df = pd.read_csv(fileName)
        df = df.drop(index=index).reset_index(drop=True)
        df.to_csv(fileName, index=False)

        return jsonify({"message": "deleted"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "error"}), 500


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
