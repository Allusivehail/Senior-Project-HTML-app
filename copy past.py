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

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        html, body {
            height: 100%;
        }

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

<script>
    function normalizeData(data) {
        return {
            ethanol: data.ethanol ?? data.Ethanol,
            ammonia: data.ammonia ?? data.Ammonia,
            h2s: data["hydrogen sulfide"] ?? data["Hydrogen Sulfide"],
            temp: data.temperature ?? data.Temperature
        };
    }

    const thresholds = {
        ethanol: { green: 5.0, yellow: 5.1, red: 10.0 },
        ammonia: { green: 12.0, yellow: 12.1, red: 20.0 },
        h2s:     { green: 3.0, yellow: 4.0, red: 5.0 },
        temp:    { green: 40.0, yellow: 41.1, red: 55.0 }
    };

    function applyValue(id, value, t) {
        const el = document.getElementById(id);

        if (value === null || value === undefined || isNaN(value)) {
            el.textContent = '--';
            el.style.color = '';
            return;
        }

        const v = Number(value);
        el.textContent = v.toFixed(2);

        if (v >= t.red) {
            el.style.color = "var(--red)";
        } else if (v >= t.yellow) {
            el.style.color = "var(--yellow)";
        } else {
            el.style.color = "var(--green)";
        }
    }

    async function loadGasData() {
        try {
            const res = await fetch('/api/gas-data');
            const raw = await res.json();

            const data = normalizeData(raw);

            applyValue('ethanol', data.ethanol, thresholds.ethanol);
            applyValue('ammonia', data.ammonia, thresholds.ammonia);
            applyValue('h2s', data.h2s, thresholds.h2s);
            applyValue('temp', data.temp, thresholds.temp);

        } catch (err) {
            console.error("Gas data fetch failed:", err);
        }
    }

    loadGasData();
    setInterval(loadGasData, 2000);
</script>

</body>
</html>
