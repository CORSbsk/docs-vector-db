import sys
from extractors import extract

path = sys.argv[1]
records = extract(path)
print(f"{len(records)} registros extraídos\n")
for r in records[:3]:
    print(r["metadata"])
    print(r["text"][:300])
    print("-" * 40)