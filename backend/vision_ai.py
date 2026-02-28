import os
from PIL import Image

try:
    from transformers import pipeline
    # Load a lightweight image classification model for general landmarks/locations
    # Using ResNet or similar small model for speed in demonstration
    vision_classifier = pipeline("image-classification", model="google/vit-base-patch16-224")
    HF_AVAILABLE = True
except Exception as e:
    print(f"HuggingFace not available: {e}")
    HF_AVAILABLE = False

try:
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="geospatial_extractor_demo")
    GEO_AVAILABLE = True
except Exception as e:
    print(f"Geopy Nominatim not available: {e}")
    GEO_AVAILABLE = False

# We'll use the google.cloud vision API if credentials match
try:
    from google.cloud import vision
except ImportError:
    vision = None

def get_landmark_from_image(image_path: str):
    """
    Fallback method when EXIF is missing. Uses Google Cloud Vision
    or an offline HuggingFace model + Geocoding.
    """
    if not os.path.exists("credentials.json"):
        print(f"[Fallback AI] Analyzing {image_path} with open-source models...")
        
        if not HF_AVAILABLE or not GEO_AVAILABLE:
            return {"has_vision_data": False, "error": "AI models not installed"}
            
        try:
            image = Image.open(image_path)
            # The ViT model returns ImageNet classes. We'll grab the top prediction.
            # Real-world usage would prefer a dedicated landmark model (e.g. google/deit-base-patch16-224)
            preds = vision_classifier(image)
            top_prediction = preds[0]['label'].split(',')[0] # Get primary noun, e.g., "alp", "palace"
            
            print(f"AI Detected: {top_prediction} (Confidence: {preds[0]['score']:.2f})")
            
            # Geocode the detected term to get latitude/longitude
            location = geolocator.geocode(top_prediction)
            
            if location:
                return {
                    "has_vision_data": True,
                    "source": "HuggingFace + Nominatim",
                    "landmark_name": f"Identified as: {top_prediction.title()}",
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "confidence": preds[0]['score']
                }
            else:
                 return {
                    "has_vision_data": True,
                    "source": "AI (No GPS mapping found)",
                    "landmark_name": f"{top_prediction.title()}",
                    "latitude": 0.0, 
                    "longitude": 0.0,
                    "confidence": preds[0]['score']
                }

        except Exception as e:
            print(f"AI Pipeline Error: {e}")
            return {"has_vision_data": False, "error": str(e)}
    
    if vision is None:
        return {"has_vision_data": False, "error": "google-cloud-vision not installed"}
        
    try:
        # In a real environment, set GOOGLE_APPLICATION_CREDENTIALS
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("credentials.json")
        client = vision.ImageAnnotatorClient()
        
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = client.landmark_detection(image=image)
        landmarks = response.landmark_annotations
        
        if landmarks:
            # We take the first match (highest confidence)
            landmark = landmarks[0]
            if len(landmark.locations) > 0:
                location = landmark.locations[0].lat_lng
                return {
                    "has_vision_data": True,
                    "source": "Google Vision",
                    "landmark_name": landmark.description,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "confidence": landmark.score
                }
        
        return {"has_vision_data": False, "error": "No landmarks detected by Vision API"}

    except Exception as e:
        print(f"Vision API Error: {e}")
        return {"has_vision_data": False, "error": str(e)}
