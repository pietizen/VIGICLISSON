"""Generate static HTML dashboard from Vigicrues data."""

import json
import logging
import os
from datetime import datetime, timezone

import config

logger = logging.getLogger(__name__)

TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Niveau La Moine — Clisson</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f1923;
            color: #e0e6ed;
            padding: 16px;
            max-width: 900px;
            margin: 0 auto;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 12px;
        }
        .station-name {
            font-size: 14px;
            color: #8899aa;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .current-level {
            font-size: 48px;
            font-weight: 700;
            line-height: 1;
            margin: 4px 0;
        }
        .trend { font-size: 28px; margin-left: 8px; }
        .trend-up { color: #ff6b35; }
        .trend-down { color: #4ecdc4; }
        .trend-stable { color: #8899aa; }
        .meta {
            font-size: 12px;
            color: #5a6a7a;
            line-height: 1.6;
            text-align: right;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            margin-top: 6px;
        }
        .status-normal { background: rgba(78, 205, 196, 0.15); color: #4ecdc4; }
        .status-vigilance { background: rgba(255, 214, 0, 0.15); color: #ffd600; }
        .status-alert { background: rgba(255, 107, 53, 0.15); color: #ff6b35; }
        .chart-container {
            position: relative;
            width: 100%;
            height: 350px;
            margin-bottom: 16px;
        }
        .legend {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            font-size: 12px;
            color: #8899aa;
            justify-content: center;
        }
        .legend-item { display: flex; align-items: center; gap: 6px; }
        .legend-dot { width: 12px; height: 3px; border-radius: 2px; }
        .legend-area { width: 12px; height: 12px; border-radius: 2px; opacity: 0.4; }
        .footer {
            margin-top: 20px;
            text-align: center;
            font-size: 11px;
            color: #3a4a5a;
        }
        .footer a { color: #5a7a9a; text-decoration: none; }
    </style>
</head>
<body>

<div class="header">
    <div>
        <div class="station-name">La Moine à Clisson</div>
        <div class="current-level" id="currentLevel">—</div>
        <div class="status-badge status-normal" id="statusBadge">Normal</div>
    </div>
    <div class="meta">
        <div>Dernière mesure : <span id="lastObs">—</span></div>
        <div>Prévision du : <span id="lastSimul">—</span></div>
        <div>Page générée : <span id="updateTime">__GENERATED_AT__</span></div>
    </div>
</div>

<div class="chart-container">
    <canvas id="chart"></canvas>
</div>

<div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#4ecdc4"></div> Observations</div>
    <div class="legend-item"><div class="legend-dot" style="background:#4ecdc4;opacity:0.5"></div> Prévision moy.</div>
    <div class="legend-item"><div class="legend-area" style="background:#4ecdc4"></div> Fourchette 80%</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ff6b35"></div> Seuil surveillance (2.00m)</div>
</div>

<div class="footer">
    Données <a href="https://www.vigicrues.gouv.fr" target="_blank">Vigicrues</a> — Station M730242010
</div>

<script>
const obsData = __OBS_JSON__;
const prevData = __PREV_JSON__;
const SEUIL = __SEUIL__;

// Parse
const obs = obsData.map(o => ({ x: new Date(o.dt), y: o.level }));
const prevMoy = prevData.prevs.map(p => ({ x: new Date(p.dt), y: p.moy }));
const prevMin = prevData.prevs.map(p => ({ x: new Date(p.dt), y: p.min }));
const prevMax = prevData.prevs.map(p => ({ x: new Date(p.dt), y: p.max }));

// Header
const last = obs[obs.length - 1];
const prev6 = obs[Math.max(0, obs.length - 7)];
const trend = last.y > prev6.y + 0.02 ? '↗' : last.y < prev6.y - 0.02 ? '↘' : '→';
const tc = trend === '↗' ? 'trend-up' : trend === '↘' ? 'trend-down' : 'trend-stable';

const fmt = (d) => new Date(d).toLocaleString('fr-FR', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit', timeZone:'Europe/Paris' });

document.getElementById('currentLevel').innerHTML = last.y.toFixed(2) + 'm <span class="trend ' + tc + '">' + trend + '</span>';
document.getElementById('lastObs').textContent = fmt(last.x);
document.getElementById('lastSimul').textContent = fmt(prevData.dt_prod);

const badge = document.getElementById('statusBadge');
const maxPrev = Math.max(...prevData.prevs.map(p => p.max));
if (last.y >= SEUIL || maxPrev >= SEUIL) {
    badge.className = 'status-badge status-alert'; badge.textContent = 'Surveillance';
} else if (last.y >= 1.80 || maxPrev >= 1.80) {
    badge.className = 'status-badge status-vigilance'; badge.textContent = 'Vigilance';
} else {
    badge.className = 'status-badge status-normal'; badge.textContent = 'Normal';
}

// Chart
const allDates = [...obs.map(d => d.x), ...prevMoy.map(d => d.x)];
new Chart(document.getElementById('chart'), {
    type: 'line',
    data: {
        datasets: [
            { label:'Observations', data:obs, borderColor:'#4ecdc4', borderWidth:2.5, pointRadius:0, pointHitRadius:10, tension:0.3, order:1 },
            { label:'Prévision moy.', data:prevMoy, borderColor:'rgba(78,205,196,0.6)', borderWidth:2, borderDash:[8,4], pointRadius:0, tension:0.3, order:2 },
            { label:'Prev max', data:prevMax, borderColor:'transparent', backgroundColor:'rgba(78,205,196,0.12)', pointRadius:0, fill:'+1', tension:0.3, order:3 },
            { label:'Prev min', data:prevMin, borderColor:'transparent', backgroundColor:'rgba(78,205,196,0.12)', pointRadius:0, fill:false, tension:0.3, order:4 }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode:'index', intersect:false },
        plugins: {
            legend: { display:false },
            tooltip: {
                backgroundColor:'rgba(15,25,35,0.95)', titleColor:'#8899aa', bodyColor:'#e0e6ed',
                borderColor:'#2a3a4a', borderWidth:1, padding:12, displayColors:false,
                callbacks: {
                    title: (items) => fmt(items[0].parsed.x),
                    label: (item) => {
                        if (item.dataset.label.startsWith('Prev ')) return null;
                        return item.dataset.label + ' : ' + item.parsed.y.toFixed(2) + 'm';
                    }
                }
            }
        },
        scales: {
            x: {
                type:'time', time:{ unit:'hour', stepSize:6, displayFormats:{ hour:'dd/MM HH:mm' } },
                grid:{ color:'rgba(255,255,255,0.04)' },
                ticks:{ color:'#5a6a7a', maxRotation:45, font:{ size:11 } },
                min: new Date(Math.min(...allDates)), max: new Date(Math.max(...allDates))
            },
            y: {
                grid:{ color:'rgba(255,255,255,0.06)' },
                ticks:{ color:'#5a6a7a', callback: v => v.toFixed(1)+'m', font:{ size:11 } },
                suggestedMin: 0,
                suggestedMax: Math.max(SEUIL + 0.3, maxPrev + 0.2)
            }
        }
    },
    plugins: [{
        id: 'seuil',
        afterDraw(chart) {
            const { ctx, chartArea, scales } = chart;
            const y = scales.y.getPixelForValue(SEUIL);
            if (y >= chartArea.top && y <= chartArea.bottom) {
                ctx.save();
                ctx.strokeStyle = 'rgba(255,107,53,0.5)';
                ctx.lineWidth = 1.5;
                ctx.setLineDash([6,4]);
                ctx.beginPath();
                ctx.moveTo(chartArea.left, y);
                ctx.lineTo(chartArea.right, y);
                ctx.stroke();
                ctx.fillStyle = 'rgba(255,107,53,0.7)';
                ctx.font = '11px -apple-system, sans-serif';
                ctx.fillText('2.00m — Surveillance', chartArea.right - 160, y - 6);
                ctx.restore();
            }
        }
    }]
});
</script>
</body>
</html>"""


def generate_html(observations: list[dict], previsions: dict) -> str:
    """Generate the HTML page with injected data."""
    # Keep last 72h of observations for readability
    if len(observations) > 432:  # 72h * 6 points/h (10min intervals)
        observations = observations[-432:]

    now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")

    html = TEMPLATE
    html = html.replace("__OBS_JSON__", json.dumps(observations, ensure_ascii=False))
    html = html.replace("__PREV_JSON__", json.dumps(previsions, ensure_ascii=False))
    html = html.replace("__SEUIL__", str(config.SEUIL_SURVEILLANCE))
    html = html.replace("__GENERATED_AT__", now_str)

    return html


def save_html(html: str) -> str:
    """Save HTML to output directory, return file path."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    path = os.path.join(config.OUTPUT_DIR, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info("HTML généré : %s", path)
    return path
