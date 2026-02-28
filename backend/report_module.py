import os
from datetime import datetime

def generate_investigation_report(locations_data, risk_data, stats_data):
    """
    Compiles an investigation report into a formatted text summary.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = []
    report.append("====================================================")
    report.append("          TRACESIGHT AI - INVESTIGATION REPORT      ")
    report.append("====================================================")
    report.append(f"Generated on: {timestamp}")
    report.append(f"Total Points Processed: {len(locations_data)}")
    report.append("")
    
    report.append("--- MOBILITY RISK ASSESSMENT ---")
    report.append(f"Risk Score: {risk_data.get('risk_score', 'N/A')}")
    report.append(f"Risk Level: {risk_data.get('risk_level', 'Unknown')}")
    report.append("")
    
    report.append("--- TRAVEL STATISTICS ---")
    report.append(f"Total Distance: {stats_data.get('total_distance_km', 0)} km")
    report.append(f"Unique Locations: {stats_data.get('unique_locations_count', 0)}")
    report.append(f"Most Visited: {stats_data.get('most_visited_location', 'None')}")
    report.append(f"Avg Movement: {stats_data.get('average_movement_km', 0)} km")
    report.append(f"Total Movements: {stats_data.get('total_movements', 0)}")
    report.append("")
    
    report.append("--- DATASET LOG ---")
    for i, loc in enumerate(locations_data):
        dt = loc.get("datetime", "Unknown Time")
        lat = loc.get("latitude", 0)
        lng = loc.get("longitude", 0)
        src = loc.get("source", "Unknown")
        landmark = loc.get("landmark_name")
        
        entry = f"[{i+1}] {dt} | Coords: ({lat}, {lng}) | Source: {src}"
        if landmark:
            entry += f" | Location: {landmark}"
        report.append(entry)
    
    report.append("")
    report.append("====================================================")
    report.append("             END OF INVESTIGATION REPORT            ")
    report.append("====================================================")
    
    return "\n".join(report)

def generate_pdf_report(locations_data, risk_data, stats_data):
    """
    Generates a professional PDF report.
    """
    from fpdf import FPDF
    
    class PDF(FPDF):
        def header(self):
            # Banner
            self.set_fill_color(26, 26, 26)
            self.rect(0, 0, 210, 40, 'F')
            self.set_font('Helvetica', 'B', 24)
            self.set_text_color(255, 255, 255)
            self.cell(0, 15, 'TRACESIGHT AI', ln=True, align='C')
            self.set_font('Helvetica', 'I', 12)
            self.cell(0, 10, 'Investigative Geospatial Analysis Report', ln=True, align='C')
            self.ln(15)

        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Summary Section
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(33, 37, 41)
    pdf.cell(0, 10, 'Executive Summary', ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 8, f'Report Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ln=True)
    pdf.cell(0, 8, f'Total Data Points: {len(locations_data)}', ln=True)
    pdf.ln(5)

    # Risk Assessment
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Mobility Risk Assessment', ln=True)
    
    risk_lv = risk_data.get('risk_level', 'Low')
    score = risk_data.get('risk_score', 0)
    
    # Color coding risk
    if risk_lv == 'High': pdf.set_text_color(220, 53, 69)
    elif risk_lv == 'Medium': pdf.set_text_color(255, 159, 10)
    else: pdf.set_text_color(40, 167, 69)
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, f'Risk Level: {risk_lv} (Score: {score})', ln=True)
    pdf.set_text_color(33, 37, 41)
    pdf.ln(5)

    # Statistics
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Travel Statistics', ln=True)
    pdf.set_font('Helvetica', '', 11)
    
    stats_fields = [
        ('Total Distance', f"{stats_data.get('total_distance_km', 0)} km"),
        ('Unique Locations', f"{stats_data.get('unique_locations_count', 0)}"),
        ('Most Visited', f"{stats_data.get('most_visited_location', 'None')}"),
        ('Avg Movement', f"{stats_data.get('average_movement_km', 0)} km"),
        ('Total Movements', f"{stats_data.get('total_movements', 0)}")
    ]
    
    for label, val in stats_fields:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(40, 8, f"{label}:", 0)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 8, str(val), ln=True)
    
    pdf.ln(10)

    # Data Log Table
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Detailed Activity Log', ln=True)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_fill_color(240, 240, 240)
    
    # Header
    pdf.cell(40, 8, 'Timestamp', border=1, fill=True)
    pdf.cell(30, 8, 'Coordinates', border=1, fill=True)
    pdf.cell(30, 8, 'Source', border=1, fill=True)
    pdf.cell(90, 8, 'Context / Landmark', border=1, fill=True, ln=True)
    
    pdf.set_font('Helvetica', '', 7)
    for loc in locations_data:
        dt = loc.get("datetime", "N/A")
        coords = f"{loc.get('latitude', 0):.4f}, {loc.get('longitude',0):.4f}"
        src = loc.get("source", "N/A")
        landmark = loc.get("landmark_name") or "Unknown"
        
        pdf.cell(40, 7, str(dt), border=1)
        pdf.cell(30, 7, coords, border=1)
        pdf.cell(30, 7, src, border=1)
        pdf.cell(90, 7, str(landmark)[:60], border=1, ln=True)

    output_dir = "data/reports"
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "investigation_report.pdf")
    pdf.output(pdf_path)
    return pdf_path

def save_report_to_file(report_text, filename="investigation_report.txt"):
    """
    Saves the report text to a temporary or data directory for download.
    """
    output_dir = "data/reports"
    os.makedirs(output_dir, exist_ok=True)
    full_path = os.path.join(output_dir, filename)
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    return full_path
