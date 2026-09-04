import asyncio

from app.hybrid_search import hybrid_search
from app.parent_retrieval import retrieve_parents
from app.reranker import rerank
from app.generator import generate_answer_stream


def run_rag_stream(query, bm25, bm25_data):
    child_results = asyncio.run(
        hybrid_search(
            query,
            bm25,
            bm25_data,
            top_k=20
        )
    )

    parent_results = retrieve_parents(
        child_results,
        top_k=5
    )

    final_results = rerank(
        query,
        parent_results,
        top_k=3
    )

    for chunk in generate_answer_stream(query, final_results):
        yield chunk