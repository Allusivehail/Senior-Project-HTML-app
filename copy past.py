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
    if (expField.value.trim() !== "") return; // don't overwrite if already filled

    const d = new Date(normalized);
    if (isNaN(d)) return;
    d.setDate(d.getDate() + 5);
    expField.value = d.toISOString().split('T')[0];
}
