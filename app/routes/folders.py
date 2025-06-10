# app/routes/folders.py

from fastapi import APIRouter, Depends, HTTPException, Response
from datetime import datetime
from bson import ObjectId
from app.schemas.folder import FolderCreate, FolderOut
from app.core.security import get_current_user
from app.core.db import db
from app.schemas.ai import SummarizeOut
router = APIRouter(prefix="/folders", tags=["folders"])

@router.post("/", response_model=FolderOut)
async def create_folder(data: FolderCreate, user=Depends(get_current_user)):
    rec = {
        "user_email": user["email"],
        "name": data.name,
        "created_at": datetime.utcnow(),
    }
    result = await db.folders.insert_one(rec)
    # Cast the ObjectId to str:
    return FolderOut(
        id=str(result.inserted_id),
        name=rec["name"],
        created_at=rec["created_at"],
    )

@router.get("/", response_model=list[FolderOut])
async def list_folders(user=Depends(get_current_user)):
    out = []
    async for f in db.folders.find({"user_email": user["email"]}).sort("created_at", -1):
        out.append(
            FolderOut(
                id=str(f["_id"]),
                name=f["name"],
                created_at=f["created_at"],
            )
        )
    return out


@router.get("/{folder_id}/summaries", response_model=list[SummarizeOut])
async def get_folder_summaries(folder_id: str, user=Depends(get_current_user)):
    # Validate folder ownership
    try:
        fid = ObjectId(folder_id)
    except:
        raise HTTPException(400, "Invalid folder_id")

    folder = await db.folders.find_one({"_id": fid, "user_email": user["email"]})
    if not folder:
        raise HTTPException(404, "Folder not found")

    # Fetch summaries assigned to this folder
    out = []
    async for s in db.summaries.find({
        "folder_id": fid,
        "user_email": user["email"]
    }).sort("created_at", -1):
        out.append(SummarizeOut(
            id=str(s["_id"]),
            doc_id=str(s["doc_id"]),
            filename=s["filename"],
            mode=s["mode"],
            summary=s["summary"],
            created_at=s["created_at"],
            folder_id=folder_id,
        ))
    return out

@router.delete("/{folder_id}/summaries/{summary_id}", status_code=204)
async def remove_summary_from_folder(
    folder_id: str,
    summary_id: str,
    user=Depends(get_current_user),
):
    """
    Un‐assign one summary from this folder (does not delete the summary).
    """
    # 1) verify folder ownership
    fid = ObjectId(folder_id)
    folder = await db.folders.find_one({"_id": fid, "user_email": user["email"]})
    if not folder:
        raise HTTPException(404, "Folder not found")
    # 2) clear the summary’s folder_id
    sid = ObjectId(summary_id)
    res = await db.summaries.update_one(
        {"_id": sid, "user_email": user["email"], "folder_id": fid},
        {"$set": {"folder_id": None}}
    )
    if res.modified_count == 0:
        raise HTTPException(404, "Summary not found in folder")
    return Response(status_code=204)

@router.put("/{folder_id}", response_model=FolderOut)
async def rename_folder(folder_id: str, data: FolderCreate, user=Depends(get_current_user)):
    oid = ObjectId(folder_id)
    res = await db.folders.update_one(
        {"_id": oid, "user_email": user["email"]},
        {"$set": {"name": data.name}}
    )
    if not res.modified_count:
        raise HTTPException(404, "Folder not found")
    f = await db.folders.find_one({"_id": oid})
    return FolderOut(
        id=str(f["_id"]),
        name=f["name"],
        created_at=f["created_at"],
    )

@router.delete("/{folder_id}", status_code=204)
async def delete_folder(folder_id: str, user=Depends(get_current_user)):
    oid = ObjectId(folder_id)
    res = await db.folders.delete_one({"_id": oid, "user_email": user["email"]})
    if not res.deleted_count:
        raise HTTPException(404, "Folder not found")
    # Optionally clear folder_id on summaries
    await db.summaries.update_many(
        {"folder_id": oid},
        {"$set": {"folder_id": None}}
    )
    return
