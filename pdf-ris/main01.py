import fitz  # PyMuPDF
import re
from pathlib import Path

# === File setup ===
pdf_path = Path(r"E:\XRZONE_Files\PDFReader\pdf-ris\samples\v1\Jitta Collectie Wat ons blijvend boeit.pdf")
output_path = pdf_path.with_name("page21_blocks_codes_clean.txt")

# === Regex for codes ===
code_pattern = re.compile(r"\b(83\d{2}\s?[A-Z]\s?\d{2}(?:-\d{2})?|Leeszaal)\b")

# === Open PDF and read page ===
doc = fitz.open(pdf_path)
page = doc.load_page(20)  #  (n-1)

# === Extract blocks with positions ===
raw_blocks = page.get_text("blocks")  # each block: (x0, y0, x1, y1, text, ...)
# Sort by vertical position then horizontal position
raw_blocks.sort(key=lambda b: (b[1], b[0]))

# === Group blocks by vertical proximity ===
grouped_blocks = []
threshold = 5  # vertical distance in points; tweak if needed
current_group = []
last_y1 = None

for b in raw_blocks:
    text = b[4].strip()
    if not text:
        continue
    y0, y1 = b[1], b[3]

    if last_y1 is None or (y0 - last_y1) > threshold:
        # start new group
        if current_group:
            grouped_blocks.append(" ".join(current_group))
        current_group = [text]
    else:
        # continue current group
        current_group.append(text)

    last_y1 = y1

# append the last group
if current_group:
    grouped_blocks.append(" ".join(current_group))

# === Process grouped blocks with your existing code logic ===
results = []
pending_codes = []

for text in grouped_blocks:
    text = text.strip()

    # --- Inline codes inside a block ---
    inline_codes = code_pattern.findall(text)
    if inline_codes and not code_pattern.fullmatch(text):
        clean_text = re.sub(r"\s*\b(83\d{2}\s?[A-Z]\s?\d{2}(?:-\d{2})?|Leeszaal)\b\s*", "", text).strip()
        all_codes = pending_codes + inline_codes
        pending_codes = []
        if clean_text:
            results.append(clean_text + "\n" + "\n".join(all_codes))
        else:
            results.append("\n".join(all_codes))
        continue

    # --- Code-only block ---
    if code_pattern.fullmatch(text):
        pending_codes.append(text)
        continue

    # --- Regular text block ---
    if pending_codes:
        text = text + "\n" + "\n".join(pending_codes)
        pending_codes = []
    results.append(text)

# --- Any remaining codes at the end ---
if pending_codes and results:
    results[-1] += "\n" + "\n".join(pending_codes)

# === Save final output ===
output_text = "\n\n".join(results)
output_path.write_text(output_text, encoding="utf-8")

print(f"✅ Clean blocks with codes saved to: {output_path}")
print("\n=== Preview ===\n")
print(output_text[:600])

doc.close()

