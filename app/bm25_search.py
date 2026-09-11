from app.vector_store import collection
from rank_bm25 import BM25Okapi

def load_documents(user_id=None):
    data = {"ids": [], "documents": [], "metadatas": []}
    
    # Try filtering by user_id if provided
    if user_id is not None:
        try:
            data = collection.get(
                include=["documents", "metadatas"],
                where={"user_id": user_id}
            )
        except Exception:
            pass # Fallback if 'user_id' filter fails schema check
            
    # Fallback: if no documents matched the user_id (or user_id is None), fetch all documents
    if not data.get("documents"):
        print("Notice: No user-specific documents found or user_id is None. Loading all documents from Chroma.")
        data = collection.get(include=["documents", "metadatas"])

    return {
        "ids": data.get("ids", []),
        "documents": data.get("documents", []),
        "metadatas": data.get("metadatas", []),
    }


def build_bm25(user_id=None):
    data = load_documents(user_id)

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
        reverse=True,
    )

    results = []

    for index in ranked_indexes[:top_k]:
        results.append({
            "id": data["ids"][index],
            "document": data["documents"][index],
            "metadata": data["metadatas"][index],
            "bm25_score": float(scores[index]),
        })

    return results
