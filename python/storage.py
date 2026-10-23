import shutil
from pathlib import Path

import fitz  # PyMuPDF

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
PDF_DIR = STORAGE_DIR / "pdfs"
CACHE_DIR = STORAGE_DIR / "cache"


def pdf_path(file_hash):
    return PDF_DIR / f"{file_hash}.pdf"


def save_pdf(src, file_hash):
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    dest = pdf_path(file_hash)
    if not dest.exists():
        shutil.copyfile(src, dest)
    return dest


def delete_files(file_hash):
    pdf_path(file_hash).unlink(missing_ok=True)
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob(f"{file_hash}_*.png"):
            f.unlink(missing_ok=True)


def page_count(file_hash):
    with fitz.open(pdf_path(file_hash)) as doc:
        return doc.page_count


def render_page(file_hash, page, width):
    """Renderiza una página como PNG del ancho pedido, con caché en disco."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out = CACHE_DIR / f"{file_hash}_p{page}_w{width}.png"
    if out.exists():
        return out
    with fitz.open(pdf_path(file_hash)) as doc:
        p = doc[page - 1]
        zoom = width / p.rect.width
        pix = p.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        pix.save(str(out))
    return out