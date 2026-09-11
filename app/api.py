from contextlib import asynccontextmanager
import logging
import time
import uuid
from pathlib import Path
import shutil

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from app.bm25_search import build_bm25
from app.database import get_connection
from app.hashing import hash_password, verify_password
from app.ingestion import ingest_file
from app.logging_config import configure_logging
from app.rag_pipeline import run_rag
from app.security import create_access_token, get_current_user_id


class UserRegister(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: str
    password: str


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10_000)


class AskResponse(BaseModel):
    answer: str


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_ROOT = PROJECT_ROOT / "data" / "documents"

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_startup")
    app.state.bm25_indexes = {}

    connection = get_connection()
    rows = connection.execute("SELECT id FROM users").fetchall()
    connection.close()

    for (user_id,) in rows:
        bm25, data = build_bm25(user_id)
        app.state.bm25_indexes[user_id] = (bm25, data)

    yield

    app.state.bm25_indexes.clear()
    logger.info("application_shutdown")


app = FastAPI(
    title="RAG API",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    adapter = logging.LoggerAdapter(logger, {"request_id": request_id})

    adapter.info("request_started method=%s path=%s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - started) * 1000
        adapter.exception("request_failed method=%s path=%s duration_ms=%.2f", request.method, request.url.path, elapsed_ms)
        raise

    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    adapter.info(
        "request_finished method=%s path=%s status_code=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.get("/health")
def health():
    logger.info("health_check")
    return {"status": "ok"}


@app.post("/register")
def register(user: UserRegister, request: Request):
    email = user.email.strip().lower()
    logger.info("registration_attempt email=%s", email)

    connection = get_connection()
    try:
        existing = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        ).fetchone()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        password_hash = hash_password(user.password)

        cursor = connection.execute(
            """
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
            """,
            (email, password_hash),
        )
        connection.commit()

        user_id = cursor.lastrowid
    finally:
        connection.close()

    logger.info("registration_success user_id=%s", user_id)
    return {
        "message": "User registered successfully",
        "user_id": user_id,
    }


@app.post("/login")
def login(user: UserLogin, request: Request):
    email = user.email.strip().lower()
    logger.info("login_attempt email=%s", email)

    connection = get_connection()
    row = connection.execute(
        "SELECT id, password_hash FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    connection.close()

    if not row or not verify_password(user.password, row[1]):
        logger.warning("login_failed email=%s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(row[0])
    logger.info("login_success user_id=%s", row[0])

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@app.post("/documents")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
):
    logger.info("document_upload_started user_id=%s filename=%s", user_id, file.filename)
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    user_directory = DOCUMENTS_ROOT / str(user_id)
    user_directory.mkdir(parents=True, exist_ok=True)

    safe_filename = Path(file.filename).name
    destination = user_directory / safe_filename

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO documents (user_id, filename, uploaded_at)
            VALUES (?, ?, datetime('now'))
            """,
            (user_id, safe_filename),
        )
        document_id = cursor.lastrowid
        connection.commit()

        with destination.open("wb") as output:
            shutil.copyfileobj(file.file, output)

        ingest_file(
            destination,
            user_id=user_id,
            document_id=document_id,
        )

        bm25, data = build_bm25(user_id)
        request.app.state.bm25_indexes[user_id] = (bm25, data)

    except Exception:
        logger.exception("document_upload_failed user_id=%s filename=%s", user_id, safe_filename)
        connection.rollback()
        if destination.exists():
            destination.unlink()
        raise
    finally:
        connection.close()

    logger.info("document_upload_success user_id=%s document_id=%s filename=%s", user_id, document_id, safe_filename)
    return {
        "message": "Document uploaded and ingested",
        "document_id": document_id,
        "filename": safe_filename,
    }


@app.post("/ask", response_model=AskResponse)
def ask(
    data: AskRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
):
    logger.info("rag_request_started user_id=%s", user_id)
    try:
        if user_id not in request.app.state.bm25_indexes:
            bm25, bm25_data = build_bm25(user_id)
            request.app.state.bm25_indexes[user_id] = (bm25, bm25_data)
        else:
            bm25, bm25_data = request.app.state.bm25_indexes[user_id]

        answer = run_rag(
            data.query,
            user_id,
            bm25,
            bm25_data,
        )

        logger.info("rag_request_success user_id=%s", user_id)
        return AskResponse(answer=answer)

    except Exception:
        logger.exception("rag_request_failed user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate an answer.",
        )
