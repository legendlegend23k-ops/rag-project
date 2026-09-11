from app.generator import generate_answer


cache = {}

def cached_generate_answer(query, results):

    context = "\n\n".join(
        result["text"]
        for result in results
    )

    cache_key = (query, context)

    if cache_key in cache:

        print("CACHE HIT")

        return cache[cache_key]

    print("CACHE MISS")

    answer = generate_answer(
        query,
        results
    )

    cache[cache_key] = answer

    return answer