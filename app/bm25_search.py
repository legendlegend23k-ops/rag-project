from app.vector_store import collection
from rank_bm25 import BM25Okapi


def load_documents():

    data = collection.get(
        include=[
            "documents",
            "metadatas"
        ]
    )

    return {
        "ids": data["ids"],
        "documents": data["documents"],
        "metadatas": data["metadatas"]
    }


def build_bm25():

    data = load_documents()

    tokenized_documents = [
        document.lower().split()
        for document in data["documents"]
    ]

    bm25 = BM25Okapi(tokenized_documents)

    return bm25, data


def bm25_search(query, bm25, data, top_k=20):

    tokenized_query = query.lower().split()

    scores = bm25.get_scores(tokenized_query)

    ranked_indexes = sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True
    )

    top_indexes = ranked_indexes[:top_k]

    results = []

    for index in top_indexes:

        results.append({
            "id": data["ids"][index],
            "document": data["documents"][index],
            "metadata": data["metadatas"][index],
            "bm25_score": float(scores[index])
        })

    return results