from app.vector_store import collection


def vector_search(query, user_id, top_k=20):
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"user_id": user_id},
        include=["documents", "metadatas", "distances"],
    )

    vector_results = []

    for index in range(len(results["ids"][0])):
        vector_results.append({
            "id": results["ids"][0][index],
            "document": results["documents"][0][index],
            "metadata": results["metadatas"][0][index],
            "vector_distance": results["distances"][0][index],
        })

    return vector_results
