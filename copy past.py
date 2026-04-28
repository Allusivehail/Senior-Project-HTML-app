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
    #,ssl_context=('cert.pem', 'key.pem')



----------

<!DOCTYPE html>
<html>
<head>
    <title>Inventory</title>

    <!-- FONTS -->
    <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">

    <style>
        :root {
            --bg: #f0f2f5;
            --white: #ffffff;
            --surface: #fafbfc;
            --border: #e2e6ea;
            --border-strong: #cdd3da;
            --accent: #0069d9;
            --accent-light: #e8f0fb;
            --accent-mid: #b8d0f5;
            --text: #1a2332;
            --text-mid: #4a5568;
            --text-muted: #8a95a3;
            --mono: 'DM Mono', monospace;
            --serif: 'Instrument Serif', serif;
            --sans: 'DM Sans', sans-serif;
            --radius: 10px;
            --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: var(--sans);
            background: var(--bg);
            color: var(--text);
        }

        /* TOPBAR */
        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 36px;
            height: 64px;
            background: var(--white);
            border-bottom: 1px solid var(--border);
        }

        .topbar-wordmark {
            font-family: var(--serif);
            font-size: 22px;
        }

        .topbar-wordmark em { color: var(--accent); }

        .nav-btn {
            padding: 7px 18px;
            border: 1px solid var(--border-strong);
            border-radius: 7px;
            background: var(--surface);
            cursor: pointer;
            text-decoration: none;
        }

        .nav-btn:hover {
            background: var(--accent-light);
            color: var(--accent);
        }

        /* SECTION */
        .section-rule {
            padding: 20px 36px;
            font-family: var(--mono);
            font-size: 10px;
            color: var(--text-muted);
            text-transform: uppercase;
        }

        /* MAIN */
        .main {
            padding: 20px 36px;
        }

        /* CARD */
        .card {
            background: var(--white);
            border-radius: var(--radius);
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
        }

        .card-header {
            padding: 14px 20px;
            border-bottom: 1px solid var(--border);
            background: var(--surface);
            font-size: 12px;
            text-transform: uppercase;
            color: var(--text-muted);
        }

        .card-body {
            padding: 20px;
        }

        /* FORM */
        input {
            padding: 8px;
            margin-right: 8px;
            border: 1px solid var(--border);
            border-radius: 6px;
        }

        .btn {
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
        }

        .btn-primary {
            background: var(--accent);
            color: white;
        }

        .btn-danger {
            background: red;
            color: white;
        }

        /* TABLE */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }

        th, td {
            border: 1px solid var(--border);
            padding: 8px;
        }

        td[contenteditable="true"] {
            background: #f9f9f9;
        }

        .scroll-box {
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
</head>

<body>

<!-- TOPBAR -->
<header class="topbar">
        <span class="topbar-wordmark">Fridge<em>Sniffer</em></span>
    <div>
        <a href="/"><button class="nav-btn">Home</button></a>
    </div>
</header>

<div class="section-rule">Today's date is: </div>

<div class="main">

    <!-- INVENTORY CARD -->
    <div class="card">

        <div class="card-header">
            Inventory (Editable)
        </div>

        <div class="card-body">

            <h4>Add Item</h4>

            <input id="newItem" placeholder="Item">
            <input id="newDate" placeholder="Date In">
            <input id="newExp" placeholder="Expiration">

            <button class="btn btn-primary" onclick="addRow()">Add</button>

            <div class="scroll-box">
                <table>
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Date In</th>
                            <th>Expiration</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="yoloBody"></tbody>
                </table>
            </div>

        </div>
    </div>

</div>

<!-- ========================= -->
<!-- ORIGINAL JS (UNCHANGED) -->
<!-- ========================= -->
<script>

// LOAD TABLE
async function loadJSON() {
    const res = await fetch("/api/get-json");
    const json = await res.json();

    const data = json.data;
    const table = document.getElementById("yoloBody");
    table.innerHTML = "";

    data.forEach(row => {
        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td contenteditable="true" onblur="updateRow(${row.id}, this)">
                ${row.Item || ""}
            </td>

            <td contenteditable="true" onblur="updateRow(${row.id}, this)">
                ${row["Date In"] || ""}
            </td>

            <td contenteditable="true" onblur="updateRow(${row.id}, this)">
                ${row["Expected Expiration"] || ""}
            </td>

            <td>
                <button class="btn btn-danger" onclick="deleteRow(${row.id})">
                    Delete
                </button>
            </td>
        `;

        table.appendChild(tr);
    });
}

// UPDATE ROW
async function updateRow(id, cell) {
    const row = cell.parentElement;
    const c = row.children;

    await fetch("/api/update-row", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            id: id,
            Item: c[0].innerText.trim(),
            "Date In": c[1].innerText.trim(),
            "Expected Expiration": c[2].innerText.trim()
        })
    });
}

// ADD ROW
async function addRow() {
    await fetch("/api/add-row", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            "Item": document.getElementById("newItem").value,
            "Date In": document.getElementById("newDate").value,
            "Expected Expiration": document.getElementById("newExp").value
        })
    });

    document.getElementById("newItem").value = "";
    document.getElementById("newDate").value = "";
    document.getElementById("newExp").value = "";

    loadJSON();
}

// DELETE ROW
async function deleteRow(id) {
    const confirmDelete = confirm("Are you sure you want to delete this row?");
    if (!confirmDelete) return;

    await fetch("/api/delete-row", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ id: id })
    });

    loadJSON();
}

// INIT
window.onload = function () {
    loadJSON();
    setInterval(loadJSON, 1000);
};

</script>

<script src="https://cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.0.1/mqttws31.min.js" type="text/javascript"></script>

<script>
    if (Notification.permission !== "granted") {
        Notification.requestPermission();
    }

    const client = new Paho.MQTT.Client("10.100.138.163", 8083, "clientId");

    const connectOptions = {
        onSuccess: onConnect,
        useSSL: false,
        userName: "testUser",
        password: "pass"
    };

    client.onConnectionLost = onConnectionLost;
    client.onMessageArrived = onMessageArrived;

    client.connect(connectOptions);

    function onConnect() {
        console.log("Webpage connected to MQTT");
        client.subscribe("tempAlert");
	client.subscribe("sensorAlert");
    }

    function onConnectionLost(responseObject) {
        if (responseObject.errorCode !== 0) {
            console.log("onConnectionLost:" + responseObject.errorMessage);
        }
    }

    function onMessageArrived(message) {
        console.log("Message Arrived: " + message.payloadString);
        if (Notification.permission === "granted") {
            new Notification("New MQTT Message", {
                body: message.payloadString,
                icon: "https://cdn-icons-png.flaticon.com/512/1827/1827347.png"
            });
        } else {
            alert("MQTT Message: " + message.payloadString);
        }
    }
</script>

</body>
</html>

