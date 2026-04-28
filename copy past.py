<input id="newDate" placeholder="Date In" oninput="autoFillExpiration(this.value)">

<input id="newExp" placeholder="Expiration" oninput="this.value = normalizeDate(this.value)">

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

    // Parse MM-DD-YY explicitly
    const parts = normalized.split("-");
    if (parts.length !== 3) return;
    const [mm, dd, yy] = parts;
    const d = new Date(`20${yy}-${mm}-${dd}`);
    if (isNaN(d)) return;

    d.setDate(d.getDate() + 5);
    const omm = String(d.getMonth() + 1).padStart(2, '0');
    const odd = String(d.getDate()).padStart(2, '0');
    const oyy = String(d.getFullYear()).slice(-2);
    expField.value = `${omm}-${odd}-${oyy}`;
}
