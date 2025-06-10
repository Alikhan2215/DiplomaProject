from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi import Query, Response
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime
from pathlib import Path
from fastapi.responses import FileResponse

from app.core.security import get_current_user
from app.core.db import db
from app.models.document import DocumentOut
from app.utils.file_utils import save_upload, extract_text
from app.schemas.ai import SummarizeOut

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/", response_model=DocumentOut)
async def upload_doc(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    # 1) Save & validate extension
    saved_path = save_upload(file)

    # 2) Insert metadata
    rec = {
        "user_email": user["email"],
        "filename": file.filename,
        "path": str(saved_path),
        "upload_date": datetime.utcnow(),
    }
    res = await db.documents.insert_one(rec)
    return DocumentOut(
        id=str(res.inserted_id),
        filename=rec["filename"],
        upload_date=rec["upload_date"],
    )

@router.get("/", response_model=list[DocumentOut])
async def list_docs(user=Depends(get_current_user)):
    docs = []
    async for d in db.documents.find({"user_email": user["email"]}):
        docs.append(DocumentOut(
            id=str(d["_id"]),
            filename=d["filename"],
            upload_date=d["upload_date"],
        ))
    return docs

@router.get("/{doc_id}/content")
async def get_document_content(
    doc_id: str,
    user=Depends(get_current_user),
):
    # 1) fetch the metadata
    doc = await db.documents.find_one({
        "_id": ObjectId(doc_id),
        "user_email": user["email"],
    })
    if not doc:
        raise HTTPException(404, "Document not found")

    # 2) stream the file
    path = doc["path"]        # e.g. "uploads/… .docx"
    filename = doc["filename"]
    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=filename,
    )

@router.get("/{doc_id}/summaries", response_model=list[SummarizeOut])
async def get_summaries(doc_id: str, user=Depends(get_current_user)):
    docs = []
    cursor = db.summaries.find({
        "doc_id": ObjectId(doc_id),
        "user_email": user["email"]
    }).sort("created_at", -1)
    async for s in cursor:
        docs.append(SummarizeOut(
            id=str(s["_id"]),
            doc_id=doc_id,
            filename=s["filename"],
            mode=s["mode"],
            summary=s["summary"],
            created_at=s["created_at"],
        ))
    return docs

@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: str,
    cascade: bool = Query(False, description="Also delete all summaries of this doc"),
    user=Depends(get_current_user)
):
    """
    Deletes a document. If ?cascade=true, also deletes all summaries for that document.
    """
    oid = ObjectId(doc_id)
    # 1) Verify ownership
    doc = await db.documents.find_one({"_id": oid, "user_email": user["email"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2) Delete file from disk (ignore if already gone)
    try:
        Path(doc["path"]).unlink()
    except Exception:
        pass

    # 3) Delete the document record
    await db.documents.delete_one({"_id": oid})

    # 4) Optionally delete all its summaries
    if cascade:
        await db.summaries.delete_many({
            "doc_id": oid,
            "user_email": user["email"]
        })

    return Response(status_code=204)