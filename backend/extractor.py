import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def _get_decimal_from_dms(dms, ref):
    """
    Converts GPS coordinates in degrees, minutes, seconds to decimal.
    """
    degrees = dms[0]
    minutes = dms[1]
    seconds = dms[2]

    try:
        # Compatibility with different formats Pillow might return
        deg = float(degrees[0]) / float(degrees[1]) if isinstance(degrees, tuple) else float(degrees)
        min_val = float(minutes[0]) / float(minutes[1]) if isinstance(minutes, tuple) else float(minutes)
        sec = float(seconds[0]) / float(seconds[1]) if isinstance(seconds, tuple) else float(seconds)
    except:
        deg = float(degrees)
        min_val = float(minutes)
        sec = float(seconds)

    decimal = deg + (min_val / 60.0) + (sec / 3600.0)
    
    if ref in ['S', 'W']:
        decimal = -decimal
        
    return decimal

def _get_exif_data(image):
    """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]
                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value
    return exif_data

def extract_metadata(image_path: str):
    """
    Extracts GPS coordinates and datetime from an image's EXIF data.
    """
    try:
        image = Image.open(image_path)
        exif_data = _get_exif_data(image)
        
        result = {
            "has_exif": False,
            "latitude": None,
            "longitude": None,
            "datetime": None,
            "source": "None"
        }
        
        if not exif_data:
            return result

        result["has_exif"] = True
        
        if "DateTimeOriginal" in exif_data:
             date_str = str(exif_data["DateTimeOriginal"])
             # Standard EXIF format is YYYY:MM:DD HH:MM:SS
             # JS/Date parsers prefer YYYY-MM-DD HH:MM:SS or ISO
             if len(date_str) >= 10 and date_str[4] == ":" and date_str[7] == ":":
                 date_str = date_str[:4] + "-" + date_str[5:7] + "-" + date_str[8:]
             result["datetime"] = date_str

        if "GPSInfo" in exif_data:
            gps_info = exif_data["GPSInfo"]
            
            if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info \
               and "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
               
               lat = _get_decimal_from_dms(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])
               lon = _get_decimal_from_dms(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])
               
               result["latitude"] = lat
               result["longitude"] = lon
               result["source"] = "EXIF"
        
        return result
    except Exception as e:
        print(f"Error extracting metadata from {image_path}: {e}")
        return {
            "has_exif": False,
            "error": str(e)
        }
