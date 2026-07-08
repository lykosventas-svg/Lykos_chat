"""ChromaDB database management for the RAG chatbot."""

import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional


CHROMA_DIR = Path(__file__).parent.parent / "chroma_data"


class ChromaDBManager:
    """Manager for ChromaDB operations."""

    def __init__(self):
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection = None

    @property
    def client(self) -> chromadb.ClientAPI:
        """Lazy initialization of ChromaDB client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        return self._client

    @property
    def collection(self):
        """Get or create the default collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def is_empty(self) -> bool:
        """Check if the collection is empty."""
        return self.collection.count() == 0

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """Add documents to the collection."""
        if ids is None:
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(documents))]

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query(
        self,
        query_text: str,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """Query the collection for similar documents."""
        if self.is_empty():
            return {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "ids": []
            }

        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, self.collection.count())
        )

        return {
            "documents": results.get("documents", [[]])[0],
            "metadatas": results.get("metadatas", [[]])[0],
            "distances": results.get("distances", [[]])[0],
            "ids": results.get("ids", [[]])[0]
        }

    def delete_collection(self) -> None:
        """Delete the collection and reset."""
        try:
            self.client.delete_collection(name="documents")
        except Exception:
            pass
        self._collection = None

    def get_all_documents(self) -> Dict[str, Any]:
        """Get all documents in the collection."""
        if self.is_empty():
            return {"ids": [], "documents": [], "metadatas": []}

        results = self.collection.get()
        return results

    def delete_documents(self, ids: List[str]) -> None:
        """Delete specific documents by ID."""
        if ids:
            self.collection.delete(ids=ids)


# Singleton instance
db_manager = ChromaDBManager()
