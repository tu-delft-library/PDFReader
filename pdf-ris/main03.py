import fitz  # PyMuPDF
import re
import csv
from pathlib import Path

# === File setup ===
pdf_path = Path(r"E:\XRZONE_Files\PDFReader\PDFReader\pdf-ris\samples\v2\Jitta Collectie Wat ons blijvend boeit.pdf")

# Output paths
base_name = pdf_path.stem
output_dir = pdf_path.parent
total_path = output_dir / f"{base_name}_blocks_total.txt"
correct_path = output_dir / f"{base_name}_blocks_correct.txt"
incorrect_path = output_dir / f"{base_name}_blocks_incorrect.txt"
categorized_path = output_dir / f"{base_name}_blocks_categorized.txt"
csv_path = output_dir / f"{base_name}_blocks_categorized.csv"

# === Regex for codes ===
code_pattern = re.compile(r"\b(83\d{2}\s?[A-Z]\s?\d{2}(?:-\d{2})?|Leeszaal)\b")

# === Helper function ===
def is_mostly_upper(line):
    letters = [c for c in line if c.isalpha()]
    if not letters:
        return False
    return sum(c.isupper() for c in letters) / len(letters) > 0.7

# === Page range setup ===
start_page = 15  # 0-indexed
end_page = 336   # inclusive

# === Open PDF ===
doc = fitz.open(pdf_path)
all_results = []

for page_num in range(start_page, end_page + 1):
    page = doc.load_page(page_num)
    raw_blocks = page.get_text("blocks")
    raw_blocks.sort(key=lambda b: (b[1], b[0]))  # sort top to bottom, left to right

    # === Group blocks by vertical proximity ===
    grouped_blocks = []
    threshold = 2  # vertical gap (in points)
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

    # === Process grouped blocks for code logic ===
    results = []
    pending_codes = []

    for text in grouped_blocks:
        text = text.strip()

        # --- Inline codes ---
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

    # Attach any leftover codes
    if pending_codes and results:
        results[-1] += "\n" + "\n".join(pending_codes)

    # Append page results
    all_results.extend(results)

doc.close()

# === Classify blocks ===
total_blocks = all_results
correct_blocks = []
incorrect_blocks = []

for block in total_blocks:
    lines = [ln for ln in block.splitlines() if ln.strip()]
    if len(lines) >= 3 and code_pattern.fullmatch(lines[-1].strip()):
        correct_blocks.append(block)
    else:
        incorrect_blocks.append(block)

# === Categorize correct blocks ===
categorized_output = []
csv_rows = []

for block in correct_blocks:
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    code = lines[-1]
    content = lines[:-1]

    # Determine author/title lines (first consecutive uppercase lines)
    author_title = []
    middle = []
    for line in content:
        if is_mostly_upper(line):
            author_title.append(line)
        else:
            middle.append(line)

    author_title_text = " ".join(author_title).strip()
    middle_text = " ".join(middle).strip()

    categorized_output.append(
        "=== AUTHOR_TITLE ===\n" + author_title_text +
        "\n\n=== MIDDLE ===\n" + middle_text +
        "\n\n=== CODE ===\n" + code + "\n\n" + "="*40 + "\n"
    )

    csv_rows.append([author_title_text, middle_text, code])

# === Save outputs ===
total_path.write_text("\n\n".join(total_blocks), encoding="utf-8")
correct_path.write_text("\n\n".join(correct_blocks), encoding="utf-8")
incorrect_path.write_text("\n\n".join(incorrect_blocks), encoding="utf-8")
categorized_path.write_text("\n".join(categorized_output), encoding="utf-8")

# === Write CSV ===
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Author_Title", "Middle", "Code"])
    writer.writerows(csv_rows)

# === Print summary ===
print(f"✅ Processed pages {start_page + 1}–{end_page + 1}")
print(f"Total blocks: {len(total_blocks)}")
print(f"Correct blocks: {len(correct_blocks)}")
print(f"Incorrect blocks: {len(incorrect_blocks)}")
print(f"\nSaved to:\n{total_path}\n{correct_path}\n{incorrect_path}\n{categorized_path}\n{csv_path}")
