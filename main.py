#!/usr/bin/env python3
"""Vigicrues Monitor — La Moine à Clisson.

Fetches water level data, generates a dashboard, pushes to GitHub Pages,
and sends Discord alerts when thresholds are exceeded.
"""

import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import config
from fetch_data import fetch_observations, fetch_previsions
from generate_html import generate_html, save_html
from push_github import push_to_github
from notify import notify_vigilance, notify_surveillance, notify_retour_normal

# --- Logging setup ---
LOG_DIR = "/var/log/vigicrues-monitor"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# File handler with rotation
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "monitor.log"),
    maxBytes=1_000_000,
    backupCount=5,
)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s"))
logger.addHandler(file_handler)

# Console handler (useful for manual runs)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(console_handler)


def load_state() -> dict:
    """Load persistent state from JSON file."""
    if os.path.exists(config.STATE_FILE):
        with open(config.STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "last_dt_prod_simul": None,
        "last_observation_dt": None,
        "last_alert_level": None,
    }


def save_state(state: dict):
    """Save state to JSON file."""
    with open(config.STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_trend(observations: list[dict]) -> str:
    """Determine trend from recent observations."""
    if len(observations) < 7:
        return "→"
    current = observations[-1]["level"]
    previous = observations[-7]["level"]
    if current > previous + 0.02:
        return "↗"
    elif current < previous - 0.02:
        return "↘"
    return "→"


def evaluate_alerts(level: float, trend: str, state: dict) -> dict:
    """Check thresholds, send alerts if needed, return updated state."""
    last_alert = state.get("last_alert_level")

    if level >= config.SEUIL_SURVEILLANCE:
        if last_alert != "surveillance":
            notify_surveillance(level, trend)
            state["last_alert_level"] = "surveillance"
    elif level >= config.SEUIL_VIGILANCE:
        if last_alert != "vigilance":
            notify_vigilance(level, trend)
            state["last_alert_level"] = "vigilance"
    else:
        if last_alert is not None:
            notify_retour_normal(level)
            state["last_alert_level"] = None

    return state


def main():
    logger.info("=== Démarrage vigicrues-monitor ===")
    state = load_state()

    # 1. Fetch data
    observations = fetch_observations()
    if not observations:
        logger.error("Impossible de récupérer les observations, arrêt")
        return

    previsions = fetch_previsions()
    # Previsions can be None (no active forecast) — we continue without

    # 2. Check if data has changed
    current_obs_dt = observations[-1]["dt"]
    current_prev_dt = previsions["dt_prod"] if previsions else None

    obs_changed = current_obs_dt != state.get("last_observation_dt")
    prev_changed = current_prev_dt != state.get("last_dt_prod_simul")

    if not obs_changed and not prev_changed:
        logger.info("Pas de nouvelles données, rien à faire")
        return

    logger.info(
        "Nouvelles données — obs: %s (changé: %s), prev: %s (changé: %s)",
        current_obs_dt, obs_changed, current_prev_dt, prev_changed
    )

    # 3. Generate HTML
    if previsions:
        html = generate_html(observations, previsions)
    else:
        # Generate with empty previsions
        html = generate_html(observations, {"dt_prod": "N/A", "prevs": []})
    save_html(html)

    # 4. Push to GitHub Pages
    push_to_github(html)

    # 5. Evaluate alerts
    current_level = observations[-1]["level"]
    trend = get_trend(observations)
    state = evaluate_alerts(current_level, trend, state)

    # 6. Save state
    state["last_observation_dt"] = current_obs_dt
    state["last_dt_prod_simul"] = current_prev_dt
    save_state(state)

    logger.info("Terminé — niveau actuel : %.2fm %s", current_level, trend)


if __name__ == "__main__":
    main()
