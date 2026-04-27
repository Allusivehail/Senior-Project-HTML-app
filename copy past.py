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
                "message": "Debug test complete: fridge → room → stop"
            }), 200

        except Exception as e:
            traceback.print_exc()
            return jsonify({"message": str(e)}), 500

    return jsonify({"message": "Unknown action"}), 400
