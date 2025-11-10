import fitz  # PyMuPDF
import re
from pathlib import Path

# === File setup ===
pdf_path = Path(r"E:\XRZONE_Files\PDFReader\PDFReader\pdf-ris\samples\v1\Jitta Collectie Wat ons blijvend boeit.pdf")
output_path = pdf_path.with_name("blocks_codes_clean_total.txt")

# === Regex for codes ===
code_pattern = re.compile(r"\b(83\d{2}\s?[A-Z]\s?\d{2}(?:-\d{2})?|Leeszaal)\b")

# === Page range setup ===
start_page = 15  # 0-indexed
end_page = 336    # inclusive

# === Open PDF ===
doc = fitz.open(pdf_path)

all_results = []

for page_num in range(start_page, end_page + 1):
    page = doc.load_page(page_num)

    # === Extract blocks with positions ===
    raw_blocks = page.get_text("blocks")
    raw_blocks.sort(key=lambda b: (b[1], b[0]))

    # === Group blocks by vertical proximity ===
    grouped_blocks = []
    threshold = 2  # vertical distance in points , 5 default
    current_group = []
    last_y1 = None

    for b in raw_blocks:
        text = b[4].strip()
        if not text:
            continue
        y0, y1 = b[1], b[3]

        if last_y1 is None or (y0 - last_y1) > threshold:
            if current_group:
                grouped_blocks.append(" ".join(current_group))
            current_group = [text]
        else:
            current_group.append(text)

        last_y1 = y1

    if current_group:
        grouped_blocks.append(" ".join(current_group))

    # === Process grouped blocks with code logic ===
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

    if pending_codes and results:
        results[-1] += "\n" + "\n".join(pending_codes)

    # --- Collect results from this page ---
    all_results.extend(results)

# === Save final output ===
output_text = "\n\n".join(all_results)
output_path.write_text(output_text, encoding="utf-8")

print(f"✅ Clean blocks with codes saved to: {output_path}")
print("\n=== Preview ===\n")
print(output_text[:600])

doc.close()
