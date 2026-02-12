"""Push HTML file to GitHub Pages via GitHub API."""

import base64
import logging
import requests
import config

logger = logging.getLogger(__name__)

API_BASE = "https://api.github.com"


def _headers():
    return {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_current_sha() -> str | None:
    """Get the SHA of the current file (needed for updates)."""
    url = f"{API_BASE}/repos/{config.GITHUB_REPO}/contents/{config.GITHUB_FILE_PATH}"
    params = {"ref": config.GITHUB_BRANCH}
    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("sha")
        elif resp.status_code == 404:
            return None  # File doesn't exist yet
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("Erreur récupération SHA GitHub : %s", e)
    return None


def push_to_github(html_content: str) -> bool:
    """Push HTML content to GitHub repo. Returns True on success."""
    if not config.GITHUB_TOKEN or not config.GITHUB_REPO:
        logger.warning("GitHub non configuré (token ou repo manquant)")
        return False

    url = f"{API_BASE}/repos/{config.GITHUB_REPO}/contents/{config.GITHUB_FILE_PATH}"

    # Encode content
    content_b64 = base64.b64encode(html_content.encode("utf-8")).decode("ascii")

    # Get current SHA (required for update, None for create)
    sha = _get_current_sha()

    payload = {
        "message": "Update vigicrues data",
        "content": content_b64,
        "branch": config.GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    try:
        resp = requests.put(url, headers=_headers(), json=payload, timeout=30)
        resp.raise_for_status()
        logger.info("HTML poussé sur GitHub Pages")
        return True
    except requests.RequestException as e:
        logger.error("Erreur push GitHub : %s", e)
        return False
