from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session
from datetime import datetime, timedelta
import time, traceback
import cv2
import board
import neopixel_spi as neopixel
import os
import pandas as pd
from paho.mqtt import client as mqtt_client


app = Flask(__name__)
app.secret_key = "demo_secret_key"

CSV_PATH = "/home/mert/app_gui/inventory_data/yolo_temp.csv"
GAS_PATH = "/home/mert/fridge_project/PPMData.csv"
IMAGE_PATH = "/home/mert/app_gui/captured_image.png"


# ---------------- LOGIN ---------------- #

@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    users = {
        "admin": "admin123",
        "john": "doe123"
    }

    if username in users and users[username] == password:
        session["user"] = username
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False}), 401


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# ---------------- UI ROUTES ---------------- #

@app.route("/")
def root():
    if "user" not in session:
        return redirect(url_for("login_page"))

    return render_template("newDash.html", username=session["user"])


@app.route("/inventory")
def inventory():
    if "user" not in session:
        return redirect(url_for("login_page"))

    return render_template("inventory.html", username=session["user"])


@app.route("/screen")
def screen():
    if "user" not in session:
        return redirect(url_for("login_page"))

    return render_template("piScreen.html", username=session["user"])


# ---------------- LED ---------------- #

NUM_PIXELS = 16
PIXEL_ORDER = neopixel.RGBW
WHITE = 0xFFFFFF
OFF = 0x000000

spi = board.SPI()
pixels = neopixel.NeoPixel_SPI(spi, NUM_PIXELS, pixel_order=PIXEL_ORDER, auto_write=False)


# ---------------- CAMERA ---------------- #

def cameraTrigger():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise IOError("Cannot open webcam")

    pixels.fill(WHITE)
    pixels.show()

    ret, frame = cap.read()

    if ret:
        cv2.imwrite(IMAGE_PATH, frame)

    pixels.fill(OFF)
    pixels.show()
    cap.release()


@app.route('/api/latest-image')
def latest_image():
    if not os.path.exists(IMAGE_PATH):
        return jsonify({"error": "No image captured yet"}), 404

    return send_file(IMAGE_PATH, mimetype='image/png', conditional=True)


# ---------------- GAS ---------------- #

@app.route('/api/gas-data')
def gas_data():
    try:
        if not os.path.exists(GAS_PATH):
            return jsonify({"error": "No data yet"}), 404

        df = pd.read_csv(GAS_PATH, header=None)
        last = df.iloc[-1]

        return jsonify({
            "Temperature": str(last[0]) if len(last) > 0 else "--",
            "Ethanol": str(last[1]) if len(last) > 1 else "--",
            "Ammonia": str(last[2]) if len(last) > 2 else "--",
            "Hydrogen Sulfide": str(last[3]) if len(last) > 3 else "--"
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
