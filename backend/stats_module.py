from collections import Counter

def generate_travel_statistics(locations_data):
    """
    Generates summary statistics for a travel timeline.
    """
    if not locations_data:
        return {
            "total_distance_km": 0,
            "unique_locations_count": 0,
            "most_visited_location": "None",
            "average_movement_km": 0,
            "total_movements": 0
        }

    import math
    def haversine(p1, p2):
        if not p1 or not p2: return 0
        R = 6371.0 # Earth radius in km
        lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
        lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    total_distance = 0.0
    movements = 0
    
    # 1. Total Distance and Movements
    valid_points = [p for p in locations_data if p.get("latitude") is not None and p.get("longitude") is not None]
    
    for i in range(len(valid_points) - 1):
        p1 = (valid_points[i]["latitude"], valid_points[i]["longitude"])
        p2 = (valid_points[i+1]["latitude"], valid_points[i+1]["longitude"])
        dist = haversine(p1, p2)
        total_distance += dist
        movements += 1

    # 2. Unique Locations and Most Visited
    coords = [(round(loc["latitude"], 4), round(loc["longitude"], 4)) for loc in valid_points]
    unique_coords = set(coords)
    counts = Counter(coords)
    
    most_visited = "None"
    if counts:
        top_coord, count = counts.most_common(1)[0]
        # Try to find a landmark name if available
        landmark_name = None
        for loc in locations_data:
            if round(loc["latitude"], 4) == top_coord[0] and round(loc["longitude"], 4) == top_coord[1]:
                landmark_name = loc.get("landmark_name")
                if landmark_name: break
        
        loc_str = landmark_name if landmark_name else f"Lat: {top_coord[0]}, Lng: {top_coord[1]}"
        if count > 1:
            most_visited = f"{loc_str} ({count} visits)"
        else:
            most_visited = f"{loc_str}"

    avg_movement = total_distance / movements if movements > 0 else 0

    return {
        "total_distance_km": round(total_distance, 2),
        "unique_locations_count": len(unique_coords),
        "most_visited_location": most_visited,
        "average_movement_km": round(avg_movement, 2),
        "total_movements": movements
    }
