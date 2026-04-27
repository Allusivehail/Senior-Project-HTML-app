<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <style>
        body {
            font-family: Arial;
            margin: 20px;
            background: #f4f4f4;
        }

        .container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }

        button {
            padding: 10px;
            margin: 5px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }

        .motor { background: #4CAF50; color: white; }
        .stop { background: #f44336; color: white; }
        .blue { background: #2196F3; color: white; }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 6px;
            border: 1px solid #ccc;
        }

        td[contenteditable="true"] {
            background: #f9f9f9;
        }

        .delete-btn {
            background: red;
            color: white;
            border: none;
            padding: 6px;
            border-radius: 5px;
            cursor: pointer;
        }
    </style>
</head>
<body>

<h1>Dashboard</h1>

<!-- MENU -->
<a href="/testing"> <button class="motor">Testing</button></a> |
<a href="/inventory"> <button class="motor">Inventory</button></a>

<hr>

    <!-- CAMERA -->
    <div class="card">
        <h2>Camera</h2>

        <button class="blue" onclick="captureImage()">Take Picture</button>
        <button onclick="loadImage()">Refresh Image</button>

        <p id="cameraStatus"></p>

        <img id="cam" style="max-width:100%; border-radius:8px;">

<script>
// ----------------------------
// CAMERA: LOAD IMAGE
// ----------------------------
function loadImage() {
    document.getElementById("cam").src =
        "/static/IMG/http_test_image.png?rand=" + Math.random();
}

// ----------------------------
// CAMERA: TAKE PICTURE (NEW FIX)
// ----------------------------
async function captureImage() {
    const res = await fetch("/api/capture-image");
    const data = await res.json();

    document.getElementById("cameraStatus").innerText = data.message;

    // Always refresh image view (even if backend is fake/debug)
    document.getElementById("cam").src =
        "/static/IMG/http_test_image.png?rand=" + Math.random();
}

</script>

<script src="https://cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.0.1/mqttws31.min.js" type="text/javascript"></script>

<script>
    // 1. Request Permission for Notifications
    if (Notification.permission !== "granted") {
        Notification.requestPermission();
    }

    // 2. MQTT Connection Settings
    // Note: Use a WebSockets port (usually 8083 or 8084 for SSL) instead of 1883
    const client = new Paho.MQTT.Client("10.100.138.163:8083", 8083, "clientId");

const connectOptions = {
    onSuccess: onConnect,
    useSSL: false, // Set to true if using port 8084/wss
    // ✅ ADD THESE LINES
    userName: "testUser",
    password: "pass"
};

    client.onConnectionLost = onConnectionLost;
    client.onMessageArrived = onMessageArrived;

    client.connect(connectOptions);

    function onConnect() {
        console.log("Webpage connected to MQTT");
        client.subscribe("tempAlert"); // Use the same topic as backend
    }

    function onConnectionLost(responseObject) {
        if (responseObject.errorCode !== 0) {
            console.log("onConnectionLost:"+responseObject.errorMessage);
        }
    }

    function onMessageArrived(message) {
        console.log("Message Arrived: " + message.payloadString);
        
        // 3. Trigger Browser Notification
        if (Notification.permission === "granted") {
            new Notification("New MQTT Message", {
                body: message.payloadString,
                icon: "https://cdn-icons-png.flaticon.com/512/1827/1827347.png" // Optional icon
            });
        } else {
            // Fallback if notifications are blocked
            alert("MQTT Message: " + message.payloadString);
        }
    }
</script>

    </div>
    <br> <br>
    <div class="card">
        <!-- SENSOR Data -->
        <h2>Fridge Diagnostics</h2>
        <p>Temperature: --</p>
        <p>Humidity: --</p>
        <p>Ethanol: --</p>
        <p>Ammonia: --</p>
        <p>Hydrogen Sulfide: --</p>
    </div>

</body>
</html>
