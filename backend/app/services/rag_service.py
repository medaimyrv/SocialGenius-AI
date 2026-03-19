"""
RAG Service - Retrieval Augmented Generation
Usa ChromaDB como vector store con embeddings ONNX nativos (sin torch).

Colecciones:
- msgs_{business_id}  : historial de conversaciones del negocio
- docs_{business_id}  : documentos subidos por el usuario
"""

import logging
import uuid
from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

logger = logging.getLogger(__name__)

CHROMA_PATH = Path("./chroma_db")
TOP_K = 5


class RAGService:
    def __init__(self):
        self._client: chromadb.PersistentClient | None = None
        self._ef = ONNXMiniLM_L6_V2()  # Embeddings ONNX, sin torch, muy ligero

    def _get_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            CHROMA_PATH.mkdir(exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(CHROMA_PATH),
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    def _messages_collection(self, business_id: str):
        return self._get_client().get_or_create_collection(
            name=f"msgs_{business_id.replace('-', '')}",
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )

    def _documents_collection(self, business_id: str):
        return self._get_client().get_or_create_collection(
            name=f"docs_{business_id.replace('-', '')}",
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )

    # ─── Indexar mensajes ────────────────────────────────────────────────────

    def index_message(self, business_id: str, conversation_id: str, role: str, content: str) -> None:
        """Indexa un mensaje en el vector store del negocio."""
        try:
            col = self._messages_collection(business_id)
            col.add(
                ids=[str(uuid.uuid4())],
                documents=[content],
                metadatas=[{
                    "business_id": business_id,
                    "conversation_id": conversation_id,
                    "role": role,
                }],
            )
        except Exception as e:
            logger.error(f"Error indexing message: {e}")

    # ─── Indexar documentos ──────────────────────────────────────────────────

    def index_document(self, business_id: str, document_id: str, filename: str, text: str) -> int:
        """Divide el documento en chunks y los indexa. Retorna cantidad de chunks."""
        chunks = _chunk_text(text, chunk_size=500, overlap=50)
        if not chunks:
            return 0
        try:
            col = self._documents_collection(business_id)
            col.add(
                ids=[f"{document_id}_{i}" for i in range(len(chunks))],
                documents=chunks,
                metadatas=[{
                    "business_id": business_id,
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": i,
                } for i in range(len(chunks))],
            )
            return len(chunks)
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            return 0

    def delete_document(self, business_id: str, document_id: str) -> None:
        """Elimina todos los chunks de un documento del vector store."""
        try:
            col = self._documents_collection(business_id)
            results = col.get(where={"document_id": document_id})
            if results["ids"]:
                col.delete(ids=results["ids"])
        except Exception as e:
            logger.error(f"Error deleting document from vector store: {e}")

    # ─── Recuperar contexto ──────────────────────────────────────────────────

    def retrieve_context(self, business_id: str, query: str) -> str:
        """Recupera contexto relevante de mensajes y documentos para el query dado."""
        parts = []

        # 1. Mensajes anteriores relevantes
        try:
            msg_col = self._messages_collection(business_id)
            count = msg_col.count()
            if count > 0:
                results = msg_col.query(
                    query_texts=[query],
                    n_results=min(TOP_K, count),
                )
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                if docs:
                    history = []
                    for doc, meta in zip(docs, metas):
                        label = "Usuario" if meta.get("role") == "user" else "Asistente"
                        history.append(f"{label}: {doc}")
                    parts.append("### Conversaciones anteriores relevantes:\n" + "\n".join(history))
        except Exception as e:
            logger.warning(f"Error retrieving message context: {e}")

        # 2. Documentos subidos relevantes
        try:
            doc_col = self._documents_collection(business_id)
            count = doc_col.count()
            if count > 0:
                results = doc_col.query(
                    query_texts=[query],
                    n_results=min(TOP_K, count),
                )
                docs = results.get("documents", [[]])[0]
                metas = results.get("metadatas", [[]])[0]
                if docs:
                    doc_parts = []
                    for doc, meta in zip(docs, metas):
                        fname = meta.get("filename", "documento")
                        doc_parts.append(f"[{fname}]: {doc}")
                    parts.append("### Documentos de referencia:\n" + "\n".join(doc_parts))
        except Exception as e:
            logger.warning(f"Error retrieving document context: {e}")

        return "\n\n".join(parts) if parts else ""


# ─── Utilidades ──────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Divide texto en chunks con overlap para mejor recuperación."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 20:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# Singleton global
rag_service = RAGService()
