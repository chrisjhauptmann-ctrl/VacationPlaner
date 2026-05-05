# 🗺️ VacationPlaner

Automatischer Bikepacking-Routenplaner via BRouter API + GitHub Actions + GitHub Pages.

## Links

- [🗺️ VacationPlaner öffnen](https://chrisjhauptmann-ctrl.github.io/VacationPlaner/)

## Wie es funktioniert

1. **Claude Code** schreibt `input/request.json` mit Startpunkt, Ziel-km/hm, POIs und Campingplätzen
2. **GitHub Actions** triggert automatisch beim Push und führt `planner/route_planner.py` aus
3. **BRouter API** berechnet bis zu 3 Routenvarianten mit echten Straßen- und Höhendaten
4. **Ergebnis** landet in `output/` (GPX, GeoJSON, JSON) und `docs/` (GitHub Pages HTML)

## Struktur

```
input/request.json        ← Claude Code schreibt hier rein
planner/
  brouter_client.py       ← BRouter API Client
  route_planner.py        ← Hauptlogik
output/
  route_1.gpx             ← GPX zum Import in Komoot/Garmin
  route_1.geojson
  summary.json
docs/
  index.html              ← GitHub Pages Visualisierung
```

## request.json Format

```json
{
  "start_lat": 43.1828,
  "start_lon": -1.7794,
  "start_name": "Pamplona, Spain",
  "date": "2026-06-15",
  "target_km": 80,
  "target_hm": 1400,
  "tolerance_km": 10,
  "tolerance_hm": 200,
  "profile": "gravel",
  "num_routes": 3,
  "pois": [
    {"name": "Roncesvalles", "lat": 43.0097, "lon": -1.3197}
  ],
  "campsites": [
    {"name": "Camping Urrobi", "lat": 42.9667, "lon": -1.3333}
  ]
}
```

## Profile

| Wert | BRouter Profil | Für |
|------|---------------|-----|
| `gravel` | gravel | E-MTB, Gravelbike |
| `touring` | trekking | Tourenrad |
| `road` | fastbike | Rennrad |

## GitHub Pages aktivieren

Settings → Pages → Source: `main` branch, `/docs` folder
