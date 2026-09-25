import sys
from pathlib import Path

from pypdf import PdfReader

from app.database import SessionLocal
from app.embeddings import create_embeddings
from app.models import DocumentChunk


CHUNK_SIZE_WORDS = 180
CHUNK_OVERLAP_WORDS = 30


def extract_text(file_path: Path) -> str:

    extension = file_path.suffix.lower()

    if extension == ".txt":

        text = file_path.read_text(
            encoding="utf-8"
        )

    elif extension == ".pdf":

        reader = PdfReader(str(file_path))

        pages = []

        for page in reader.pages:

            page_text = page.extract_text() or ""

            pages.append(page_text)

        text = "\n".join(pages)

    else:

        raise ValueError(
            "Only PDF and TXT files are currently supported."
        )

    if not text.strip():

        raise ValueError(
            "No readable text was found in the document."
        )

    return text


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_WORDS,
    overlap: int = CHUNK_OVERLAP_WORDS
) -> list[str]:

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = min(
            start + chunk_size,
            len(words)
        )

        chunk = " ".join(
            words[start:end]
        ).strip()

        if chunk:
            chunks.append(chunk)

        if end == len(words):
            break

        start = end - overlap

    return chunks


def ingest_document(file_path: str):

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    print(f"Reading: {path.name}")

    text = extract_text(path)

    chunks = chunk_text(text)

    print(
        f"Created {len(chunks)} chunks."
    )

    embeddings = create_embeddings(chunks)

    db = SessionLocal()

    try:

        # Remove old version if this document
        # has already been ingested.
        db.query(DocumentChunk).filter(
            DocumentChunk.document_name == path.name
        ).delete()

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):

            record = DocumentChunk(
                document_name=path.name,
                chunk_index=index,
                content=chunk,
                embedding=embedding
            )

            db.add(record)

        db.commit()

        print(
            f"Successfully stored "
            f"{len(chunks)} chunks."
        )
        return len(chunks)

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage: python -m app.document_ingestion "
            "<file_path>"
        )

        sys.exit(1)

    ingest_document(
        sys.argv[1]
    )