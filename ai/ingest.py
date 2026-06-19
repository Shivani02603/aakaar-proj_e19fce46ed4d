import os
import pandas as pd
from tiktoken import encoding_for_model
from pgvector.psycopg2 import register_vector
import psycopg2
from .embeddings import get_embedding

# Constants for chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_DIM = 1536

def chunk(document):
    """
    Splits a document into overlapping chunks using the token_overlap strategy.
    """
    encoder = encoding_for_model("text-embedding-3-small")
    tokens = encoder.encode(document)
    chunks = []
    for i in range(0, len(tokens), CHUNK_SIZE - CHUNK_OVERLAP):
        chunk_tokens = tokens[i:i + CHUNK_SIZE]
        chunk_text = encoder.decode(chunk_tokens)
        chunks.append(chunk_text)
        if len(chunk_tokens) < CHUNK_SIZE:
            break
    return chunks

def ingest_excel(file_path, session_id, user_id):
    """
    Reads an Excel file, processes its sheets, chunks the content, generates embeddings,
    and upserts the data into the vector store.
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

    # Read the Excel file
    excel_data = pd.ExcelFile(file_path)

    for sheet_name in excel_data.sheet_names:
        sheet_data = excel_data.parse(sheet_name)
        for index, row in sheet_data.iterrows():
            row_text = row.to_string(index=False)
            chunks = chunk(row_text)
            for chunk_text in chunks:
                embedding = get_embedding(chunk_text)
                # Upsert into the vector store
                cursor.execute(
                    """
                    INSERT INTO document_chunks (session_id, file_id, embedding, content, metadata, chunk_index, start_row, end_row, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (file_id, chunk_index) DO NOTHING
                    """,
                    (session_id, None, embedding, chunk_text, {"sheet": sheet_name, "row": index}, index, index, index)
                )

    conn.commit()
    cursor.close()
    conn.close()