"""Fetch observations and forecast data from Vigicrues API."""

import logging
import time
import requests
import config

logger = logging.getLogger(__name__)


def _fetch_json(url: str) -> dict | None:
    """Fetch JSON from URL with retry."""
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning("Tentative %d/%d échouée pour %s : %s", attempt, config.MAX_RETRIES, url, e)
            if attempt < config.MAX_RETRIES:
                time.sleep(5 * attempt)
    logger.error("Impossible de récupérer %s après %d tentatives", url, config.MAX_RETRIES)
    return None


def fetch_observations() -> list[dict] | None:
    """Return list of {dt, level} or None on error."""
    data = _fetch_json(config.OBS_URL)
    if not data:
        return None
    try:
        obs = data["Serie"]["ObssHydro"]
        return [{"dt": o["DtObsHydro"], "level": o["ResObsHydro"]} for o in obs]
    except (KeyError, TypeError) as e:
        logger.error("Structure observations inattendue : %s", e)
        return None


def fetch_previsions() -> dict | None:
    """Return {dt_prod, prevs: [{dt, min, moy, max}]} or None."""
    data = _fetch_json(config.PREV_URL)
    if not data:
        return None
    try:
        simul = data["Simul"]
        prevs = [
            {
                "dt": p["DtPrev"],
                "min": p["ResMinPrev"],
                "moy": p["ResMoyPrev"],
                "max": p["ResMaxPrev"],
            }
            for p in simul["Prevs"]
        ]
        return {"dt_prod": simul["DtProdSimul"], "prevs": prevs}
    except (KeyError, TypeError) as e:
        logger.error("Structure prévisions inattendue : %s", e)
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    obs = fetch_observations()
    if obs:
        print(f"Observations : {len(obs)} points, dernier = {obs[-1]}")
    prev = fetch_previsions()
    if prev:
        print(f"Prévisions : {len(prev['prevs'])} points, produit le {prev['dt_prod']}")
