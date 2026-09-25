from app.database import SessionLocal
from app.models import DocumentChunk
from app.embeddings import create_embedding


sample_chunks = [
    {
        "document_name": "employee_policy.txt",
        "chunk_index": 1,
        "content": "Employees may work remotely up to two days per week."
    },
    {
        "document_name": "employee_policy.txt",
        "chunk_index": 2,
        "content": "Employee health insurance coverage begins after 30 days of employment."
    },
    {
        "document_name": "employee_policy.txt",
        "chunk_index": 3,
        "content": "Employees receive a company laptop on their first day."
    }
]


db = SessionLocal()

try:
    for item in sample_chunks:

        existing = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_name == item["document_name"],
                DocumentChunk.chunk_index == item["chunk_index"]
            )
            .first()
        )

        if existing:
            print(
                f"Chunk {item['chunk_index']} already exists. Skipping."
            )
            continue

        embedding = create_embedding(item["content"])

        chunk = DocumentChunk(
            document_name=item["document_name"],
            chunk_index=item["chunk_index"],
            content=item["content"],
            embedding=embedding
        )

        db.add(chunk)

    db.commit()

    print("Sample document chunks saved successfully!")

finally:
    db.close()