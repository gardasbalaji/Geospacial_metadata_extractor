from geopy.distance import geodesic
from datetime import datetime
import dateutil.parser

def calculate_velocity(p1, p2):
    """
    p1, p2 are dicts: {"latitude": float, "longitude": float, "datetime": str}
    Returns distance (km), time_diff (hours), and speed (km/h)
    """
    try:
        coord1 = (p1["latitude"], p1["longitude"])
        coord2 = (p2["latitude"], p2["longitude"])
        
        distance_km = geodesic(coord1, coord2).kilometers
        
        t1 = dateutil.parser.parse(p1["datetime"])
        t2 = dateutil.parser.parse(p2["datetime"])
        
        time_diff_hours = abs((t2 - t1).total_seconds()) / 3600.0
        
        if time_diff_hours == 0:
            speed_kmh = float("inf")
        else:
            speed_kmh = distance_km / time_diff_hours
            
        return {
            "distance_km": round(distance_km, 2),
            "time_diff_hours": round(time_diff_hours, 2),
            "speed_kmh": round(speed_kmh, 2)
        }
    except Exception as e:
        return {"error": str(e)}

def analyze_timeline(points):
    """
    Sorts a list of locations chronologically and flags impossible travel.
    """
    # Filter points to those that have dates and valid coords
    valid_points = [
        p for p in points 
        if p.get("latitude") and p.get("longitude") and p.get("datetime")
    ]
    
    # Sort by datetime
    try:
        sorted_points = sorted(
            valid_points, 
            key=lambda p: dateutil.parser.parse(p["datetime"])
        )
    except:
        return {"error": "Date casting error", "timeline": points}

    timeline = []
    
    # Analyze point-to-point sequences
    for i in range(len(sorted_points)):
        current = sorted_points[i]
        
        analysis = {
            "point": current,
            "flagged": False,
            "reason": None,
            "movement_metrics": None
        }

        if i > 0:
            previous = sorted_points[i-1]
            metrics = calculate_velocity(previous, current)
            
            if "error" not in metrics:
                analysis["movement_metrics"] = metrics
                
                # Flag impossible travel: if speed > 1000 km/h (Commercial jets are ~900 km/h)
                if metrics["speed_kmh"] > 1000:
                    analysis["flagged"] = True
                    analysis["reason"] = f"Impossible velocity detected: {metrics['speed_kmh']} km/h"

        timeline.append(analysis)
        
    return {
        "chronological_timeline": timeline,
        "total_points_analyzed": len(valid_points)
    }
