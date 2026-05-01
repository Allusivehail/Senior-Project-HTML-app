<!DOCTYPE html>
<html>
<head>
    <title>Fridge Diagnostics</title>

    <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">

    <style>
        :root {
            --bg: #f0f2f5;
            --white: #ffffff;
            --surface: #fafbfc;
            --border: #e2e6ea;
            --accent: #0069d9;
            --text: #1a2332;
            --text-mid: #4a5568;
            --text-muted: #8a95a3;
            --serif: 'Instrument Serif', serif;
            --sans: 'DM Sans', sans-serif;
            --mono: 'DM Mono', monospace;
            --radius: 16px;
            --shadow: 0 2px 10px rgba(0,0,0,0.08);

            --green: #28a745;
            --yellow: #ffc107;
            --red: #dc3545;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        html, body { height: 100%; }

        body {
            font-family: var(--sans);
            background: var(--bg);
            color: var(--text);
            display: flex;
            flex-direction: column;
        }

        .topbar {
            background: white;
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
            flex-shrink: 0;
        }

        .topbar-wordmark {
            font-family: var(--serif);
            font-size: 20px;
        }

        .topbar-wordmark em {
            color: var(--accent);
        }

        .main {
            flex: 1;
            padding: 12px;
            display: flex;
        }

        .card-body {
            flex: 1;
            padding: 12px;
            display: flex;
        }

        .gas-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-auto-rows: 1fr;
            gap: 12px;
            width: 100%;
            height: 100%;
        }

        .gas-box {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }

        .gas-title {
            font-size: 11px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 8px;
        }

        .gas-value {
            font-size: 28px;
            font-weight: 600;
        }
    </style>
</head>

<body>

<div class="topbar">
    <div class="topbar-wordmark">Fridge <em>Sniffer</em></div>
</div>

<div class="main">
    <div class="card-body">
        <div class="gas-grid">

            <div class="gas-box">
                <div class="gas-title">Ethanol</div>
                <div class="gas-value" id="ethanol">--</div>
            </div>

            <div class="gas-box">
                <div class="gas-title">Ammonia</div>
                <div class="gas-value" id="ammonia">--</div>
            </div>

            <div class="gas-box">
                <div class="gas-title">Hydrogen Sulfide</div>
                <div class="gas-value" id="h2s">--</div>
            </div>

            <div class="gas-box">
                <div class="gas-title">Temperature</div>
                <div class="gas-value" id="temp">--</div>
            </div>

        </div>
    </div>
</div>

<!-- MQTT -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.0.1/mqttws31.min.js"></script>

<script>
    const client = new Paho.MQTT.Client("10.100.138.163", 8083, "fridge-ui-" + Math.random());

    const options = {
        onSuccess: onConnect,
        useSSL: false,
        userName: "testUser",
        password: "pass"
    };

    client.onConnectionLost = onLost;
    client.onMessageArrived = onMessage;

    client.connect(options);

    function onConnect() {
        console.log("MQTT connected");

        client.subscribe("sensorAlert");
        client.subscribe("tempAlert");
        client.subscribe("gasData");
    }

    function onLost(res) {
        console.log("MQTT lost:", res.errorMessage);
    }

    function onMessage(msg) {
        console.log("MQTT:", msg.destinationName, msg.payloadString);

        let data;

        // Try JSON first
        try {
            data = JSON.parse(msg.payloadString);
        } catch (e) {
            return;
        }

        // EXPECTED FORMAT:
        // { Ethanol: 1.2, Ammonia: 3.4, HydrogenSulfide: 5.6, Temperature: 22 }

        if (data.Ethanol !== undefined)
            document.getElementById("ethanol").textContent = parseFloat(data.Ethanol).toFixed(2);

        if (data.Ammonia !== undefined)
            document.getElementById("ammonia").textContent = parseFloat(data.Ammonia).toFixed(2);

        if (data.HydrogenSulfide !== undefined)
            document.getElementById("h2s").textContent = parseFloat(data.HydrogenSulfide).toFixed(2);

        if (data.Temperature !== undefined)
            document.getElementById("temp").textContent = parseFloat(data.Temperature).toFixed(2);
    }
</script>

<!-- fallback REST polling (kept as backup) -->
<script>
async function loadGasData() {
    try {
        const res = await fetch('/api/gas-data');
        const data = await res.json();

        document.getElementById("ethanol").textContent = data.Ethanol ?? "--";
        document.getElementById("ammonia").textContent = data.Ammonia ?? "--";
        document.getElementById("h2s").textContent = data["Hydrogen Sulfide"] ?? "--";
        document.getElementById("temp").textContent = data.Temperature ?? "--";

    } catch (err) {
        console.error("REST fallback failed:", err);
    }
}

loadGasData();
setInterval(loadGasData, 2000);
</script>

</body>
</html>
