import os
from typing import List
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.extractor import extract_metadata
from backend.vision_ai import get_landmark_from_image
from backend.analyzer import analyze_timeline
from datetime import datetime
from backend.risk_module import calculate_risk_score
from backend.stats_module import generate_travel_statistics
from backend.report_module import generate_investigation_report, save_report_to_file, generate_pdf_report

app = FastAPI(title="Geospatial Metadata Extractor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("data/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

from fastapi.responses import FileResponse

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/api/analyze_batch")
async def analyze_batch(files: List[UploadFile] = File(...)):
    """
    Accepts multiple image files, extracts metadata, 
    falls back to vision AI if needed, 
    and returns a sorted chronological timeline of movement.
    """
    # Clean up previous uploads to ensure analytics match current session
    uploads_dir = "data/uploads"
    if os.path.exists(uploads_dir):
        import shutil
        shutil.rmtree(uploads_dir)
    os.makedirs(uploads_dir, exist_ok=True)

    extracted_points = []
    processed_images = []

    for file in files:
        file_location = f"data/uploads/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
            
        # Step A: EXIF Extraction
        metadata = extract_metadata(file_location)
        
        point_data = {
            "filename": file.filename,
            "url": f"/data/uploads/{file.filename}", 
            "latitude": metadata.get("latitude"),
            "longitude": metadata.get("longitude"),
            "datetime": metadata.get("datetime"),
            "source": metadata.get("source"),
            "landmark_name": None
        }

        # Step B: Vision Fallback if GPS missing
        if point_data["latitude"] is None or point_data["longitude"] is None:
            vision_result = get_landmark_from_image(file_location)
            
            if vision_result.get("has_vision_data"):
                point_data["latitude"] = vision_result.get("latitude")
                point_data["longitude"] = vision_result.get("longitude")
                point_data["source"] = vision_result.get("source")
                point_data["landmark_name"] = vision_result.get("landmark_name")
                
                # Synthesize a sequential datetime if missing so sorting still draws lines correctly
                if not point_data.get("datetime"):
                     import datetime
                     base_time = datetime.datetime.now() - datetime.timedelta(days=len(files))
                     # Add +1 hour per image processed arbitrarily for chronological sorting
                     fake_time = base_time + datetime.timedelta(hours=len(extracted_points))
                     point_data["datetime"] = fake_time.strftime("%Y-%m-%d %H:%M:%S")
                     
        extracted_points.append(point_data)
        processed_images.append(point_data)

    # Step C: Chronological Sort & Analysis
    analysis_result = analyze_timeline(extracted_points)
    
    return {
        "status": "success",
        "processed_count": len(processed_images),
        "raw_points": processed_images,
        "timeline_analysis": analysis_result
    }

@app.get("/api/download-pdf")
async def download_pdf():
    """
    Generates and returns the investigation report as a PDF.
    """
    uploads_dir = "data/uploads"
    extracted_points = []
    if os.path.exists(uploads_dir):
        from backend.extractor import extract_metadata
        for filename in sorted(os.listdir(uploads_dir)):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(uploads_dir, filename)
                metadata = extract_metadata(file_path)
                
                lat = metadata.get("latitude")
                lng = metadata.get("longitude")
                
                # Only include images with GPS data for the investigative report stats
                if lat is not None and lng is not None:
                    extracted_points.append({
                        "filename": filename,
                        "latitude": lat,
                        "longitude": lng,
                        "datetime": metadata.get("datetime"),
                        "source": metadata.get("source"),
                        "landmark_name": metadata.get("landmark_name")
                    })

    if not extracted_points:
        return {"error": "No data found with GPS coordinates. Upload images first."}

    # Sort chronologically before calculation
    import dateutil.parser
    def get_date(x):
        try:
            return dateutil.parser.parse(x["datetime"]) if x.get("datetime") else datetime.min
        except:
            return datetime.min

    extracted_points.sort(key=get_date)

    risk_data = calculate_risk_score(extracted_points)
    stats_data = generate_travel_statistics(extracted_points)
    pdf_path = generate_pdf_report(extracted_points, risk_data, stats_data)
    
    return FileResponse(
        pdf_path, 
        media_type='application/pdf', 
        filename="investigation_report.pdf"
    )

@app.get("/analytics")
def analytics_page():
    return FileResponse("static/analytics.html")

@app.get("/route-map")
def route_map_page():
    return FileResponse("static/route_map.html")

@app.get("/api/route-info")
async def get_route_info():
    """
    Returns points for route selection.
    """
    uploads_dir = "data/uploads"
    extracted_points = []
    if os.path.exists(uploads_dir):
        from backend.extractor import extract_metadata
        for filename in sorted(os.listdir(uploads_dir)):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(uploads_dir, filename)
                metadata = extract_metadata(file_path)
                
                lat = metadata.get("latitude")
                lng = metadata.get("longitude")
                
                # Only include points with valid coordinates for routing
                if lat is not None and lng is not None:
                    extracted_points.append({
                        "filename": filename,
                        "latitude": lat,
                        "longitude": lng,
                        "datetime": metadata.get("datetime")
                    })
    
    if not extracted_points:
        return {"status": "no_data"}

    # Sort chronologically
    import dateutil.parser
    def get_date(x):
        try:
            return dateutil.parser.parse(x["datetime"]) if x.get("datetime") else datetime.min
        except:
            return datetime.min

    extracted_points.sort(key=get_date)

    return {
        "status": "success",
        "points": extracted_points
    }

@app.get("/api/analytics")
async def get_analytics():
    """
    Returns analytics summary for frontend charts.
    """
    uploads_dir = "data/uploads"
    extracted_points = []
    if os.path.exists(uploads_dir):
        from backend.extractor import extract_metadata
        for filename in sorted(os.listdir(uploads_dir)):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(uploads_dir, filename)
                metadata = extract_metadata(file_path)
                
                lat = metadata.get("latitude")
                lng = metadata.get("longitude")
                
                # Filter points to only those with coordinates
                if lat is not None and lng is not None:
                    extracted_points.append({
                        "datetime": metadata.get("datetime"),
                        "latitude": lat,
                        "longitude": lng,
                        "source": metadata.get("source"),
                        "landmark_name": metadata.get("landmark_name")
                    })
    
    if not extracted_points:
        return {"status": "no_data"}

    # Sort chronologically before calculation
    import dateutil.parser
    def get_date(x):
        try:
            return dateutil.parser.parse(x["datetime"]) if x.get("datetime") else datetime.min
        except:
            return datetime.min

    extracted_points.sort(key=get_date)

    risk_data = calculate_risk_score(extracted_points)
    stats_data = generate_travel_statistics(extracted_points)
    
    return {
        "status": "success",
        "risk": risk_data,
        "stats": stats_data,
        "points": extracted_points
    }

# Also need to mount data volume for frontend to display images
app.mount("/data", StaticFiles(directory="data"), name="data")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
