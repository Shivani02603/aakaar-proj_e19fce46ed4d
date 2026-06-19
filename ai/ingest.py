import os
import pandas as pd
from tiktoken import Tokenizer
from .embeddings import get_embedding
from pgvector.psycopg2 import register_vector
import psycopg2

# Constants for chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def chunk(document):
    """
    Splits a document into overlapping chunks based on token size.
    """
    tokenizer = Tokenizer()
    tokens = tokenizer.encode(document)
    chunks = []
    for i in range(0, len(tokens), CHUNK_SIZE - CHUNK_OVERLAP):
        chunk_tokens = tokens[i:i + CHUNK_SIZE]
        chunks.append(tokenizer.decode(chunk_tokens))
    return chunks

def ingest_excel(file_path, session_id, user_id):
    """
    Reads an Excel file, chunks its content, generates embeddings, and stores them in the vector store.
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

    # Read the Excel file
    excel_data = pd.ExcelFile(file_path)
    for sheet_name in excel_data.sheet_names:
        sheet_data = excel_data.parse(sheet_name)
        for index, row in sheet_data.iterrows():
            row_text = row.to_string(index=False)
            chunks = chunk(row_text)
            for chunk_text in chunks:
                embedding = get_embedding(chunk_text, api_key=openai_api_key)
                cursor.execute(
                    """
                    INSERT INTO document_chunks (session_id, user_id, content, embedding, chunk_index, start_row, end_row, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (session_id, content)
                    DO UPDATE SET embedding = EXCLUDED.embedding;
                    """,
                    (session_id, user_id, chunk_text, embedding, index, index, index, '{}')
                )
    conn.commit()
    cursor.close()
    conn.close()