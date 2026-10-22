import hashlib
import os
import sys

from pgvector.psycopg2 import register_vector
from psycopg2.extras import Json, execute_values

from chunker import chunk_pages
from db import get_connection
from embeddings import embed_texts
from extractors import extract


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def ingest(path, chunk_size=500):
    filename = os.path.basename(path)
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    h = file_hash(path)

    conn = get_connection()
    register_vector(conn)
    cur = conn.cursor()
    try:
        # 1. ¿Ya existe este archivo?
        cur.execute("SELECT id FROM documents WHERE file_hash = %s", (h,))
        if cur.fetchone():
            print(f"[omitido] {filename} ya estaba en la base de datos")
            return

        # 2. Extraer y dividir
        records = extract(path)
        if not records:
            print(f"[omitido] {filename}: no se extrajo texto (PDF NO LEGIBLE)")
            return
        chunks = chunk_pages(records, size=chunk_size)

        # 3. Embeddings de todos los chunks en lote
        embeddings = embed_texts([c["content"] for c in chunks])

        # 4. Guardar documento y chunks en una sola transacción
        cur.execute(
            "INSERT INTO documents (filename, file_type, file_hash) "
            "VALUES (%s, %s, %s) RETURNING id",
            (filename, ext, h),
        )
        doc_id = cur.fetchone()[0]

        rows = [
            (doc_id, i, c["content"], Json(c["metadata"]), emb)
            for i, (c, emb) in enumerate(zip(chunks, embeddings))
        ]
        execute_values(
            cur,
            "INSERT INTO chunks (document_id, chunk_index, content, metadata, embedding) "
            "VALUES %s",
            rows,
        )
        conn.commit()
        print(f"[ok] {filename}: {len(chunks)} chunks guardados")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python python/ingest.py <archivo.pdf | carpeta> [chunk_size]")
        sys.exit(1)

    target = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 500

    if os.path.isdir(target):
        for name in sorted(os.listdir(target)):
            if name.lower().endswith(".pdf"):
                ingest(os.path.join(target, name), size)
    else:
        ingest(target, size)