"""Discord webhook notifications for water level alerts."""

import logging
import requests
import config

logger = logging.getLogger(__name__)


def _send_embed(title: str, description: str, color: int, level: float, trend: str):
    """Send a Discord embed message."""
    if not config.DISCORD_WEBHOOK_URL:
        logger.warning("DISCORD_WEBHOOK_URL non configuré, notification ignorée")
        return False

    # Build GitHub Pages URL
    repo = config.GITHUB_REPO
    if repo:
        owner = repo.split("/")[0]
        repo_name = repo.split("/")[1] if "/" in repo else repo
        page_url = f"https://{owner}.github.io/{repo_name}/"
    else:
        page_url = ""

    embed = {
        "title": title,
        "description": description,
        "color": color,
        "fields": [
            {"name": "Niveau actuel", "value": f"**{level:.2f}m** {trend}", "inline": True},
            {"name": "Seuil surveillance", "value": f"{config.SEUIL_SURVEILLANCE:.2f}m", "inline": True},
        ],
    }
    if page_url:
        embed["fields"].append({"name": "Dashboard", "value": f"[Voir le graphique]({page_url})", "inline": False})

    payload = {
        "username": "Vigicrues Clisson",
        "embeds": [embed],
    }

    try:
        resp = requests.post(config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("Notification Discord envoyée : %s", title)
        return True
    except requests.RequestException as e:
        logger.error("Erreur envoi Discord : %s", e)
        return False


def notify_vigilance(level: float, trend: str):
    """Yellow alert: approaching threshold."""
    _send_embed(
        title="⚠️ Vigilance — La Moine monte",
        description=f"Le niveau de La Moine à Clisson approche le seuil de surveillance.",
        color=0xFFD600,  # yellow
        level=level,
        trend=trend,
    )


def notify_surveillance(level: float, trend: str):
    """Orange alert: threshold exceeded."""
    _send_embed(
        title="🟠 Surveillance — Seuil dépassé",
        description=f"Le niveau de La Moine à Clisson a dépassé le seuil de surveillance de {config.SEUIL_SURVEILLANCE:.2f}m.",
        color=0xFF6B35,  # orange
        level=level,
        trend=trend,
    )


def notify_retour_normal(level: float):
    """Back to normal notification."""
    _send_embed(
        title="✅ Retour à la normale",
        description=f"Le niveau de La Moine à Clisson est repassé sous le seuil de vigilance.",
        color=0x4ECDC4,  # teal
        level=level,
        trend="↘",
    )
