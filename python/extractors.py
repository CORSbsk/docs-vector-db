import os
import pymupdf

def extract_pdf(path):
    records = []
    with pymupdf.open(path) as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            if text:
                records.append({"text": text, "metadata": {"page": i}})
    return records


def extract(path):
    ext = os.path.splitext(path)[1].lower()
    if ext != ".pdf":
        raise ValueError(f"Por ahora solo se soportan PDFs, recibí: {ext}")
    return extract_pdf(path)