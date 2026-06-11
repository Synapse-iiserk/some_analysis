#!/usr/bin/env python3
"""Generate a simplified India states GeoJSON for the interactive map.

Creates state polygons with approximate boundaries.
This is a simplified version - for production use, download from
the official Survey of India or DataMeet community sources.
"""

import json
from pathlib import Path

OUT = Path("data/processed/chart_data")
OUT.mkdir(parents=True, exist_ok=True)

# Simplified state boundaries - approximate polygons for each Indian state
# Coordinates are [longitude, latitude] pairs forming rough polygon boundaries
# These are simplified versions for visualization purposes

INDIA_STATES = [
    {
        "name": "Andhra Pradesh", "code": "AP",
        "capital": "Amaravati", "region": "South",
        "coordinates": [[[79.5, 18.0], [81.5, 18.0], [84.0, 17.5], [84.5, 16.0], [83.0, 14.5], [80.0, 14.0], [79.0, 15.5], [79.5, 18.0]]]
    },
    {
        "name": "Arunachal Pradesh", "code": "AR",
        "capital": "Itanagar", "region": "Northeast",
        "coordinates": [[[91.5, 27.5], [95.0, 28.5], [97.0, 28.0], [97.5, 26.5], [95.5, 26.0], [92.0, 27.0], [91.5, 27.5]]]
    },
    {
        "name": "Assam", "code": "AS",
        "capital": "Dispur", "region": "Northeast",
        "coordinates": [[[89.5, 25.5], [91.0, 26.0], [92.5, 26.5], [93.5, 27.0], [94.5, 27.0], [95.0, 26.0], [92.0, 25.0], [89.5, 25.5]]]
    },
    {
        "name": "Bihar", "code": "BR",
        "capital": "Patna", "region": "East",
        "coordinates": [[[83.0, 24.5], [85.0, 25.5], [86.5, 26.0], [88.0, 26.5], [88.5, 25.0], [87.0, 24.0], [85.0, 24.0], [83.5, 24.0], [83.0, 24.5]]]
    },
    {
        "name": "Chhattisgarh", "code": "CG",
        "capital": "Raipur", "region": "Central",
        "coordinates": [[[80.0, 22.0], [82.0, 22.5], [83.5, 22.0], [84.0, 20.5], [83.0, 18.5], [81.0, 18.0], [80.0, 19.5], [80.0, 22.0]]]
    },
    {
        "name": "Goa", "code": "GA",
        "capital": "Panaji", "region": "West",
        "coordinates": [[[73.5, 15.0], [74.5, 15.0], [74.5, 14.8], [73.5, 14.8], [73.5, 15.0]]]
    },
    {
        "name": "Gujarat", "code": "GJ",
        "capital": "Gandhinagar", "region": "West",
        "coordinates": [[[68.0, 23.5], [71.0, 24.0], [73.5, 24.5], [74.0, 22.5], [73.0, 20.5], [72.0, 20.0], [69.5, 20.5], [68.0, 22.0], [68.0, 23.5]]]
    },
    {
        "name": "Haryana", "code": "HR",
        "capital": "Chandigarh", "region": "North",
        "coordinates": [[[74.5, 28.0], [77.0, 28.5], [77.5, 30.0], [77.0, 30.5], [74.5, 30.0], [74.5, 28.0]]]
    },
    {
        "name": "Himachal Pradesh", "code": "HP",
        "capital": "Shimla", "region": "North",
        "coordinates": [[[75.5, 31.0], [78.0, 32.0], [79.0, 32.0], [79.0, 30.5], [77.0, 30.0], [75.5, 30.5], [75.5, 31.0]]]
    },
    {
        "name": "Jharkhand", "code": "JH",
        "capital": "Ranchi", "region": "East",
        "coordinates": [[[83.5, 23.5], [85.0, 24.0], [86.0, 24.5], [87.0, 24.5], [87.5, 23.5], [86.5, 22.5], [85.0, 22.0], [84.0, 22.5], [83.5, 23.5]]]
    },
    {
        "name": "Karnataka", "code": "KA",
        "capital": "Bengaluru", "region": "South",
        "coordinates": [[[74.0, 18.0], [76.0, 18.0], [78.0, 18.5], [78.5, 17.0], [77.5, 15.0], [75.5, 14.0], [74.5, 14.5], [74.0, 16.0], [74.0, 18.0]]]
    },
    {
        "name": "Kerala", "code": "KL",
        "capital": "Thiruvananthapuram", "region": "South",
        "coordinates": [[[74.5, 12.0], [77.0, 12.5], [77.0, 11.0], [76.0, 9.0], [75.0, 8.5], [74.0, 10.0], [74.5, 12.0]]]
    },
    {
        "name": "Madhya Pradesh", "code": "MP",
        "capital": "Bhopal", "region": "Central",
        "coordinates": [[[74.0, 21.5], [77.0, 22.0], [78.5, 24.0], [80.0, 24.0], [82.0, 22.5], [82.0, 20.0], [78.0, 19.0], [74.5, 20.0], [74.0, 21.5]]]
    },
    {
        "name": "Maharashtra", "code": "MH",
        "capital": "Mumbai", "region": "West",
        "coordinates": [[[72.5, 20.0], [75.0, 20.0], [76.5, 21.0], [77.5, 21.0], [80.0, 21.0], [80.0, 19.0], [77.0, 16.5], [75.5, 16.0], [73.0, 16.0], [72.5, 18.0], [72.5, 20.0]]]
    },
    {
        "name": "Manipur", "code": "MN",
        "capital": "Imphal", "region": "Northeast",
        "coordinates": [[[93.0, 24.0], [94.5, 24.5], [94.5, 25.0], [93.0, 25.0], [93.0, 24.0]]]
    },
    {
        "name": "Meghalaya", "code": "ML",
        "capital": "Shillong", "region": "Northeast",
        "coordinates": [[[89.5, 25.0], [91.0, 25.0], [92.5, 25.5], [92.5, 26.0], [91.0, 26.0], [89.5, 25.5], [89.5, 25.0]]]
    },
    {
        "name": "Mizoram", "code": "MZ",
        "capital": "Aizawl", "region": "Northeast",
        "coordinates": [[[92.0, 22.0], [93.5, 22.5], [93.5, 23.5], [92.0, 24.0], [92.0, 22.0]]]
    },
    {
        "name": "Nagaland", "code": "NL",
        "capital": "Kohima", "region": "Northeast",
        "coordinates": [[[93.0, 25.0], [95.0, 25.0], [95.5, 26.0], [94.0, 26.5], [93.0, 26.0], [93.0, 25.0]]]
    },
    {
        "name": "Odisha", "code": "OD",
        "capital": "Bhubaneswar", "region": "East",
        "coordinates": [[[81.5, 19.0], [84.0, 20.0], [85.0, 21.0], [86.5, 21.5], [87.0, 20.5], [86.0, 19.0], [83.0, 18.0], [81.5, 19.0]]]
    },
    {
        "name": "Punjab", "code": "PB",
        "capital": "Chandigarh", "region": "North",
        "coordinates": [[[74.0, 29.5], [76.5, 30.0], [77.0, 31.5], [76.0, 32.0], [74.0, 31.0], [74.0, 29.5]]]
    },
    {
        "name": "Rajasthan", "code": "RJ",
        "capital": "Jaipur", "region": "North",
        "coordinates": [[[69.5, 23.0], [73.0, 24.0], [75.0, 25.5], [76.5, 27.0], [77.0, 28.5], [74.5, 28.0], [72.0, 26.0], [70.0, 24.0], [69.5, 23.0]]]
    },
    {
        "name": "Sikkim", "code": "SK",
        "capital": "Gangtok", "region": "Northeast",
        "coordinates": [[[88.0, 27.5], [88.5, 28.0], [88.5, 28.2], [88.0, 28.2], [88.0, 27.5]]]
    },
    {
        "name": "Tamil Nadu", "code": "TN",
        "capital": "Chennai", "region": "South",
        "coordinates": [[[76.0, 10.0], [78.0, 11.0], [80.0, 12.5], [80.0, 13.5], [78.5, 13.5], [77.5, 12.0], [77.0, 10.0], [76.0, 10.0]]]
    },
    {
        "name": "Telangana", "code": "TG",
        "capital": "Hyderabad", "region": "South",
        "coordinates": [[[77.0, 16.0], [80.0, 16.5], [81.0, 18.0], [80.0, 19.5], [78.0, 19.0], [77.0, 18.0], [77.0, 16.0]]]
    },
    {
        "name": "Tripura", "code": "TR",
        "capital": "Agartala", "region": "Northeast",
        "coordinates": [[[91.0, 23.5], [92.0, 24.0], [92.5, 24.0], [92.0, 23.5], [91.0, 23.5]]]
    },
    {
        "name": "Uttar Pradesh", "code": "UP",
        "capital": "Lucknow", "region": "North",
        "coordinates": [[[77.0, 24.5], [80.0, 25.0], [83.0, 25.5], [84.0, 27.0], [84.0, 28.0], [83.0, 28.5], [80.0, 28.5], [77.5, 27.5], [77.0, 25.0], [77.0, 24.5]]]
    },
    {
        "name": "Uttarakhand", "code": "UK",
        "capital": "Dehradun", "region": "North",
        "coordinates": [[[77.5, 28.5], [80.0, 29.0], [81.0, 30.0], [80.5, 31.0], [78.0, 31.0], [77.5, 30.0], [77.5, 28.5]]]
    },
    {
        "name": "West Bengal", "code": "WB",
        "capital": "Kolkata", "region": "East",
        "coordinates": [[[85.5, 24.0], [87.0, 25.0], [88.0, 26.0], [89.0, 27.0], [89.5, 26.0], [88.0, 23.5], [86.0, 22.0], [85.5, 22.5], [85.5, 24.0]]]
    },
    {
        "name": "Andaman and Nicobar Islands", "code": "AN",
        "capital": "Port Blair", "region": "UT",
        "coordinates": [[[92.5, 11.5], [93.5, 12.0], [93.5, 13.0], [92.5, 13.0], [92.5, 11.5]]]
    },
    {
        "name": "Chandigarh", "code": "CH",
        "capital": "Chandigarh", "region": "UT",
        "coordinates": [[[76.7, 30.68], [76.85, 30.68], [76.85, 30.78], [76.7, 30.78], [76.7, 30.68]]]
    },
    {
        "name": "Dadra and Nagar Haveli", "code": "DN",
        "capital": "Daman", "region": "UT",
        "coordinates": [[[73.0, 20.0], [73.2, 20.0], [73.2, 20.2], [73.0, 20.2], [73.0, 20.0]]]
    },
    {
        "name": "Daman and Diu", "code": "DD",
        "capital": "Daman", "region": "UT",
        "coordinates": [[[72.8, 20.4], [73.0, 20.4], [73.0, 20.5], [72.8, 20.5], [72.8, 20.4]]]
    },
    {
        "name": "Delhi", "code": "DL",
        "capital": "New Delhi", "region": "UT",
        "coordinates": [[[76.85, 28.4], [77.35, 28.4], [77.35, 28.9], [76.85, 28.9], [76.85, 28.4]]]
    },
    {
        "name": "Jammu and Kashmir", "code": "JK",
        "capital": "Srinagar", "region": "UT",
        "coordinates": [[[73.0, 32.5], [76.0, 34.0], [78.0, 34.0], [78.5, 33.0], [77.0, 32.0], [74.0, 32.0], [73.0, 32.5]]]
    },
    {
        "name": "Ladakh", "code": "LA",
        "capital": "Leh", "region": "UT",
        "coordinates": [[[75.0, 34.0], [79.0, 35.0], [80.0, 34.0], [79.0, 33.0], [76.0, 33.0], [75.0, 34.0]]]
    },
    {
        "name": "Lakshadweep", "code": "LD",
        "capital": "Kavaratti", "region": "UT",
        "coordinates": [[[72.0, 10.0], [73.0, 10.0], [73.0, 11.0], [72.0, 11.0], [72.0, 10.0]]]
    },
    {
        "name": "Puducherry", "code": "PY",
        "capital": "Puducherry", "region": "UT",
        "coordinates": [[[79.5, 11.8], [79.9, 11.8], [79.9, 12.0], [79.5, 12.0], [79.5, 11.8]]]
    },
]


def build_geojson():
    """Build GeoJSON for India states."""
    features = []
    for state in INDIA_STATES:
        feature = {
            "type": "Feature",
            "properties": {
                "name": state["name"],
                "code": state["code"],
                "capital": state["capital"],
                "region": state["region"]
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": state["coordinates"]
            }
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    return geojson


def build_state_centers():
    """Build state center points for the bubble map."""
    centers = {}
    for state in INDIA_STATES:
        # Calculate centroid of the polygon
        coords = state["coordinates"][0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        centers[state["name"]] = {
            "lon": sum(lons) / len(lons),
            "lat": sum(lats) / len(lats)
        }
    return centers


if __name__ == "__main__":
    geojson = build_geojson()
    with open(OUT / "india_states_geojson.json", "w") as f:
        json.dump(geojson, f, indent=2)
    print(f"GeoJSON: {len(geojson['features'])} features")

    centers = build_state_centers()
    with open(OUT / "state_centers.json", "w") as f:
        json.dump(centers, f, indent=2)
    print(f"State centers: {len(centers)} states")
