import sys

from pgvector.psycopg2 import register_vector

from db import get_connection
from embeddings import embed_query

MIN_SIMILARITY = 0.3

def search(query, k=5):
    vec = embed_query(query)
    conn = get_connection()
    register_vector(conn)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.filename, c.metadata, c.content,
               1 - (c.embedding <=> %s) AS similarity
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        ORDER BY c.embedding <=> %s
        LIMIT %s
        """,
        (vec, vec, k),
    )
    rows = cur.fetchall()
    conn.close()
    return [r for r in rows if r[3] >= MIN_SIMILARITY]


def show(results):
    if not results:
        print("\nNo hay similitudes con al consulta en la base de datos.\n")
        return

    for i, (filename, meta, content, sim) in enumerate(results, start=1):
        p0, p1 = meta.get("page_start"), meta.get("page_end")
        pages = f"p. {p0}" if p0 == p1 else f"pp. {p0}-{p1}"
        print(f"\n#{i} | similitud {sim:.3f} | {filename} ({pages})")
        print("-" * 60)
        print(content)
    print()


if __name__ == "__main__":
    k = 5

    # Con argumento: una sola consulta. Sin argumento: modo interactivo.
    if len(sys.argv) > 1:
        show(search(" ".join(sys.argv[1:]), k))
    else:
        print("Escribe tu pregunta (o 'salir' para terminar)")
        while True:
            q = input("\n> ").strip()
            if q.lower() in ("salir", "exit", "q"):
                break
            if q:
                show(search(q, k))