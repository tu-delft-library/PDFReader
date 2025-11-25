from pdf2image import convert_from_path
from pathlib import Path
import pytesseract
import cv2
import pandas as pd
import numpy as np

# ----------------------------
# INPUT PDF
# ----------------------------
pdf_path = Path(r"E:\XRZONE_Files\PDFReader\PDFReader\pdf-ris\samples\v3\Jitta Collectie Wat ons blijvend boeit.pdf")
base_name = pdf_path.stem
output_dir = pdf_path.parent
ocr_total_path = output_dir / f"{base_name}_total.txt"

# ----------------------------
# OCR SETTINGS
# ----------------------------
OCR_DPI = 300
TESSERACT_CONFIG = "--oem 3 --psm 12"

POPPLER_PATH = r"E:\XRZONE_Files\PDFReader\PDFReader\pdf-ris\poppler-25.11.0\Library\bin"

# ----------------------------
# PAGE RANGE
# ----------------------------
first_page = 22   # the first page you want to process
last_page = 23    # the last page you want to process

print(f"🔍 Converting PDF pages {first_page} to {last_page} to images...")
if POPPLER_PATH:
    pages = convert_from_path(str(pdf_path), OCR_DPI, poppler_path=POPPLER_PATH,
                              first_page=first_page, last_page=last_page)
else:
    pages = convert_from_path(str(pdf_path), OCR_DPI,
                              first_page=first_page, last_page=last_page)

master_lines = []

print("🔠 Running Tesseract OCR...")
for i, page in enumerate(pages, start=first_page):
    gray = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    data = pytesseract.image_to_data(thresh, config=TESSERACT_CONFIG, output_type="dict")
    
    df = pd.DataFrame(data)
    df = df[df["conf"].astype(float) > 0]

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

    for key in sorted(page_dict.keys()):
        master_lines.append(page_dict[key])

ocr_total_path.write_text("\n".join(master_lines), encoding="utf-8")
print(f"✅ OCR done. Saved to: {ocr_total_path}")