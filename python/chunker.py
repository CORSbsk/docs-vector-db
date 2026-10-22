def chunk_pages(records, size=800, overlap=100):
    """
    Une el texto de todas las páginas y lo divide en fragmentos de ~size caracteres,
    con traslape, cortando preferentemente en párrafo, fin de oración o salto de línea.
    Cada fragmento guarda en qué páginas empieza y termina.
    """
    full = ""
    spans = []  # (inicio, fin, página)
    for r in records:
        start = len(full)
        full += r["text"] + "\n\n"
        spans.append((start, len(full), r["metadata"]["page"]))

    def pages_for(a, b):
        pages = [p for s, e, p in spans if s < b and e > a]
        return pages[0], pages[-1]

    # Puntos de corte en orden de preferencia (de mejor a peor)
    separators = ["\n\n", ".\n", ". ", "\n", " "]

    chunks = []
    n = len(full)
    start = 0
    while start < n:
        end = min(start + size, n)

        if end < n:
            window_start = start + int(size * 0.5)
            for sep in separators:
                idx = full.rfind(sep, window_start, end)
                if idx != -1:
                    end = idx + len(sep)
                    break

        text = full[start:end].strip()
        if text:
            p0, p1 = pages_for(start, end)
            chunks.append({
                "content": text,
                "metadata": {"page_start": p0, "page_end": p1},
            })

        if end >= n:
            break

        # Retroceder para crear el traslape, sin empezar a media palabra
        new_start = max(end - overlap, start + 1)
        while new_start < end and not full[new_start - 1].isspace():
            new_start += 1
        start = new_start

    return chunks