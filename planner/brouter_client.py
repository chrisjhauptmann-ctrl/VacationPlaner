from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any


BROUTER_URL = "https://brouter.de/brouter"

PROFILE_MAP = {
    "gravel": "gravel",
    "touring": "trekking",
    "trekking": "trekking",
    "road": "fastbike",
    "fast": "fastbike",
    "safe": "safety",
}


def validate_route(waypoints: list[dict[str, Any]], route_type: str = "gravel", timeout: int = 120) -> dict[str, Any]:
    if len(waypoints) < 2:
        raise ValueError("At least two waypoints are required")

    profile = PROFILE_MAP.get(route_type, route_type)
    params = {
        "lonlats": "|".join(f"{point['lon']},{point['lat']}" for point in waypoints),
        "profile": profile,
        "alternativeidx": "0",
        "format": "geojson",
    }
    geojson = _fetch_json(params, timeout)
    feature = geojson["features"][0]
    properties = feature["properties"]

    gpx_params = dict(params)
    gpx_params["format"] = "gpx"
    gpx = _fetch_text(gpx_params, timeout)

    return {
        "profile": profile,
        "distance_km": round(int(properties["track-length"]) / 1000, 2),
        "elevation_gain_m": _safe_int(properties.get("filtered ascend")),
        "estimated_time_h": round(int(properties["total-time"]) / 3600, 2),
        "geojson": geojson,
        "gpx": gpx,
    }


def _fetch_json(params: dict[str, str], timeout: int) -> dict[str, Any]:
    url = BROUTER_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "TourPlanner/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _fetch_text(params: dict[str, str], timeout: int) -> str:
    url = BROUTER_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "TourPlanner/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def _safe_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0