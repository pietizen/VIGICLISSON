# Vigicrues Monitor — La Moine à Clisson

Monitoring automatique du niveau de La Moine (station M730242010) avec dashboard GitHub Pages et alertes Discord.

## Fonctionnement

- Interroge l'API Vigicrues toutes les 30 min (cron)
- Génère une page HTML interactive (Chart.js) avec observations + prévisions
- Pousse la page sur GitHub Pages
- Envoie une alerte Discord si le niveau dépasse les seuils configurés

## Seuils

| Niveau | Action |
|--------|--------|
| ≥ 1.80m | Notification Discord "Vigilance" |
| ≥ 2.00m | Notification Discord "Surveillance" |
| Retour < 1.80m | Notification "Retour à la normale" |

## Installation

```bash
cp .env.example .env
# Éditer .env avec tes valeurs
pip install -r requirements.txt
python3 main.py
```

## Déploiement VPS

Voir les instructions de déploiement dans la documentation du projet.
