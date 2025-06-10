from fastapi import APIRouter, HTTPException, Depends
from fastapi import Response
from bson import ObjectId
from app.core.security import get_current_user
from app.core.db import db
from app.schemas.ai import SummarizeOut
from app.schemas.summary import SummaryFolderUpdate
from app.models.note import SummaryNoteUpdate

router = APIRouter(prefix="/summaries", tags=["summaries"])

@router.put("/{summary_id}/folder", response_model=SummarizeOut)
async def update_summary_folder(
    summary_id: str,
    data: SummaryFolderUpdate,
    user = Depends(get_current_user)
):
    # 1) Fetch and validate ownership
    rec = await db.summaries.find_one({
        "_id": ObjectId(summary_id),
        "user_email": user["email"]
    })
    if not rec:
        raise HTTPException(404, "Summary not found")

    update = {}
    # 2) If folder_id provided, validate that folder exists & you own it
    if data.folder_id is not None:
        try:
            fid = ObjectId(data.folder_id)
        except Exception:
            raise HTTPException(400, "Invalid folder_id")
        folder = await db.folders.find_one({
            "_id": fid,
            "user_email": user["email"]
        })
        if not folder:
            raise HTTPException(404, "Folder not found")
        update["folder_id"] = fid
    else:
        update["folder_id"] = None

    # 3) Persist change
    await db.summaries.update_one(
        {"_id": ObjectId(summary_id)},
        {"$set": update}
    )

    # 4) Return the updated summary
    updated = await db.summaries.find_one({"_id": ObjectId(summary_id)})
    return SummarizeOut(
        id=str(updated["_id"]),
        doc_id=str(updated["doc_id"]),
        filename=updated["filename"],
        mode=updated["mode"],
        summary=updated["summary"],
        created_at=updated["created_at"],
        folder_id=str(updated.get("folder_id")) if updated.get("folder_id") else None,
    )

@router.get("/{summary_id}", response_model=SummarizeOut)
async def get_one_summary(summary_id: str, user=Depends(get_current_user)):
    """
    Fetch one summary (including its note, if any).
    """
    oid = ObjectId(summary_id)
    rec = await db.summaries.find_one({
        "_id": oid,
        "user_email": user["email"]
    })
    if not rec:
        raise HTTPException(404, "Summary not found")

    return SummarizeOut(
        id=str(rec["_id"]),
        doc_id=str(rec["doc_id"]),
        filename=rec["filename"],
        mode=rec["mode"],
        summary=rec["summary"],
        created_at=rec["created_at"],
        folder_id=str(rec.get("folder_id")) if rec.get("folder_id") else None,
        note=rec.get("note")
    )

@router.get("/", response_model=list[SummarizeOut])
async def list_all_summaries(user=Depends(get_current_user)):
    """
    Returns all summaries belonging to the current user,
    sorted newest first.
    """
    out: list[SummarizeOut] = []
    cursor = db.summaries.find(
        {"user_email": user["email"]}
    ).sort("created_at", -1)

    async for s in cursor:
        out.append(SummarizeOut(
            id=str(s["_id"]),
            doc_id=str(s["doc_id"]),
            filename=s["filename"],
            mode=s["mode"],
            summary=s["summary"],
            created_at=s["created_at"],
            folder_id=str(s["folder_id"]) if s.get("folder_id") else None,
        ))
    return out

@router.put("/{summary_id}/note", response_model=SummarizeOut)
async def update_summary_note(
    summary_id: str,
    data: SummaryNoteUpdate,
    user=Depends(get_current_user)
):
    """
    Add or overwrite the custom note on a summary.
    """
    oid = ObjectId(summary_id)
    # ensure it exists & you own it
    rec = await db.summaries.find_one({"_id": oid, "user_email": user["email"]})
    if not rec:
        raise HTTPException(404, "Summary not found")

    # update the note field
    await db.summaries.update_one(
        {"_id": oid},
        {"$set": {"note": data.note}}
    )

    # return the updated record
    updated = await db.summaries.find_one({"_id": oid})
    return SummarizeOut(
        id=str(updated["_id"]),
        doc_id=str(updated["doc_id"]),
        filename=updated["filename"],
        mode=updated["mode"],
        summary=updated["summary"],
        created_at=updated["created_at"],
        folder_id=str(updated.get("folder_id")) if updated.get("folder_id") else None,
        note=updated.get("note"),
    )

@router.delete("/{summary_id}", status_code=204)
async def delete_summary(
    summary_id: str,
    user=Depends(get_current_user)
):
    """
    Deletes exactly one summary.
    """
    oid = ObjectId(summary_id)
    res = await db.summaries.delete_one({
        "_id": oid,
        "user_email": user["email"]
    })
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Summary not found")
    return Response(status_code=204)
