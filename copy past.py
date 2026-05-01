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
                    <div class="gas-value" id="temp">--</div>
                </div>

                <div class="gas-box">
                    <div class="gas-title">Ammonia</div>
                    <div class="gas-value" id="ethanol">--</div>
                </div>

                <div class="gas-box">
                    <div class="gas-title">Hydrogen Sulfide</div>
                    <div class="gas-value" id="ammonia">--</div>
                </div>

                <div class="gas-box">
                    <div class="gas-title">Temperature</div>
                    <div class="gas-value" id="h2s">--</div>
                </div>

            </div>
        </div>
    </div>

    <script>
        // The element IDs in this file are mismatched to their labels (legacy naming).
        // Mapping: label "Ethanol" -> id="temp", label "Ammonia" -> id="ethanol",
        //          label "H2S" -> id="ammonia", label "Temperature" -> id="h2s"
        // We preserve those IDs and wire thresholds to match each label (not each ID).

        const COLOR_OK     = '#1a8a3a';  // green
        const COLOR_WARN   = '#b45309';  // amber
        const COLOR_DANGER = '#c0392b';  // red

        function colorFor(value, okMax, warnMax) {
            if (typeof value !== 'number') return '';
            if (value <= okMax)   return COLOR_OK;
            if (value <= warnMax) return COLOR_WARN;
            return COLOR_DANGER;
        }

        function isDanger(value, warnMax) {
            return typeof value === 'number' && value > warnMax;
        }

        async function loadGasData() {
            try {
                const res  = await fetch('/api/gas-data');
                const data = await res.json();

                const ethanol = data.Ethanol;           // shown in id="temp"
                const ammonia = data.Ammonia;           // shown in id="ethanol"
                const h2s     = data["Hydrogen Sulfide"]; // shown in id="ammonia"
                const temp    = data.Temperature;       // shown in id="h2s"

                // Ethanol: green <=5, yellow 6-9, red >=10
                const elEthanol = document.getElementById('temp');
                elEthanol.textContent = ethanol ?? '--';
                elEthanol.style.color = colorFor(ethanol, 5, 9);

                // Ammonia: green <=12, yellow 13-19, red >=20
                const elAmmonia = document.getElementById('ethanol');
                elAmmonia.textContent = ammonia ?? '--';
                elAmmonia.style.color = colorFor(ammonia, 12, 19);

                // Hydrogen Sulfide: green <=2, yellow 3-4, red >=5
                const elH2S = document.getElementById('ammonia');
                elH2S.textContent = h2s ?? '--';
                elH2S.style.color = colorFor(h2s, 2, 4);

                // Temperature: green <=40, yellow 41-54, red >=55
                const elTemp = document.getElementById('h2s');
                elTemp.textContent = temp ?? '--';
                elTemp.style.color = colorFor(temp, 40, 54);

                const anyDanger = isDanger(ethanol, 9)
                               || isDanger(ammonia, 19)
                               || isDanger(h2s, 4)
                               || isDanger(temp, 54);

                document.body.classList.toggle('alert-active', anyDanger);
                document.getElementById('alertBanner').classList.toggle('visible', anyDanger);

            } catch (err) {
                console.error("Gas data fetch failed:", err);
            }
        }

        loadGasData();
        setInterval(loadGasData, 2000);
    </script>

</body>
</html>
