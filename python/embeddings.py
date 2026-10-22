from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts):
    return get_model().encode(
        texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True
    )


def embed_query(query):
    return get_model().encode(query, normalize_embeddings=True)