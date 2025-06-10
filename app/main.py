# app/main.py

from fastapi import FastAPI, Depends
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from app.routes.documents import router as docs_router
from app.routes.auth import router as auth_router
from app.core.security import get_current_user, bearer_scheme
from app.routes.users import router as users_router
from app.routes.ai import router as ai_router
from app.routes.folders import router as folders_router
from app.routes.summaries import router as summaries_router

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = FastAPI()

# include auth routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(docs_router)
app.include_router(ai_router)
app.include_router(summaries_router)
app.include_router(folders_router)




# protected test
@app.get("/protected", tags=["protected"])
async def protected(current_user = Depends(get_current_user)):
    return {"email": current_user["email"], "msg": "Authenticated!"}
