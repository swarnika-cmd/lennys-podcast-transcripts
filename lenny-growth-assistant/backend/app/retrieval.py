from sqlalchemy.orm import Session
from app import models, llm
from typing import List, Tuple

def retrieve_similar_chunks(
    db: Session,
    query: str,
    limit: int = 5,
    provider: str = "ollama"
) -> List[Tuple[models.TranscriptChunk, float]]:
    try:
        # Get embedding for the query
        query_embedding = llm.get_embeddings(query, provider=provider)
    except Exception as e:
        print(f"[RETRIEVAL ERROR] Failed to generate query embedding: {e}")
        return []
    
    # Calculate cosine distance
    cosine_distance = models.TranscriptChunk.embedding.cosine_distance(query_embedding)
    
    # Run the query
    results = db.query(
        models.TranscriptChunk,
        (1.0 - cosine_distance).label("similarity")
    ).order_by(cosine_distance).limit(limit).all()
    
    return [(chunk, float(score)) for chunk, score in results]
