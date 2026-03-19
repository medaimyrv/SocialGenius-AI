"""
Endpoints para subir y gestionar documentos de referencia por negocio.
Los documentos se indexan automáticamente en pgvector para RAG.
"""

import logging
import uuid
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.models.business import Business
from app.models.document import Document
from app.services import rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {"application/pdf", "text/plain", "text/markdown"}
MAX_SIZE_MB = 10


@router.post("/{business_id}", status_code=201)
async def upload_document(
    business_id: UUID,
    file: UploadFile = File(...),
    db: DB = None,
    current_user: CurrentUser = None,
):
    """Sube un documento (PDF o TXT) y lo indexa para RAG."""
    # Verificar que el negocio pertenece al usuario
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.owner_id == current_user.id,
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    # Validar tipo y tamaño
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo no permitido. Usa PDF o TXT.",
        )

    raw = await file.read()
    if len(raw) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Archivo muy grande (máx {MAX_SIZE_MB}MB)")

    # Extraer texto
    text = _extract_text(raw, content_type)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No se pudo extraer texto del archivo")

    # Guardar en DB
    doc = Document(
        business_id=business_id,
        user_id=current_user.id,
        filename=file.filename or "documento",
        content_type=content_type,
        text_content=text[:50000],  # límite 50k chars
        chunk_count=0,
    )
    db.add(doc)
    await db.flush()

    # Indexar en pgvector
    chunks = await rag_service.index_document(
        db=db,
        business_id=str(business_id),
        document_id=str(doc.id),
        filename=doc.filename,
        text_=text,
    )
    doc.chunk_count = chunks
    await db.commit()

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "chunk_count": chunks,
        "message": f"Documento indexado en {chunks} fragmentos",
    }


@router.get("/{business_id}")
async def list_documents(
    business_id: UUID,
    db: DB = None,
    current_user: CurrentUser = None,
):
    """Lista los documentos subidos para un negocio."""
    result = await db.execute(
        select(Document).where(
            Document.business_id == business_id,
            Document.user_id == current_user.id,
        )
    )
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "filename": d.filename,
            "content_type": d.content_type,
            "chunk_count": d.chunk_count,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.delete("/{business_id}/{document_id}", status_code=204)
async def delete_document(
    business_id: UUID,
    document_id: UUID,
    db: DB = None,
    current_user: CurrentUser = None,
):
    """Elimina un documento y sus vectores del RAG."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    await rag_service.delete_document_chunks(db, str(business_id), str(document_id))
    await db.delete(doc)
    await db.commit()


# ─── Utilidades ──────────────────────────────────────────────────────────────

def _extract_text(raw: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(raw))
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return ""
    return raw.decode("utf-8", errors="ignore")
