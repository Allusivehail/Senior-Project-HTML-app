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
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { height: 100%; }

        body {
            font-family: var(--sans);
            background: var(--bg);
            color: var(--text);
            display: flex;
            flex-direction: column;
            transition: background 0.3s;
        }

        body.alert-active {
            animation: bgFlash 1s ease-in-out infinite;
        }

        @keyframes bgFlash {
            0%   { background: var(--bg); }
            50%  { background: #ffcccc; }
            100% { background: var(--bg); }
        }

        .topbar {
            background: white;
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
            flex-shrink: 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .topbar-wordmark { font-family: var(--serif); font-size: 20px; }
        .topbar-wordmark em { color: var(--accent); }

        .alert-banner {
            display: none;
            margin-left: auto;
            background: #c0392b;
            color: white;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 5px 12px;
            border-radius: 20px;
            animation: bannerPulse 1s ease-in-out infinite;
        }

        .alert-banner.visible { display: inline-block; }

        @keyframes bannerPulse {
            0%, 100% { opacity: 1; }
            50%       { opacity: 0.5; }
        }

        .main { flex: 1; padding: 12px; display: flex; }

        .card-body { flex: 1; padding: 12px; display: flex; }

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
            color: var(--text);
            transition: color 0.3s;
        }
    </style>
</head>

<body>

    <div class="topbar">
        <div class="topbar-wordmark">Fridge <em>Sniffer</em></div>
        <div class="alert-banner" id="alertBanner">⚠ Alert — Threshold Exceeded</div>
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
        const THRESHOLDS = {
            ethanol: { ok: 5,  warn: 9  },
            ammonia: { ok: 12, warn: 19 },
            h2s:     { ok: 2,  warn: 4  },
            temp:    { ok: 40, warn: 54 },
        };

        const COLOR = {
            ok:     '#1a8a3a',
            warn:   '#b45309',
            danger: '#c0392b',
        };

        function getStatus(value, t) {
            if (typeof value !== 'number') return null;
            if (value <= t.ok)   return 'ok';
            if (value <= t.warn) return 'warn';
            return 'danger';
        }

        function updateSensor(elementId, value, thresholds) {
            const el = document.getElementById(elementId);
            el.textContent = value ?? '--';
            const status = getStatus(value, thresholds);
            el.style.color = status ? COLOR[status] : '';
            return status === 'danger';
        }

        async function loadGasData() {
            try {
                const res  = await fetch('/api/gas-data');
                const data = await res.json();

                let anyDanger = false;
                anyDanger |= updateSensor('ethanol', data.Ethanol,             THRESHOLDS.ethanol);
                anyDanger |= updateSensor('ammonia', data.Ammonia,             THRESHOLDS.ammonia);
                anyDanger |= updateSensor('h2s',     data["Hydrogen Sulfide"], THRESHOLDS.h2s);
                anyDanger |= updateSensor('temp',    data.Temperature,         THRESHOLDS.temp);

                document.body.classList.toggle('alert-active', !!anyDanger);
                document.getElementById('alertBanner').classList.toggle('visible', !!anyDanger);

            } catch (err) {
                console.error("Gas data fetch failed:", err);
            }
        }

        loadGasData();
        setInterval(loadGasData, 2000);
    </script>

</body>
</html>
