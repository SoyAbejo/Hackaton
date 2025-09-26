// static/js/dashboard.js
async function fetchJSON(path) { const r = await fetch(path); return await r.json(); }

async function init() {
    const services = await fetchJSON('/api/services');
    const jornadas = await fetchJSON('/api/jornadas');
    const pred = await fetchJSON('/api/prediction').catch(() => null);

    // Mapa
    const map = L.map('map').setView([5.5, -73.3], 9);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18 }).addTo(map);

    services.forEach(s => {
        const icon = L.circleMarker([s.lat, s.lon], { radius: 8, color: s.type === 'hospital' ? '#327039' : s.type === 'puesto' ? '#F0BE49' : '#DD5C36' }).addTo(map);
        icon.bindPopup(`<strong>${s.name}</strong><br>Tipo: ${s.type}<br>Estado: ${s.status}<br>Capacidad: ${s.capacity}`);
    });

    // Jornadas list
    const jl = document.getElementById('jornadas-list');
    jornadas.slice(0, 6).forEach(j => {
        const li = document.createElement('li');
        li.innerText = `${j.date} — ${j.title} (Att esp: ${j.expected_attendees})`;
        jl.appendChild(li);
    });

    // Estimate (next month projection)
    if (pred && pred.projections && pred.projections.length) {
        document.getElementById('estimate').innerText = pred.projections[0].projected + " atenciones (proyectado)";
    } else {
        document.getElementById('estimate').innerText = "Sin datos";
    }

    // Charts
    if (pred && pred.history) {
        const ctx = document.getElementById('historyChart').getContext('2d');
        const labels = pred.history.map(h => h.month);
        const data = pred.history.map(h => h.count);
        new Chart(ctx, {
            type: 'line',
            data: { labels, datasets: [{ label: 'Atenciones', data, fill: true, tension: 0.3 }] },
            options: { plugins: { legend: { display: false } } }
        });
    }

    if (pred && pred.projections) {
        const ctx2 = document.getElementById('projChart').getContext('2d');
        const labels = pred.projections.map(p => p.month);
        const data = pred.projections.map(p => p.projected);
        new Chart(ctx2, { type: 'bar', data: { labels, datasets: [{ label: 'Proyección', data }] }, options: { plugins: { legend: { display: false } } } });
    }
}

// ejecutar
init();
