def reciprocal_rank_fusion(
    vector_results,
    bm25_results,
    k=60
):
    fused_results = {}

    # Add vector search rankings
    for rank, result in enumerate(vector_results, start=1):

        result_id = result["id"]

        rrf_score = 1 / (k + rank)

        if result_id not in fused_results:

            fused_results[result_id] = {
                "id": result["id"],
                "document": result["document"],
                "metadata": result["metadata"],
                "rrf_score": 0
            }

        fused_results[result_id]["rrf_score"] += rrf_score

    # Add BM25 rankings
    for rank, result in enumerate(bm25_results, start=1):

        result_id = result["id"]

        rrf_score = 1 / (k + rank)

        if result_id not in fused_results:

            fused_results[result_id] = {
                "id": result["id"],
                "document": result["document"],
                "metadata": result["metadata"],
                "rrf_score": 0
            }

        fused_results[result_id]["rrf_score"] += rrf_score

    # Convert dictionary into a list
    fused_results = list(fused_results.values())

    # Highest RRF score first
    fused_results.sort(
        key=lambda result: result["rrf_score"],
        reverse=True
    )

    return fused_results