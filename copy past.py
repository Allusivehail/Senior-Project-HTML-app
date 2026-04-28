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
