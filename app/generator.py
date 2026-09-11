from google import genai

from app.config import GEMINI_API_KEY


client = genai.Client(api_key=GEMINI_API_KEY)



def generate_answer(query, results):

    context = "\n\n".join(
        result["text"]
        for result in results
    )

    prompt = f"""
You are a helpful question-answering assistant.

Answer the user's question using the provided context.

If the answer cannot be found in the context,
say that you don't have enough information.

Do not invent facts.

Context:
{context}

User question:
{query}

Answer:
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text


