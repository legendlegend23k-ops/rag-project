import asyncio

from app.hybrid_search import hybrid_search
from app.parent_retrieval import retrieve_parents
from app.reranker import rerank
from app.cache import cached_generate_answer


def run_rag(query, user_id, bm25, bm25_data):
    child_results = asyncio.run(
        hybrid_search(
            query,
            user_id,
            bm25,
            bm25_data,
            top_k=20,
        )
    )

    parent_results = retrieve_parents(
        child_results,
        user_id,
        top_k=5,
    )

    final_results = rerank(
        query,
        parent_results,
        top_k=3,
    )

    return cached_generate_answer(query, final_results)
