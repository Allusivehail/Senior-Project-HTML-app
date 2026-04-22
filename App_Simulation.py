from flask import Flask, request, jsonify, render_template
import time
import os
import csv

app = Flask(__name__)

# ----------------------------
# FAKE STATE (for testing UI)
# ----------------------------
motor_state = "stopped"
last_action = None


# ----------------------------
# UI ROUTE
# ----------------------------
@app.route("/")
def ui():
    return render_template("index.html")


# ----------------------------
# BASIC TEST
# ----------------------------
@app.route("/api/test")
def test():
    return jsonify({
        "message": "DEBUG SERVER OK",
        "status": "running",
        "time": time.time()
    })


# ----------------------------
# MOTOR SIMULATION
# ----------------------------
@app.route("/motorfridge")
def motor_fridge():
    global motor_state, last_action
    motor_state = "fridge"
    last_action = "motorfridge"
    return "DEBUG: Fridge motor ON"


@app.route("/motorroom")
def motor_room():
    global motor_state, last_action
    motor_state = "room"
    last_action = "motorroom"
    return "DEBUG: Room motor ON"


@app.route("/motorstop")
def motor_stop():
    global motor_state, last_action
    motor_state = "stopped"
    last_action = "motorstop"
    return "DEBUG: Motors STOPPED"


# ----------------------------
# DEBUG SEQUENCE
# ----------------------------
@app.route("/api/run-debug", methods=["POST"])
def run_debug():
    data = request.get_json()

    if not data or data.get("action") != "run_program":
        return jsonify({"message": "Invalid request"}), 400

    steps = [
        "Starting sequence...",
        "Motor room ON",
        "Motor fridge ON",
        "Running...",
        "Running...",
        "Stopping motors",
        "DONE"
    ]

    for s in steps:
        print(s)
        time.sleep(0.3)

    return jsonify({
        "message": "DEBUG sequence completed",
        "steps": steps
    })


# ----------------------------
# IMAGE SIMULATION
# ----------------------------
@app.route("/api/capture-image")
def capture_image():
    img_path = os.path.join("static", "IMG", "http_test_image.png")

    if not os.path.exists(img_path):
        return jsonify({
            "message": "No image found (DEBUG mode)",
            "image_url": None
        })

    return jsonify({
        "message": "DEBUG image ready",
        "image_url": "/static/IMG/http_test_image.png"
    })


# ----------------------------
# SAFE CSV READER
# ----------------------------
def read_csv():
    csv_path = os.path.join("data", "FakedData.csv")
    data = []

    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader):

                # SKIP EMPTY ROWS (FIXES GHOST ROW BUG)
                if not row.get("Item") and not row.get("Date In") and not row.get("Expected Expiration"):
                    continue

                data.append({
                    "id": i,
                    "Item": row.get("Item") or "",
                    "Date In": row.get("Date In") or "",
                    "Expected Expiration": row.get("Expected Expiration") or ""
                })

    except FileNotFoundError:
        return []

    return data


# ----------------------------
# GET TABLE DATA
# ----------------------------
@app.route("/api/get-json")
def get_json():
    return jsonify({
        "message": "ok",
        "data": read_csv()
    })


# ----------------------------
# UPDATE ROW
# ----------------------------
@app.route("/api/update-row", methods=["POST"])
def update_row():
    data = request.get_json()

    row_id = int(data["id"])
    csv_path = os.path.join("data", "FakedData.csv")

    rows = read_csv()

    if 0 <= row_id < len(rows):
        rows[row_id]["Item"] = data["Item"]
        rows[row_id]["Date In"] = data["Date In"]
        rows[row_id]["Expected Expiration"] = data["Expected Expiration"]

    # REWRITE CSV CLEANLY
    with open(csv_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Item", "Date In", "Expected Expiration"])
        writer.writeheader()

        for r in rows:
            writer.writerow({
                "Item": r["Item"],
                "Date In": r["Date In"],
                "Expected Expiration": r["Expected Expiration"]
            })

    return jsonify({"status": "updated"})


# ----------------------------
# ADD ROW
# ----------------------------
@app.route("/api/add-row", methods=["POST"])
def add_row():
    data = request.get_json()

    csv_path = os.path.join("data", "FakedData.csv")
    file_exists = os.path.exists(csv_path)

    with open(csv_path, "a", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Item", "Date In", "Expected Expiration"])

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "Item": data.get("Item", ""),
            "Date In": data.get("Date In", ""),
            "Expected Expiration": data.get("Expected Expiration", "")
        })

    return jsonify({"status": "added"})


# ----------------------------
# DELETE ROW (NEW)
# ----------------------------
@app.route("/api/delete-row", methods=["POST"])
def delete_row():
    data = request.get_json()
    row_id = int(data["id"])

    csv_path = os.path.join("data", "FakedData.csv")

    rows = read_csv()

    # REMOVE TARGET ROW
    rows = [r for r in rows if r["id"] != row_id]

    # REWRITE CLEAN CSV
    with open(csv_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Item", "Date In", "Expected Expiration"])
        writer.writeheader()

        for r in rows:
            writer.writerow({
                "Item": r["Item"],
                "Date In": r["Date In"],
                "Expected Expiration": r["Expected Expiration"]
            })

    return jsonify({"status": "deleted"})


# ----------------------------
# STATUS
# ----------------------------
@app.route("/api/status")
def status():
    return jsonify({
        "motor_state": motor_state,
        "last_action": last_action
    })



# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == "__main__":
    print("DEBUG FLASK SERVER STARTING...")
    app.run(host="0.0.0.0", port=5000, debug=True)
