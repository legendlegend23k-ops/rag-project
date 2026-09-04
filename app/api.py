from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.rag_pipeline import run_rag_stream  # Assumes you have a streaming version of your RAG pipeline
from app.bm25_search import build_bm25

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("🚀 Application starting...")

    print("Building BM25 index...")

    bm25, bm25_data = build_bm25()

    app.state.bm25 = bm25
    app.state.bm25_data = bm25_data

    print("BM25 index ready.")

    yield

    print("🛑 Application shutting down...")


app = FastAPI(
    title="RAG API",
    lifespan=lifespan
)


class AskRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(request: Request, data: AskRequest):
    try:
        # Stream the response chunks directly back to the client for faster UX
        return StreamingResponse(
            run_rag_stream(
                data.query,
                request.app.state.bm25,
                request.app.state.bm25_data
            ),
            media_type="text/plain"
        )

    except Exception as error:
        print(f"RAG error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Failed to generate an answer."
        )


@app.post("/test-background")
def test_background(background_tasks: BackgroundTasks):

    background_tasks.add_task(
        print,
        "🔥 Background task finished!"
    )

    return {
        "message": "Task started in background"
    }