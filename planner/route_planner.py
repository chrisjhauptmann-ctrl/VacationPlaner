"""
VacationPlaner - Route Planner
Reads input/request.json, generates up to N route variants via BRouter,
evaluates them against target km/hm, and writes results to output/ and docs/.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from brouter_client import validate_route

ROOT = Path(__file__).parent.parent
INPUT_FILE = ROOT / "input" / "request.json"
OUTPUT_DIR = ROOT / "output"
DOCS_DIR = ROOT / "docs"


def load_request() -> dict[str, Any]:
    with open(INPUT_FILE) as f:
        return json.load(f)


def build_waypoints(req: dict[str, Any], poi_subset: list[dict]) -> list[dict]:
    """Build waypoint list: start -> selected POIs -> campsite."""
    waypoints = [{"lat": req["start_lat"], "lon": req["start_lon"]}]
    waypoints.extend(poi_subset)
    # pick first campsite as endpoint (route variants use different campsites)
    if req.get("campsites"):
        waypoints.append(req["campsites"][0])
    return waypoints


def evaluate(result: dict, req: dict) -> dict:
    """Check if route meets target km/hm within tolerance."""
    target_km = req["target_km"]
    target_hm = req["target_hm"]
    tol_km = req.get("tolerance_km", 10)
    tol_hm = req.get("tolerance_hm", 200)

    km_ok = abs(result["distance_km"] - target_km) <= tol_km
    hm_ok = abs(result["elevation_gain_m"] - target_hm) <= tol_hm

    return {
        "km_ok": km_ok,
        "hm_ok": hm_ok,
        "meets_target": km_ok and hm_ok,
        "km_diff": round(result["distance_km"] - target_km, 1),
        "hm_diff": result["elevation_gain_m"] - target_hm,
    }


def plan_routes(req: dict) -> list[dict]:
    """Generate route variants by using different POI/campsite combos."""
    pois = req.get("pois", [])
    campsites = req.get("campsites", [])
    num_routes = req.get("num_routes", 3)
    profile = req.get("profile", "gravel")

    routes = []

    # Variant strategy: cycle through campsites and POI subsets
    for i in range(num_routes):
        campsite = campsites[i % len(campsites)] if campsites else None
        # Use all POIs for first route, then drop last POI for variants
        poi_subset = pois[:max(1, len(pois) - i)] if pois else []

        waypoints = [{"lat": req["start_lat"], "lon": req["start_lon"]}]
        waypoints.extend(poi_subset)
        if campsite:
            waypoints.append(campsite)

        variant_name = f"Route {i+1}: via {', '.join(p['name'] for p in poi_subset)}"
        if campsite:
            variant_name += f" → {campsite['name']}"

        print(f"  Calculating {variant_name}...")
        try:
            result = validate_route(waypoints, route_type=profile)
            evaluation = evaluate(result, req)
            routes.append({
                "name": variant_name,
                "waypoints": waypoints,
                "pois": poi_subset,
                "campsite": campsite,
                **result,
                "evaluation": evaluation,
            })
            print(f"    → {result['distance_km']} km, {result['elevation_gain_m']} hm | meets target: {evaluation['meets_target']}")
        except Exception as e:
            print(f"    ✗ Failed: {e}")
            routes.append({
                "name": variant_name,
                "error": str(e),
                "evaluation": {"meets_target": False},
            })

    return routes


def save_gpx(route: dict, idx: int) -> str:
    fname = f"route_{idx+1}.gpx"
    path = OUTPUT_DIR / fname
    if route.get("gpx"):
        path.write_text(route["gpx"])
    return fname


def save_geojson(route: dict, idx: int) -> str:
    fname = f"route_{idx+1}.geojson"
    path = OUTPUT_DIR / fname
    if route.get("geojson"):
        path.write_text(json.dumps(route["geojson"], indent=2))
    return fname


def build_html(req: dict, routes: list[dict], timestamp: str) -> str:
    route_cards = ""
    for i, r in enumerate(routes):
        ev = r.get("evaluation", {})
        status = "✅ Ziel erfüllt" if ev.get("meets_target") else "⚠️ Außerhalb Toleranz"
        err = r.get("error", "")
        if err:
            status = f"❌ Fehler: {err}"

        gpx_link = f'<a href="../output/route_{i+1}.gpx" download>⬇ GPX</a>' if r.get("gpx") else ""

        km_diff = ev.get("km_diff", 0)
        hm_diff = ev.get("hm_diff", 0)
        km_color = "#2ecc71" if ev.get("km_ok") else "#e74c3c"
        hm_color = "#2ecc71" if ev.get("hm_ok") else "#e74c3c"

        route_cards += f"""
        <div class="card">
          <h2>{r['name']}</h2>
          <div class="status">{status}</div>
          <div class="stats">
            <span style="color:{km_color}">🚴 {r.get('distance_km','?')} km ({km_diff:+.1f})</span>
            <span style="color:{hm_color}">⛰️ {r.get('elevation_gain_m','?')} hm ({hm_diff:+.0f})</span>
            <span>⏱️ {r.get('estimated_time_h','?')} h</span>
          </div>
          <div class="gpx">{gpx_link}</div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VacationPlaner – {req.get('start_name','Route')}</title>
  <style>
    body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 1rem; background: #f5f5f5; }}
    h1 {{ color: #2c3e50; }}
    .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 1.5rem; }}
    .card {{ background: white; border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 1rem; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }}
    h2 {{ margin: 0 0 0.4rem; font-size: 1rem; color: #2c3e50; }}
    .status {{ font-weight: bold; margin-bottom: 0.6rem; }}
    .stats {{ display: flex; gap: 1.5rem; flex-wrap: wrap; font-size: 1.05rem; }}
    .gpx {{ margin-top: 0.8rem; }}
    .gpx a {{ background: #3498db; color: white; padding: 0.3rem 0.8rem; border-radius: 6px; text-decoration: none; font-size: 0.9rem; }}
    .target {{ background: #eaf4fb; border-left: 4px solid #3498db; padding: 0.6rem 1rem; border-radius: 4px; margin-bottom: 1.5rem; }}
  </style>
</head>
<body>
  <h1>🗺️ VacationPlaner</h1>
  <div class="meta">Start: {req.get('start_name')} | Datum: {req.get('date')} | Berechnet: {timestamp}</div>
  <div class="target">🎯 Ziel: {req['target_km']} km ±{req.get('tolerance_km',10)} | {req['target_hm']} hm ±{req.get('tolerance_hm',200)}</div>
  {route_cards}
</body>
</html>"""


def main():
    print("=== VacationPlaner ===")
    req = load_request()
    print(f"Start: {req.get('start_name')} | Ziel: {req['target_km']} km / {req['target_hm']} hm")
    print(f"Profil: {req.get('profile','gravel')} | Routen: {req.get('num_routes',3)}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    DOCS_DIR.mkdir(exist_ok=True)

    print("\nBerechne Routen via BRouter...")
    routes = plan_routes(req)

    # Save GPX + GeoJSON
    for i, r in enumerate(routes):
        if not r.get("error"):
            save_gpx(r, i)
            save_geojson(r, i)

    # Save summary JSON
    summary = {
        "request": req,
        "timestamp": datetime.utcnow().isoformat(),
        "routes": [
            {k: v for k, v in r.items() if k not in ("gpx", "geojson")}
            for r in routes
        ],
    }
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))

    # Build GitHub Pages HTML
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    html = build_html(req, routes, ts)
    (DOCS_DIR / "index.html").write_text(html)

    # Print summary
    print("\n=== Ergebnis ===")
    for r in routes:
        ev = r.get("evaluation", {})
        ok = "✅" if ev.get("meets_target") else "⚠️"
        print(f"{ok} {r['name']}: {r.get('distance_km','?')} km / {r.get('elevation_gain_m','?')} hm")

    print("\nOutput gespeichert in output/ und docs/")


if __name__ == "__main__":
    main()
