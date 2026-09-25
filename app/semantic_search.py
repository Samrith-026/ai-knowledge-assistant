import os

from dotenv import load_dotenv
from sqlalchemy import select

from app.database import SessionLocal
from app.models import DocumentChunk
from app.embeddings import create_embedding


load_dotenv()

MAX_COSINE_DISTANCE = float(
    os.getenv("MAX_COSINE_DISTANCE", "0.50")
)


def semantic_search(
    query: str,
    limit: int = 5,
    max_distance: float = MAX_COSINE_DISTANCE
):

    query_embedding = create_embedding(query)

    db = SessionLocal()

    try:
        distance = DocumentChunk.embedding.cosine_distance(
            query_embedding
        ).label("distance")

        statement = (
            select(DocumentChunk, distance)
            .order_by(distance)
            .limit(limit)
        )

        results = db.execute(statement).all()

        filtered_results = [
            (chunk, score)
            for chunk, score in results
            if float(score) <= max_distance
        ]

        return filtered_results

    finally:
        db.close()


if __name__ == "__main__":

    query = "How much vacation time do employees get?"

    print(f"\nQuestion: {query}\n")

    results = semantic_search(query)

    if not results:
        print("No sufficiently relevant results found.")

    for chunk, distance in results:
        print(f"Content: {chunk.content}")
        print(f"Distance: {distance:.4f}")
        print("-" * 60)