import folium
from folium.plugins import HeatMap

def add_heatmap_layer(map_object, locations_data):
    """
    Adds a heatmap layer to an existing Folium map object.
    Does NOT recreate the base map or override existing markers.
    """
    if not locations_data:
        return map_object

    # Extract [lat, lng] pairs
    heat_data = [
        [loc["latitude"], loc["longitude"]] 
        for loc in locations_data 
        if loc.get("latitude") is not None and loc.get("longitude") is not None
    ]
    
    if heat_data:
        HeatMap(heat_data, name="Intensity Heatmap", min_opacity=0.4, blur=15).addTo(map_object)
        
    return map_object
