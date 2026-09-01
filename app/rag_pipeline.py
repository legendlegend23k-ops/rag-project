import asyncio

from app.hybrid_search import hybrid_search
from app.parent_retrieval import retrieve_parents
from app.reranker import rerank
from app.generator import generate_answer


def run_rag(query):

    child_results = asyncio.run(
        hybrid_search(query, top_k=20)
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

    answer = generate_answer(
        query,
        final_results
    )

    return answer