"""Document management routes."""

from __future__ import annotations

import asyncio
import os
from uuid import UUID, uuid4

import anyio
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import get_current_active_user
from app.db.session import AsyncSessionLocal, get_db
from app.dependencies import get_document_processor, get_embedding_service, get_vector_store
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.document_processor import DocumentProcessor
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.utils.file_utils import ensure_directory, get_file_extension, safe_filename
from app.utils.logger import get_logger

logger = get_logger()

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
	"/upload",
	response_model=list[DocumentResponse],
	status_code=status.HTTP_202_ACCEPTED,
	summary="Upload a document",
	description="Upload one or more documents for indexing.",
	response_description="Document upload status.",
)
async def upload_document(
	background_tasks: BackgroundTasks,
	file: UploadFile | None = File(None),
	files: list[UploadFile] | None = File(None),
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db),
	document_processor: DocumentProcessor = Depends(get_document_processor),
	embedding_service: EmbeddingService = Depends(get_embedding_service),
	vector_store: VectorStoreService = Depends(get_vector_store),
) -> list[DocumentResponse]:
	"""Upload and enqueue a document for processing."""
	upload_files = files or ([file] if file else [])
	if not upload_files:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")

	responses: list[DocumentResponse] = []
	for upload in upload_files:
		file_type = get_file_extension(upload.filename)
		if file_type not in settings.ALLOWED_FILE_TYPES:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

		contents = await upload.read()
		file_size = len(contents)
		max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
		if file_size > max_bytes:
			raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

		safe_name = safe_filename(upload.filename)
		upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
		ensure_directory(upload_dir)
		doc_id = uuid4()
		stored_filename = f"{doc_id}_{safe_name}"
		file_path = os.path.join(upload_dir, stored_filename)

		async with await anyio.open_file(file_path, "wb") as handle:
			await handle.write(contents)

		namespace = f"user_{current_user.id}_doc_{doc_id}"
		document = Document(
			id=doc_id,
			user_id=current_user.id,
			filename=stored_filename,
			original_filename=safe_name,
			file_type=file_type,
			file_size_bytes=file_size,
			status=DocumentStatus.PENDING,
			pinecone_namespace=namespace,
			chunk_count=0,
		)
		db.add(document)
		await db.flush()
		await db.refresh(document)

		background_tasks.add_task(
			_start_background_task,
			process_document_background(
				document_processor,
				embedding_service,
				vector_store,
				doc_id=str(document.id),
				file_path=file_path,
				file_type=file_type,
				namespace=namespace,
			),
		)
		responses.append(DocumentResponse.model_validate(document))

	return responses


@router.get(
	"",
	response_model=DocumentListResponse,
	status_code=status.HTTP_200_OK,
	summary="List documents",
	description="List uploaded documents with optional filters.",
	response_description="Paginated list of documents.",
)
async def list_documents(
	skip: int = 0,
	limit: int = 20,
	status_filter: str | None = None,
	file_type: str | None = None,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
	"""List documents for the current user."""
	query = select(Document).where(Document.user_id == current_user.id)
	if status_filter:
		try:
			status_value = DocumentStatus(status_filter)
		except ValueError as exc:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter") from exc
		query = query.where(Document.status == status_value)
	if file_type:
		query = query.where(Document.file_type == file_type)

	count_result = await db.execute(select(func.count()).select_from(query.subquery()))
	total = int(count_result.scalar() or 0)
	result = await db.execute(query.offset(skip).limit(limit))
	documents = result.scalars().all()
	items = [DocumentResponse.model_validate(doc) for doc in documents]
	return DocumentListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
	"/{doc_id}",
	response_model=DocumentResponse,
	status_code=status.HTTP_200_OK,
	summary="Get document details",
	description="Return a single document record.",
	response_description="Document details.",
)
async def get_document(
	doc_id: str,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
	"""Get document details."""
	try:
		doc_uuid = UUID(doc_id)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID") from exc
	result = await db.execute(select(Document).where(Document.id == doc_uuid, Document.user_id == current_user.id))
	document = result.scalar_one_or_none()
	if document is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
	return DocumentResponse.model_validate(document)


@router.delete(
	"/{doc_id}",
	status_code=status.HTTP_204_NO_CONTENT,
	summary="Delete a document",
	description="Delete document and remove vectors from Pinecone.",
	response_description="Document deleted.",
)
async def delete_document(
	doc_id: str,
	current_user: User = Depends(get_current_active_user),
	db: AsyncSession = Depends(get_db),
	vector_store: VectorStoreService = Depends(get_vector_store),
) -> None:
	"""Delete a document and its vectors."""
	try:
		doc_uuid = UUID(doc_id)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID") from exc
	result = await db.execute(select(Document).where(Document.id == doc_uuid, Document.user_id == current_user.id))
	document = result.scalar_one_or_none()
	if document is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

	await vector_store.delete_namespace(document.pinecone_namespace)
	await db.delete(document)


def _start_background_task(coro: asyncio.Task | asyncio.Future | Any) -> None:
	"""Schedule an async background task."""
	asyncio.create_task(coro)


async def process_document_background(
	document_processor: DocumentProcessor,
	embedding_service: EmbeddingService,
	vector_store: VectorStoreService,
	doc_id: str,
	file_path: str,
	file_type: str,
	namespace: str,
) -> None:
	"""Process and index a document in the background."""
	async with AsyncSessionLocal() as session:
		try:
			document = await session.get(Document, UUID(doc_id))
			if document is None:
				return
			document.status = DocumentStatus.PROCESSING
			await session.commit()

			docs = await document_processor.process(file_path, file_type, doc_id)
			for doc in docs:
				doc.metadata["user_id"] = str(document.user_id)
			texts = [doc.page_content for doc in docs]
			embeddings = await embedding_service.embed_documents(texts)
			total = await vector_store.upsert_documents(docs, embeddings, namespace=namespace)

			document.status = DocumentStatus.INDEXED
			document.chunk_count = total
			await session.commit()
		except Exception as exc:
			logger.exception("document_processing_failed", doc_id=doc_id)
			document = await session.get(Document, UUID(doc_id))
			if document:
				document.status = DocumentStatus.FAILED
				document.error_message = str(exc)
				await session.commit()
		finally:
			await asyncio.to_thread(_safe_remove, file_path)


def _safe_remove(path: str) -> None:
	if os.path.exists(path):
		os.remove(path)
