import asyncio

from app.vector_search import vector_search
from app.bm25_search import bm25_search
from app.rrf import reciprocal_rank_fusion


async def hybrid_search(query, bm25, bm25_data, top_k=20):

    vector_task = asyncio.to_thread(
        vector_search,
        query,
        top_k
    )

    bm25_task = asyncio.to_thread(
        bm25_search,
        query,
        bm25,
        bm25_data,
        top_k
    )

    vector_results, bm25_results = await asyncio.gather(
        vector_task,
        bm25_task
    )

    fused_results = reciprocal_rank_fusion(
        vector_results,
        bm25_results
    )

    return fused_results[:top_k]