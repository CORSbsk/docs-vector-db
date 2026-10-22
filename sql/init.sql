CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id          SERIAL PRIMARY KEY,
    filename    TEXT NOT NULL,
    file_type   TEXT,
    file_hash   TEXT UNIQUE,          -- para evitar subir el mismo archivo dos veces
    uploaded_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id          SERIAL PRIMARY KEY,
    document_id INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,         -- posición del fragmento dentro del documento
    content     TEXT NOT NULL,
    metadata    JSONB,                -- página, fila original, etc.
    embedding   vector(384)
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS chunks_document_idx
    ON chunks (document_id);