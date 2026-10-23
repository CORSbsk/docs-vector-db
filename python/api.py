import os
import shutil
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from db import get_connection
from embeddings import get_model
from ingest import ingest
from search import search
from storage import delete_files, page_count, pdf_path, render_page


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_model()  # carga el modelo al arrancar, no en la primera petición
    yield


app = FastAPI(title="docs-vector-db", lifespan=lifespan)


# ---------- Búsqueda ----------

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    k: int = Field(default=5, ge=1, le=20)
    min_similarity: float = Field(default=0.3, ge=0, le=1)


@app.post("/api/search")
def api_search(req: SearchRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(400, "La pregunta está vacía")

    results = []
    for doc_id, filename, meta, content, sim in search(query, req.k):
        if sim < req.min_similarity:
            continue
        results.append({
            "document_id": doc_id,
            "filename": filename,
            "page_start": meta.get("page_start"),
            "page_end": meta.get("page_end"),
            "similarity": round(float(sim), 3),
            "content": content,
        })
    return {"query": query, "results": results}


# ---------- Documentos ----------

@app.get("/api/documents")
def list_documents():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT d.id, d.filename, d.file_type, d.uploaded_at, COUNT(c.id)
            FROM documents d
            LEFT JOIN chunks c ON c.document_id = d.id
            GROUP BY d.id
            ORDER BY d.uploaded_at DESC
            """
        )
        return [
            {
                "id": id_,
                "filename": filename,
                "file_type": file_type,
                "uploaded_at": uploaded_at.isoformat(),
                "chunks": n_chunks,
            }
            for id_, filename, file_type, uploaded_at, n_chunks in cur.fetchall()
        ]
    finally:
        conn.close()


@app.post("/api/upload")
def upload(file: UploadFile):
    filename = os.path.basename(file.filename or "")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo se aceptan archivos PDF")

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        try:
            return ingest(path)
        except Exception as e:
            raise HTTPException(500, f"No se pudo procesar el archivo: {e}")


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM documents WHERE id = %s RETURNING filename, file_hash",
            (doc_id,),
        )
        row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(404, "Documento no encontrado")
    delete_files(row[1])
    return {"deleted": row[0]}


# ---------- Vista previa de documentos ----------

def get_file_hash(doc_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT file_hash FROM documents WHERE id = %s", (doc_id,))
        row = cur.fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(404, "Documento no encontrado")
    if not pdf_path(row[0]).exists():
        raise HTTPException(
            404, "El archivo original no está guardado. Elimina el documento y vuelve a subirlo."
        )
    return row[0]


@app.get("/api/documents/{doc_id}/page/{page}")
def document_page(doc_id: int, page: int, width: int = Query(400, ge=100, le=1200)):
    file_hash = get_file_hash(doc_id)
    if not 1 <= page <= page_count(file_hash):
        raise HTTPException(404, "Esa página no existe")
    return FileResponse(
        render_page(file_hash, page, width),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/api/documents/{doc_id}/file")
def document_file(doc_id: int):
    return FileResponse(pdf_path(get_file_hash(doc_id)), media_type="application/pdf")


# ---------- Frontend ----------

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")