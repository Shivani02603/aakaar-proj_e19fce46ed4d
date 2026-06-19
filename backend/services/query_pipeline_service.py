from typing import List, Dict
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk, UploadedFile
from backend.routers.query_pipeline import embed_query, retrieve_chunks, build_prompt, call_llm


class QueryPipelineService:
    async def embed_query(self, query: str) -> List[float]:
        """
        Embed the user query into a vector representation.
        """
        try:
            embedding = embed_query(query)
            return embedding
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to embed query: {str(e)}")

    async def retrieve_top_chunks(self, query_embedding: List[float], top_k: int, db: AsyncSession) -> List[DocumentChunk]:
        """
        Retrieve the top-k chunks based on cosine similarity.
        """
        try:
            chunks = retrieve_chunks(query_embedding, top_k, db)
            if not chunks:
                raise HTTPException(status_code=404, detail="No relevant chunks found.")
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error while retrieving chunks: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve chunks: {str(e)}")

    async def generate_answer(self, query: str, chunks: List[DocumentChunk]) -> Dict[str, str]:
        """
        Generate an answer using the retrieved chunks and the user's query.
        """
        try:
            context = build_prompt(chunks, query)
            messages = [{"role": "system", "content": context}, {"role": "user", "content": query}]
            response = call_llm(messages, stream=False)
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

    async def query_pipeline(self, query: str, top_k: int, db: AsyncSession) -> Dict[str, Dict]:
        """
        Execute the full query pipeline: embed query, retrieve chunks, and generate answer.
        """
        try:
            # Step 1: Embed the query
            query_embedding = await self.embed_query(query)

            # Step 2: Retrieve top-k chunks
            chunks = await self.retrieve_top_chunks(query_embedding, top_k, db)

            # Step 3: Generate answer
            answer = await self.generate_answer(query, chunks)

            # Step 4: Prepare citations
            citations = [
                {
                    "filename": chunk.metadata.get("filename"),
                    "row_range": f"{chunk.start_row}-{chunk.end_row}"
                }
                for chunk in chunks
            ]

            return {"answer": answer, "citations": citations}
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to execute query pipeline: {str(e)}")

    async def create_document_chunk(self, chunk_data: Dict, db: AsyncSession) -> DocumentChunk:
        """
        Create a new document chunk in the database.
        """
        try:
            new_chunk = DocumentChunk(**chunk_data)
            db.add(new_chunk)
            await db.commit()
            await db.refresh(new_chunk)
            return new_chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error while creating document chunk: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create document chunk: {str(e)}")

    async def get_document_chunk_by_id(self, chunk_id: UUID, db: AsyncSession) -> DocumentChunk:
        """
        Retrieve a document chunk by its ID.
        """
        try:
            result = await db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
            chunk = result.scalar_one_or_none()
            if not chunk:
                raise HTTPException(status_code=404, detail="Document chunk not found.")
            return chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error while retrieving document chunk: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve document chunk: {str(e)}")

    async def list_all_document_chunks(self, db: AsyncSession) -> List[DocumentChunk]:
        """
        List all document chunks in the database.
        """
        try:
            result = await db.execute(select(DocumentChunk))
            chunks = result.scalars().all()
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error while listing document chunks: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list document chunks: {str(e)}")

    async def update_document_chunk(self, chunk_id: UUID, updated_data: Dict, db: AsyncSession) -> DocumentChunk:
        """
        Update an existing document chunk.
        """
        try:
            chunk = await self.get_document_chunk_by_id(chunk_id, db)
            for key, value in updated_data.items():
                setattr(chunk, key, value)
            db.add(chunk)
            await db.commit()
            await db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error while updating document chunk: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update document chunk: {str(e)}")

    async def delete_document_chunk(self, chunk_id: UUID, db: AsyncSession) -> None:
        """
        Delete a document chunk by its ID.
        """
        try:
            chunk = await self.get_document_chunk_by_id(chunk_id, db)
            await db.delete(chunk)
            await db.commit()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error while deleting document chunk: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete document chunk: {str(e)}")