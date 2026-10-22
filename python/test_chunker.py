import sys
from extractors import extract
from chunker import chunk_pages

path = sys.argv[1]
size = int(sys.argv[2]) if len(sys.argv) > 2 else 800

records = extract(path)
chunks = chunk_pages(records, size=size)

lengths = [len(c["content"]) for c in chunks]
print(f"Páginas con texto: {len(records)}")
print(f"Caracteres totales: {sum(len(r['text']) for r in records)}")
print(f"Chunks generados: {len(chunks)}")
print(f"Longitud min/prom/max: {min(lengths)} / {sum(lengths)//len(lengths)} / {max(lengths)}\n")

for i, c in enumerate(chunks[:3]):
    print(f"--- Chunk {i} | {c['metadata']} | {len(c['content'])} caracteres ---")
    print(c["content"])
    print()