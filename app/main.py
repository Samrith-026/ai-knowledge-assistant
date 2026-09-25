import logging
import time
import shutil
from pathlib import Path

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile
)
from fastapi.responses import JSONResponse

from app.document_ingestion import ingest_document
from app.schemas import (
    AskRequest,
    AskResponse,
    UploadResponse
)

from app.exceptions import RAGServiceError
from app.logging_config import setup_logging
from app.rag import answer_question


setup_logging()

logger = logging.getLogger(__name__)

from app.cache import (
    cache_answer,
    get_cached_answer
)

from app.rate_limit import is_rate_limited


app = FastAPI(
    title="AI Knowledge Assistant",
    version="1.0.0"
)


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next
):

    start_time = time.perf_counter()

    logger.info(
        "Request started: %s %s",
        request.method,
        request.url.path
    )

    response = await call_next(request)

    duration_ms = (
        time.perf_counter() - start_time
    ) * 1000

    logger.info(
        "Request completed: %s %s "
        "status=%d duration=%.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms
    )

    return response


@app.exception_handler(RAGServiceError)
async def rag_error_handler(
    request: Request,
    exc: RAGServiceError
):

    logger.error(
        "RAG service error on %s",
        request.url.path
    )

    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "The AI service is temporarily "
                "unavailable."
            )
        }
    )


@app.get("/")
def root():

    return {
        "message":
        "AI Knowledge Assistant is running"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.post(
    "/ask",
    response_model=AskResponse
)
def ask_question(
    request_body: AskRequest,
    request: Request
):

    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    if is_rate_limited(client_ip):

        raise HTTPException(
            status_code=429,
            detail=(
                "Too many requests. "
                "Please try again later."
            )
        )

    cached_result = get_cached_answer(
        request_body.question
    )

    if cached_result:

        return AskResponse(
            answer=cached_result["answer"],
            sources=cached_result["sources"]
        )

    result = answer_question(
        request_body.question
    )

    cache_answer(
        request_body.question,
        result
    )

    return AskResponse(
        answer=result["answer"],
        sources=result["sources"]
    )
DATA_DIRECTORY = Path("data")
DATA_DIRECTORY.mkdir(exist_ok=True)


@app.post(
    "/documents/upload",
    response_model=UploadResponse
)
def upload_document(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required."
        )

    safe_filename = Path(file.filename).name

    extension = Path(
        safe_filename
    ).suffix.lower()

    if extension not in {
        ".pdf",
        ".txt"
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF and TXT files "
                "are supported."
            )
        )

    destination = (
        DATA_DIRECTORY
        / safe_filename
    )

    try:

        with destination.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        chunks_created = ingest_document(
            str(destination)
        )

        return UploadResponse(
            filename=safe_filename,
            chunks_created=chunks_created,
            message=(
                "Document uploaded and "
                "indexed successfully."
            )
        )

    except Exception:

        logger.exception(
            "Document upload failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to process "
                "the document."
            )
        )

    finally:

        file.file.close()
