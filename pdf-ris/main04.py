import pytesseract
from pdf2image import convert_from_path
import cv2
import pandas as pd
import numpy as np
from pathlib import Path

# ---------------------------------------
# INPUT PDF
# ---------------------------------------
pdf_path = Path(r"E:\XRZONE_Files\PDFReader\PDFReader\pdf-ris\samples\v3\Jitta Collectie Wat ons blijvend boeit.pdf")
base_name = pdf_path.stem
output_dir = pdf_path.parent

# OCR total output
ocr_total_path = output_dir / f"{base_name}_total.txt"

# ---------------------------------------
# OCR SETTINGS
# ---------------------------------------
OCR_DPI = 300
TESSERACT_CONFIG = "--oem 3 --psm 6"  # Line-based OCR

# Poppler path (must point to 'bin' folder)
POPPLER_PATH = r"E:\XRZONE_Files\PDFReader\PDFReader\pdf-ris\poppler-25.11.0\Library\bin"

# ---------------------------------------
# RUN OCR (pages → paragraphs → lines)
# ---------------------------------------
print("🔍 Converting PDF pages to images...")
pages = convert_from_path(str(pdf_path), OCR_DPI, poppler_path=POPPLER_PATH)

master_lines = []

print("🔠 Running Tesseract OCR...")
for i, page in enumerate(pages, start=1):
    # Convert to grayscale + threshold
    gray = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    # OCR data dictionary
    data = pytesseract.image_to_data(thresh, config=TESSERACT_CONFIG, output_type="dict")
    df = pd.DataFrame(data)
    df = df[df["conf"].astype(float) > 0]  # Keep only confident text

    # Build lines grouped by (page, paragraph, line)
    page_dict = {}
    for idx, row in df.iterrows():
        key = f"{i}_{row['par_num']}_{row['line_num']}"
        text = str(row["text"]).strip()
        if not text:
            continue
        if key not in page_dict:
            page_dict[key] = text
        else:
            page_dict[key] += " " + text

    # Append ordered text lines
    for key in sorted(page_dict.keys()):
        master_lines.append(page_dict[key])

print("💾 Saving OCR total text...")
ocr_total_path.write_text("\n".join(master_lines), encoding="utf-8")

print("✅ DONE")
print(f"Saved OCR text: {ocr_total_path}")
