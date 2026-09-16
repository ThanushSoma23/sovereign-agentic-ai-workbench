from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_document(output_path: str):
    # Create white canvas 800x600
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    lines = [
        "EQUIPMENT INSPECTION REPORT",
        "------------------------------------",
        "Report ID: INSP-2026-9941",
        "Facility: Air-Gapped Workbench Node A",
        "Inspector: M4 Engineer",
        "Date: 2026-09-16",
        "System Status: OPERATIONAL",
        "CPU Load: 42%",
        "Thermal Status: NORMAL",
        "Notes: All diagnostic checks passed cleanly.",
        "------------------------------------",
        "Verification Code: SIH-2026-SOVEREIGN"
    ]

    y = 50
    for line in lines:
        draw.text((50, y), line, fill=(0, 0, 0))
        y += 40

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"Sample test document created at: {output_path}")

if __name__ == "__main__":
    create_sample_document("c:/Users/somat/Desktop/SIH/sample_data/test_report.png")
