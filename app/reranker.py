from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

reranker = CrossEncoder(MODEL_NAME)


def rerank(query, parent_results, top_k=3):

    pairs = []

    for result in parent_results:
        pairs.append(
            (query, result["text"])
        )

    scores = reranker.predict(pairs)

    for result, score in zip(parent_results, scores):
        result["reranker_score"] = float(score)

    parent_results.sort(
        key=lambda result: result["reranker_score"],
        reverse=True
    )

    return parent_results[:top_k]