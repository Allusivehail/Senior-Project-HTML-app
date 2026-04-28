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
	    <input id="newDate" placeholder="Date In" onblur="autoFillExpiration(this.value)">
	    <input id="newExp" placeholder="Expiration" oninput="this.value = normalizeDate(this.value)">

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




function normalizeDate(dateStr) {
    if (!dateStr) return "";
    // Convert slashes to dashes
    return dateStr.replace(/\//g, "-");
}

function autoFillExpiration(dateStr) {
    if (!dateStr) return;
    const normalized = normalizeDate(dateStr);
    document.getElementById("newDate").value = normalized;

    const expField = document.getElementById("newExp");
    if (expField.value.trim() !== "") return;

    const parts = normalized.split("-");
    if (parts.length !== 3) return;
    const [mm, dd, yy] = parts;

    console.log("DEBUG parts:", mm, dd, yy); // ✅ check this in browser console

    const fullYear = parseInt(yy) < 100 ? 2000 + parseInt(yy) : parseInt(yy);
    const d = new Date(fullYear, parseInt(mm) - 1, parseInt(dd));

    if (isNaN(d.getTime())) return;

    d.setDate(d.getDate() + 5);

    const omm = String(d.getMonth() + 1).padStart(2, '0');
    const odd = String(d.getDate()).padStart(2, '0');
    const oyy = String(d.getFullYear()).slice(-2);

    console.log("DEBUG result:", omm, odd, oyy); // ✅ check this too

    expField.value = `${omm}-${odd}-${oyy}`;
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
