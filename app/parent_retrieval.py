import json

from app.ingestion import PARENTS_PATH


def load_parent_records():

    with open(
        PARENTS_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def retrieve_parents(child_results, top_k=5):

    parent_record = load_parent_records()

    parent_scores = {}

    for child in child_results:

        parent_id = child["metadata"]["parent_id"]

        if parent_id not in parent_scores:
            parent_scores[parent_id] = 0

        parent_scores[parent_id] += child["rrf_score"]

    ranked_parents = sorted(
        parent_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    parent_results = []

    for parent_id, score in ranked_parents[:top_k]:

        if parent_id not in parent_record:
            continue

        parent = parent_record[parent_id]

        parent_results.append({
            "id": parent_id,
            "text": parent["text"],
            "source": parent["source"],
            "page": parent["page"],
            "score": score
        })

    return parent_results