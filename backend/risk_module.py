from geopy.distance import geodesic
import dateutil.parser
from collections import Counter

def calculate_risk_score(locations_data):
    """
    Calculates a mobility risk score based on location patterns.
    Rules:
    - +20 if total distance > 300 km
    - +15 if repeated visits > 3
    - +20 if >50% timestamps between 10 PM–5 AM
    - +15 if any jump > 200 km
    """
    if not locations_data:
        return {"risk_score": 0, "risk_level": "Low"}

    risk_score = 0
    total_distance = 0
    max_jump = 0
    nighttime_count = 0
    
    # Sort data by datetime if possible
    try:
        sorted_data = sorted(
            [loc for loc in locations_data if loc.get("datetime")],
            key=lambda x: dateutil.parser.parse(x["datetime"])
        )
    except:
        sorted_data = locations_data

    # Filter out points without coordinates for distance calculations
    valid_data = [loc for loc in sorted_data if loc.get("latitude") is not None and loc.get("longitude") is not None]

    # 1. Total Distance and Max Jump
    for i in range(len(valid_data) - 1):
        p1 = (valid_data[i]["latitude"], valid_data[i]["longitude"])
        p2 = (valid_data[i+1]["latitude"], valid_data[i+1]["longitude"])
        dist = geodesic(p1, p2).kilometers
        total_distance += dist
        if dist > max_jump:
            max_jump = dist

    if total_distance > 300:
        risk_score += 20
    
    if max_jump > 200:
        risk_score += 15

    # 2. Repeated Visits
    # Rounding coordinates to 4 decimal places to identify "same" location (~11m precision)
    coords = [(round(loc["latitude"], 4), round(loc["longitude"], 4)) for loc in locations_data]
    counts = Counter(coords)
    if any(count > 3 for count in counts.values()):
        risk_score += 15

    # 3. Nighttime Activity (10 PM - 5 AM)
    for loc in locations_data:
        try:
            dt = dateutil.parser.parse(loc["datetime"])
            if dt.hour >= 22 or dt.hour < 5:
                nighttime_count += 1
        except:
            continue
    
    if len(locations_data) > 0 and (nighttime_count / len(locations_data)) > 0.5:
        risk_score += 20

    # Risk Level
    risk_level = "Low"
    if risk_score >= 40:
        risk_level = "High"
    elif risk_score >= 20:
        risk_level = "Medium"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level
    }
