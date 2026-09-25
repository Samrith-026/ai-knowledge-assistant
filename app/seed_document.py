from app.database import SessionLocal
from app.models import DocumentChunk
from app.embeddings import create_embedding


text = "Employees receive 15 days of PTO each year."

embedding = create_embedding(text)

db = SessionLocal()

try:
    chunk = DocumentChunk(
        document_name="employee_policy.txt",
        chunk_index=0,
        content=text,
        embedding=embedding
    )

    db.add(chunk)
    db.commit()
    db.refresh(chunk)

    print(f"Document chunk saved with ID: {chunk.id}")

finally:
    db.close()