from sentence_transformers import SentenceTransformer, util
_embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def cosine_similarity_score(reference: str, generated: str) -> float:
    """Calcula similitud de coseno entre dos respuestas."""
    emb_ref = _embedding_model.encode(reference, convert_to_tensor=True)
    emb_gen = _embedding_model.encode(generated, convert_to_tensor=True)
    score = util.cos_sim(emb_ref, emb_gen)
    return float(score.item())  # valor entre -1 y 1