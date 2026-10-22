import psycopg2
from sentence_transformers import SentenceTransformer

# 1. Conexión a la base de datos
conn = psycopg2.connect(
    host="localhost", port=5433,
    dbname="docs", user="postgres", password="postgres"
)
cur = conn.cursor()
cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
conn.commit()
cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
print("pgvector versión:", cur.fetchone()[0])
conn.close()

# 2. Descarga y prueba del modelo de embeddings
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
vec = model.encode("Hola, esto es una prueba")
print("Dimensiones del embedding:", len(vec))