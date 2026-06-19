import os
from pgvector.psycopg2 import register_vector
import psycopg2
import google.generativeai as genai

def retrieve_context(query, top_k, session_id, user_id):
    """
    Embeds the query, retrieves the top-k relevant chunks from the vector store.
    """
    # Read the OpenAI API key lazily
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    # Read the PostgreSQL connection details lazily
    pg_host = os.getenv("PG_HOST")
    pg_port = os.getenv("PG_PORT")
    pg_user = os.getenv("PG_USER")
    pg_password = os.getenv("PG_PASSWORD")
    pg_database = os.getenv("PG_DATABASE")
    if not all([pg_host, pg_port, pg_user, pg_password, pg_database]):
        raise ValueError("PostgreSQL connection environment variables are not set.")

    # Connect to PostgreSQL and register pgvector
    conn = psycopg2.connect(
        host=pg_host,
        port=pg_port,
        user=pg_user,
        password=pg_password,
        dbname=pg_database
    )
    register_vector(conn)
    cursor = conn.cursor()

    # Embed the query
    query_embedding = embed_query(query, api_key=openai_api_key)

    # Retrieve top-k chunks by cosine similarity
    cursor.execute(
        """
        SELECT content, filename, row_range
        FROM vectors
        WHERE session_id = %s AND user_id = %s
        ORDER BY embedding <=> %s
        LIMIT %s;
        """,
        (session_id, user_id, query_embedding, top_k)
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    # Format the results
    context = [{"content": row[0], "filename": row[1], "row_range": row[2]} for row in results]
    return context

def embed_query(query, api_key):
    """
    Placeholder function for embedding the query.
    """
    # This function should implement the embedding logic
    raise NotImplementedError("Embedding logic is not implemented.")

def answer_question(query: str, session_id: str, user_id: str) -> dict:
    """
    Retrieves context, generates an answer using gemini-2.0-flash, and returns the answer with sources.
    """
    # Read the Google Generative AI API key lazily
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    # Retrieve context
    context = retrieve_context(query, top_k=5, session_id=session_id, user_id=user_id)

    # Build the prompt
    context_text = "\n".join([f"{item['content']}" for item in context])
    prompt = f"Context:\n{context_text}\n\nQuestion: {query}\nAnswer:"

    # Generate the answer using gemini-2.0-flash
    genai.configure(api_key=gemini_api_key)
    response = genai.generate_text(model="gemini-2.0-flash", prompt=prompt)

    # Extract the answer and format the sources
    answer = response.text.strip()
    sources = [{"filename": item["filename"], "row_range": item["row_range"]} for item in context]

    return {"answer": answer, "sources": sources}