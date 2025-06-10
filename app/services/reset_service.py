# app/services/reset_service.py

import random
from datetime import datetime, timedelta
from app.core.db import db
from app.core.config import settings

CODE_LENGTH = 6
EXPIRY_MINUTES = 10

async def create_reset_code(email: str) -> str:
    """
    Generate a unique 6-digit code, store it in MongoDB with an expiry,
    and return the plain code to be emailed.
    """
    # 1) Generate a zero-padded 6-digit code
    code = f"{random.randint(0, 10**CODE_LENGTH - 1):0{CODE_LENGTH}d}"
    # 2) Insert into Mongo with TTL index on expires_at
    await db.password_resets.insert_one({
        "email": email,
        "code": code,
        "expires_at": datetime.utcnow() + timedelta(minutes=EXPIRY_MINUTES),
    })
    return code

async def consume_reset_code(code: str) -> str | None:
    """
    Atomically find + delete the reset document matching this code
    (and not yet expired). Returns the associated email if found.
    """
    rec = await db.password_resets.find_one_and_delete({
        "code": code,
        "expires_at": {"$gt": datetime.utcnow()},
    })
    return rec["email"] if rec else None
