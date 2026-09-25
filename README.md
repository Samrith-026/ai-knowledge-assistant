# AI Knowledge Assistant

[![CI](https://github.com/Samrith-026/ai-knowledge-assistant/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Samrith-026/ai-knowledge-assistant/actions/workflows/ci.yml)

A production-style retrieval-augmented generation (RAG) API for indexing PDF and TXT documents and answering questions with source references. The service combines FastAPI, OpenAI embeddings and responses, PostgreSQL with pgvector, and Redis-backed caching and rate limiting.

## Architecture

Question answering flow:

```mermaid
flowchart LR
    U[User] --> API[FastAPI]
    API --> RL[Redis rate limit]
    RL --> CACHE[Redis answer cache]
    CACHE -->|cache miss| EMB[OpenAI embedding]
    EMB --> DB[(PostgreSQL + pgvector)]
    DB --> RET[Cosine-distance retrieval]
    RET --> FILTER[Relevance threshold]
    FILTER --> LLM[OpenAI response model]
    LLM --> OUT[Answer + source chunks]
    CACHE -->|cache hit| OUT
```

Document ingestion flow:

```mermaid
flowchart LR
    FILE[PDF or TXT] --> EXT[Text extraction]
    EXT --> CHUNK[180-word chunks with 30-word overlap]
    CHUNK --> EMB[OpenAI embeddings in a batch]
    EMB --> STORE[(PostgreSQL + pgvector)]
```

## Features

- PDF and TXT upload at `POST /documents/upload`.
- PDF text extraction with pypdf and overlapping word-based chunking.
- Batched embeddings stored in a PostgreSQL `vector(1536)` column through pgvector.
- Cosine-distance semantic search with a configurable maximum distance.
- RAG answers instructed to use retrieved context only, with source references and the retrieved source chunks returned in the API response.
- Redis answer caching with a configurable TTL.
- Redis fixed-window request limiting for `/ask`; the current implementation fails open if Redis is unavailable.
- Structured request logging and a service-error response handler.
- A retrieval evaluation script and offline unit tests.
- Docker Compose for the API, PostgreSQL/pgvector, and Redis.
- GitHub Actions checks for Python compilation, offline tests, and Docker image builds.

## Technology stack

Python 3.10 · FastAPI · OpenAI Python SDK · PostgreSQL · pgvector · SQLAlchemy · Redis · pypdf · Docker Compose · GitHub Actions

## Requirements

- Python 3.10
- Docker Engine with the Docker Compose plugin (for the full stack)
- An OpenAI API key for document embedding and LLM-backed answers

## Run locally

1. Clone the repository and enter its folder.
2. Create and activate a virtual environment, then install the pinned dependencies:

   ```powershell
   py -3.10 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

   On macOS or Linux, use `python3.10 -m venv .venv` and `source .venv/bin/activate`.

3. Create your local environment file and add your own OpenAI key:

   ```powershell
   Copy-Item .env.example .env
   ```

   Set `OPENAI_API_KEY` in `.env`. Keep `.env` private; it is ignored by Git.

4. Start PostgreSQL/pgvector and Redis, then initialize the schema:

   ```powershell
   docker compose up -d postgres redis
   python -m app.init_db
   ```

5. Run the API:

   ```powershell
   uvicorn app.main:app --reload
   ```

   The API is at `http://localhost:8000`; interactive OpenAPI docs are at `http://localhost:8000/docs`.

## Environment variables

Copy `.env.example` to `.env` and change the placeholder API key. The example contains no real credentials.

| Variable | Purpose | Example/default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy PostgreSQL connection | `postgresql+psycopg://postgres:postgres@localhost:5432/knowledge_db` |
| `OPENAI_API_KEY` | OpenAI API authentication | Set locally; never commit it |
| `OPENAI_MODEL` | Responses API model | `gpt-4o-mini` |
| `MAX_COSINE_DISTANCE` | Maximum accepted cosine distance; smaller is more similar | `0.50` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `CACHE_TTL_SECONDS` | Answer-cache lifetime | `300` |
| `RATE_LIMIT_REQUESTS` | Maximum `/ask` requests per client/window | `10` |
| `RATE_LIMIT_WINDOW_SECONDS` | Fixed-window duration | `60` |

The sample database credentials are for local development only. Configure strong credentials and restrict network access before using this stack in a shared or production environment.

## Run the full stack with Docker Compose

Copy `.env.example` to `.env`, set `OPENAI_API_KEY`, then run:

```sh
docker compose up --build
```

Compose starts PostgreSQL/pgvector and Redis, waits for their health checks, initializes the database schema, and starts the API on port 8000. The API container uses the Compose service names for its database and Redis connections. Stop the stack with `docker compose down`; named PostgreSQL data remains in the `postgres_data` volume. To remove that local database volume too, use `docker compose down -v`.

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Basic service message |
| `GET` | `/health` | Lightweight process health response |
| `POST` | `/documents/upload` | Upload and index one `.pdf` or `.txt` document |
| `POST` | `/ask` | Retrieve relevant chunks and generate an answer |
| `GET` | `/docs` | Interactive Swagger UI provided by FastAPI |

`/health` reports that the process is responding; it does not check PostgreSQL, Redis, or OpenAI connectivity.

## Example upload and ask workflow

Upload the included fictional sample document (it contains no real company or employee information):

```sh
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@./examples/demo_handbook.txt"
```

Ask a question:

```sh
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"How many paid time-off days do full-time team members receive?"}'
```

The upload response includes the filename and number of indexed chunks. The ask response contains an answer plus source records with document name, chunk index, content, and cosine distance. If no retrieved chunk passes the configured relevance threshold, the service returns an insufficient-context answer instead of calling the response model.

## Retrieval evaluation

`app/evaluate.py` runs a small, predefined retrieval evaluation and reports expected-document/chunk matches and retrieval latency. It queries the existing database and uses the embeddings API, so it is not a standalone offline test: initialize and populate the database with the expected evaluation documents first, and set a valid OpenAI key. The evaluation script currently prints its results; it does not set a CI pass/fail exit status. CI intentionally does not run it or call OpenAI.

## Caching and rate limiting

`/ask` checks a Redis fixed-window counter before checking its response cache. Cached answers use a normalized question hash as the Redis key and expire after `CACHE_TTL_SECONDS`. Redis errors are logged: cache errors fall through to normal processing, and rate-limit errors fail open so Redis downtime does not block the API. This availability-oriented behavior means the rate limit is not enforced while Redis is unavailable.

## CI

The workflow in `.github/workflows/ci.yml` runs on pushes to `main` and pull requests. It sets up Python 3.10, installs `requirements.txt`, compiles the application and tests, runs offline `unittest` checks, and builds the Docker image. These checks need no OpenAI API key and do not make external AI API calls.

Run the offline checks locally:

```sh
python -m compileall app tests
python -m unittest discover -s tests -v
```

## Project structure

```text
.
├── .github/workflows/ci.yml
├── app/
│   ├── cache.py
│   ├── database.py
│   ├── document_ingestion.py
│   ├── embeddings.py
│   ├── evaluate.py
│   ├── main.py
│   ├── models.py
│   ├── rag.py
│   ├── rate_limit.py
│   ├── schemas.py
│   └── semantic_search.py
├── tests/
├── .dockerignore
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

Local documents and the `data/` directory are intentionally excluded from version control. The application creates its runtime data directory when it starts.

## Security and secrets

- Never commit `.env`, API keys, passwords, tokens, private documents, or generated local data.
- `.env.example` contains placeholders only; `.gitignore` excludes local environment files except that template.
- The Docker build context excludes `.env` files, virtual environments, Git metadata, and local data.
- Rotate any credential immediately if it is accidentally exposed. Use your hosting platform’s secret manager for deployed environments.
