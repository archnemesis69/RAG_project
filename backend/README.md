# rag-backend

Spring Boot backend for the AI Research Assistant. Handles accounts (JWT
auth), file management (upload/list/delete), and proxies chat queries to
the FastAPI AI service. This is the "Serveur principal" box in section 3
of the cahier des charges.

## Prerequisites

- Java 17+
- Maven 3.9+
- PostgreSQL running locally (or via Docker)
- The FastAPI AI service running on `http://localhost:8000` (see the
  `rag/` Python project)

## Database setup

```sql
CREATE DATABASE rag_assistant;
CREATE USER rag_user WITH PASSWORD 'rag_password';
GRANT ALL PRIVILEGES ON DATABASE rag_assistant TO rag_user;
```

Tables (`users`, `documents`) are created automatically on startup via
`spring.jpa.hibernate.ddl-auto: update` — fine for the stage, but swap
for Flyway/Liquibase migrations before this goes anywhere near
production data.

## Configuration

`src/main/resources/application.yml` reads two env vars with sane
local defaults:

- `JWT_SECRET` — override in any real deployment; the default is a
  placeholder.
- `AI_SERVICE_URL` — defaults to `http://localhost:8000`.

## Running

```bash
mvn spring-boot:run
```

Starts on `http://localhost:8080`.

## API

All `/api/documents/**` and `/api/chat/**` routes require
`Authorization: Bearer <token>`. `/api/auth/**` is public.

| Method | Path | Body | Description |
|---|---|---|---|
| POST | `/api/auth/register` | `{email, password}` | Create an account, returns a JWT |
| POST | `/api/auth/login` | `{email, password}` | Returns a JWT |
| POST | `/api/documents` | multipart `file` | Upload + ingest a PDF/DOCX/TXT |
| GET | `/api/documents` | — | List the current user's documents |
| DELETE | `/api/documents/{id}` | — | Delete a document |
| POST | `/api/chat/query` | `{question, topK?}` | Ask a question, get an answer + sources |

### Example

```bash
# register
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'



curl -X POST http://localhost:8080/api/documents \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/doc.pdf"


curl -X POST http://localhost:8080/api/chat/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the reimbursement procedure?"}'
```

## Known limitation: documents aren't actually isolated per user yet

The FastAPI AI service uses a single shared Chroma vector store — there
is no per-user namespace or metadata filter on `owner` yet. Right now,
`documents` correctly tracks *which user uploaded what* in Postgres,
but `/api/chat/query` will retrieve from **every** ingested document
regardless of who uploaded it. For a single-user demo/stage this is
invisible, but if you test with two accounts, user B will get answers
sourced from user A's documents.

Fixing this properly means:
1. Tagging each chunk's metadata with the owner's user ID during
   ingestion (the AI service would need to accept a `user_id` param on
   `/documents` upload).
2. Filtering retrieval in `multi_query.py` with `where={"owner": user_id}`.

Flagging this now so it doesn't surprise you later — happy to implement
it whenever you're ready to tackle the AI service again.
