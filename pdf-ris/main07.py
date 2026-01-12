from pdf2image import convert_from_path
from pathlib import Path
import pytesseract
import cv2
import pandas as pd
import numpy as np
import re

# ----------------------------
# INPUT PDF
# ----------------------------
pdf_path = Path(r"E:\XRZONE_Files\PDFReader\PDFReader\pdf-ris\samples\v6\Jitta Collectie Wat ons blijvend boeit.pdf")
base_name = pdf_path.stem
output_dir = pdf_path.parent
ocr_total_path = output_dir / f"{base_name}_total.txt"
blocks_path = output_dir / f"{base_name}_blocks.txt"

# ----------------------------
# OCR SETTINGS
# ----------------------------
OCR_DPI = 300
TESSERACT_CONFIG = "--oem 3 --psm 12"
POPPLER_PATH = r"E:\XRZONE_Files\PDFReader\PDFReader\pdf-ris\poppler-25.11.0\Library\bin"

# ----------------------------
# PAGE RANGE
# ----------------------------
first_page = 14
last_page = 341

# ----------------------------
# OCR OR LOAD EXISTING TEXT
# ----------------------------
if ocr_total_path.exists():
    print(f"📄 OCR text exists. Loading: {ocr_total_path}")
    ocr_text = ocr_total_path.read_text(encoding="utf-8")

else:
    print(f"🔍 Converting PDF pages {first_page} to {last_page} to images...")

    if POPPLER_PATH:
        pages = convert_from_path(
            str(pdf_path),
            OCR_DPI,
            poppler_path=POPPLER_PATH,
            first_page=first_page,
            last_page=last_page
        )
    else:
        pages = convert_from_path(
            str(pdf_path),
            OCR_DPI,
            first_page=first_page,
            last_page=last_page
        )

    master_lines = []

    print("🔠 Running Tesseract OCR...")
    for i, page in enumerate(pages, start=first_page):
        gray = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        data = pytesseract.image_to_data(
            thresh,
            config=TESSERACT_CONFIG,
            output_type="dict"
        )

        df = pd.DataFrame(data)
        df = df[df["conf"].astype(float) > 0]

        page_dict = {}
        for _, row in df.iterrows():
            key = f"{i}_{row['par_num']}_{row['line_num']}"
            text = str(row["text"]).strip()
            if not text:
                continue
            page_dict.setdefault(key, "")
            page_dict[key] += (" " if page_dict[key] else "") + text

        for key in sorted(page_dict.keys()):
            master_lines.append(page_dict[key])

    ocr_text = " ".join(master_lines)
    ocr_total_path.write_text(ocr_text, encoding="utf-8")
    print(f"✅ OCR done. Saved to: {ocr_total_path}")

# ----------------------------
# TITLE EXTRACTION
# ----------------------------
def extract_title(block_text, threshold=0.7):
    words = block_text.split()
    title_words = []

    for w in words:
        # Keep only letters for ratio check
        letters = re.findall(r'[A-Za-z]', w)
        if not letters:
            break  # stop if word has no letters

        # Count uppercase letters
        upper_count = sum(1 for c in letters if c.isupper())
        ratio = upper_count / len(letters)

        if ratio >= threshold:
            title_words.append(w)
        else:
            break

    return " ".join(title_words).strip()


# ----------------------------
# BLOCK DETECTION
# ----------------------------
code_pattern = re.compile(r"(83\d{2}\s?[A-Za-z]{1,2}\s?\d{2}(?:-\d{2})?|Leeszaal)")
matches = list(code_pattern.finditer(ocr_text))
blocks = []

for i, match in enumerate(matches):
    code = match.group()

    # Block text
    start_idx = match.end()
    end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(ocr_text)
    block_text = ocr_text[start_idx:end_idx].strip()

    # Find author: last uppercase sequence before code
    before_code = ocr_text[:match.start()].rstrip()
    author_match = re.findall(r'([A-Z ,.\-\'*]+)[\.\*]?$', before_code)
    author = author_match[-1].strip() if author_match else ""

    # --- AUTHOR CORRECTION ---
    author = re.sub(r'^[^A-Z]+', '', author)
    author = re.sub(r'[.\*]+$', '', author)

    # --- SUBTRACT AUTHOR FROM PREVIOUS BLOCK ---
    if i > 0 and author:
        prev_block = blocks[-1]
        # Regex removes trailing whitespace/punctuation plus the author
        pattern = re.escape(author) + r'[\s\.\*]*$'
        prev_block["text"] = re.sub(pattern, '', prev_block["text"]).rstrip()

    # Extract title
    title = extract_title(block_text)

    # --- REMOVE TITLE FROM START OF BLOCK TEXT ---
    if title:
        title_pattern = re.escape(title) + r'[\s\.\*]*'
        block_text = re.sub(r'^' + title_pattern, '', block_text, count=1).strip()

    # Append current block
    blocks.append({
        "code": code,
        "author": author,
        "title": title,
        "text": block_text
    })

# ----------------------------
# WRITE BLOCKS TO FILE
# ----------------------------
with blocks_path.open("w", encoding="utf-8") as f:
    for block in blocks:
        f.write(
            f"{block['code']}\n"
            f"{block['author']}\n"
            f"{block['title']}\n"
            f"{block['text']}\n\n"
        )

print(f"📦 Generated {len(blocks)} blocks")
print(f"📄 Blocks saved to: {blocks_path}")

# ----------------------------
# WRITE CSV FILE
# ----------------------------
csv_path = output_dir / f"{base_name}_blocks.csv"

# Convert blocks list of dicts to DataFrame
df_blocks = pd.DataFrame(blocks, columns=["code", "author", "title", "text"])
df_blocks.to_csv(csv_path, index=False, encoding="utf-8")

print(f"📊 CSV saved: {csv_path}")
