import os
import psycopg2
from pgvector.psycopg2 import register_vector
import google.generativeai as genai

# Constants
EMBEDDING_DIM = 1536
TOP_K = 5

def retrieve_context(query, top_k, session_id, user_id):
    """
    Embeds the query, retrieves the top-k most relevant chunks from the vector store.
    """
    # Read the PostgreSQL connection details from environment variables
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    db_name = os.getenv("POSTGRES_DB")
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")

    # Connect to PostgreSQL with pgvector extension
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password
    )
    register_vector(conn)
    cursor = conn.cursor()

    # Embed the query
    query_embedding = [0] * EMBEDDING_DIM  # Placeholder for embedding logic

    # Retrieve top-k chunks by cosine similarity
    cursor.execute(
        """
        SELECT content, metadata
        FROM vectors
        WHERE session_id = %s AND user_id = %s
        ORDER BY embedding <=> %s
        LIMIT %s
        """,
        (session_id, user_id, query_embedding, top_k)
    )
    results = cursor.fetchall()
    conn.close()

    # Format the results
    context = [{"content": row[0], "metadata": row[1]} for row in results]
    return context

def answer_question(query: str, session_id: str, user_id: str) -> dict:
    """
    Retrieves context, generates an answer using gemini-2.0-flash, and returns the answer with sources.
    """
    # Retrieve context
    context = retrieve_context(query, TOP_K, session_id, user_id)

    # Build the prompt
    context_text = "\n".join([f"{item['content']} (Source: {item['metadata']})" for item in context])
    prompt = f"Context:\n{context_text}\n\nQuestion: {query}\nAnswer:"

    # Read the Gemini API key from environment variables
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=gemini_api_key)

    # Generate the answer
    response = genai.generate_text(model="gemini-2.0-flash", prompt=prompt)
    answer = response.result

    # Extract sources
    sources = [{"filename": item["metadata"]["sheet"], "row": item["metadata"]["row"]} for item in context]

    return {"answer": answer, "sources": sources}