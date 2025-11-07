import fitz  # PyMuPDF
import re
from pathlib import Path

# Folder setup
samples_folder = Path(r"E:\XRZONE_Files\PDFReader\pdf-ris\samples\v0")
output_total = samples_folder / "output_total.ris"

# Collect all RIS entries
all_ris_entries = []

def detect_ris_type(text):
    if re.search(r'Proceedings of|Conference', text, re.IGNORECASE):
        return "CONF"
    elif re.search(r'Journal', text, re.IGNORECASE):
        return "JOUR"
    elif re.search(r'Thesis|Dissertation', text, re.IGNORECASE):
        return "THES"
    elif re.search(r'Book|Publisher', text, re.IGNORECASE):
        return "BOOK"
    else:
        return "GEN"

for pdf_file in samples_folder.glob("*.pdf"):
    print(f"Processing: {pdf_file.name}")

    try:
        doc = fitz.open(pdf_file)
        full_text = "\n".join(page.get_text() for page in doc)
        doc.close()

        # RIS Type
        ris_type = detect_ris_type(full_text)

        # DOI
        doi_match = re.search(r'(10\.\d{4,9}/[^\s]+)', full_text)
        doi = f"https://doi.org/{doi_match.group(1)}" if doi_match else ""

        # Title (largest uppercase line or first long line)
        lines = full_text.splitlines()
        title_candidates = [line.strip() for line in lines if line.strip() and line.strip().isupper()]
        if title_candidates:
            title = max(title_candidates, key=len).title()
        else:
            title = max(lines[:20], key=len).strip().title() if lines else "Untitled"

        # Authors (lines after title)
        authors = []
        try:
            title_index = lines.index(title.upper())
        except ValueError:
            title_index = 0
        for line in lines[title_index+1:title_index+10]:
            line = line.strip()
            if not line or re.search(r'\d|@', line):
                continue
            if any(c.isalpha() for c in line):
                authors.append(line.replace(',', '').strip())

        # Abstract
        abstract_match = re.search(r'Abstract\s*([\s\S]*?)(?=\n\s*Key\s*words|\n\d|\Z)', full_text, re.IGNORECASE)
        abstract = abstract_match.group(1).strip() if abstract_match else ""

        # Keywords
        kw_match = re.search(r'Key\s*words?\s*[:\-]?\s*(.*)', full_text, re.IGNORECASE)
        keywords = [kw.strip() for kw in re.split(r'[;,]', kw_match.group(1))] if kw_match else []

        # Venue
        venue_match = re.search(r'(Proceedings of[^\n]+|Conference[^\n]+|Journal[^\n]+)', full_text, re.IGNORECASE)
        venue = venue_match.group(1).strip() if venue_match else ""

        # Publisher
        pub_match = re.search(r'Published by\s*([^\n]+)', full_text, re.IGNORECASE)
        publisher = pub_match.group(1).strip() if pub_match else ""

        # Year
        year_match = re.search(r'\b(20\d{2})\b', full_text)
        year = year_match.group(1) if year_match else "2024"

        # Build RIS entry
        ris = f"TY  - {ris_type}\n"
        ris += f"T1  - {title}\n"
        for au in authors:
            ris += f"AU  - {au}\n"
        ris += f"PY  - {year}\nY1  - {year}\n"
        if abstract:
            ris += f"AB  - {abstract}\nN2  - {abstract}\n"
        for kw in keywords:
            ris += f"KW  - {kw}\n"
        if doi:
            ris += f"U2  - {doi}\nDO  - {doi}\n"
        if venue:
            ris += f"T2  - {venue}\n"
        if publisher:
            ris += f"PB  - {publisher}\n"
        ris += "ER  -\n"

        all_ris_entries.append(ris)
        print(f"✅ Processed: {pdf_file.name}")

    except Exception as e:
        print(f"❌ Error processing {pdf_file.name}: {e}")

# Join all entries with exactly two newlines between them
combined_ris = "\n\n".join(entry.strip() for entry in all_ris_entries)

# Write to output file
output_total.write_text(combined_ris + "\n", encoding="utf-8")

print(f"\n🎉 All RIS entries saved to: {output_total}")
