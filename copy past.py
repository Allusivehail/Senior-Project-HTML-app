function autoFillExpiration(dateStr) {
    if (!dateStr) return;
    const normalized = normalizeDate(dateStr);
    document.getElementById("newDate").value = normalized;

    const expField = document.getElementById("newExp");
    if (expField.value.trim() !== "") return;

    const parts = normalized.split("-");
    if (parts.length !== 3) return;
    const [mm, dd, yy] = parts;

    // ✅ Use local date construction, not a string parse (avoids UTC timezone shift)
    const d = new Date(2000 + parseInt(yy), parseInt(mm) - 1, parseInt(dd));
    if (isNaN(d)) return;

    d.setDate(d.getDate() + 5);
    const omm = String(d.getMonth() + 1).padStart(2, '0');
    const odd = String(d.getDate()).padStart(2, '0');
    const oyy = String(d.getFullYear()).slice(-2);
    expField.value = `${omm}-${odd}-${oyy}`;
}
