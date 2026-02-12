import os
from dotenv import load_dotenv

load_dotenv()

# --- Vigicrues API ---
STATION_ID = "M730242010"
STATION_NAME = "La Moine à Clisson"
OBS_URL = f"https://www.vigicrues.gouv.fr/services/observations.json/index.php?CdStationHydro={STATION_ID}&FormatDate=iso"
PREV_URL = f"https://www.vigicrues.gouv.fr/services/previsions.json/index.php?CdStationHydro={STATION_ID}&FormatDate=iso"

# --- Seuils (mètres) ---
SEUIL_VIGILANCE = 1.80
SEUIL_SURVEILLANCE = 2.00

# --- Discord ---
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# --- GitHub Pages ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")  # format: "owner/repo-name"
GITHUB_FILE_PATH = "index.html"
GITHUB_BRANCH = "main"

# --- Paths ---
STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

# --- Timeouts ---
REQUEST_TIMEOUT = 15
MAX_RETRIES = 2
