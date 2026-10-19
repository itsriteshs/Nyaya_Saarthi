from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import FRONTEND_ORIGINS
from app.db.database import init_database
from app.api import health, datasets, matters, nlp, conversations

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield

app = FastAPI(title="NyayaSaarthi Backend", version="0.1.0", lifespan=lifespan)
@app.middleware("http")
async def limit_body(request: Request, call_next):
    if request.method in {"POST", "PATCH"}:
        if len(await request.body()) > 256_000:
            return JSONResponse(status_code=413, content={"detail": "Request body too large"})
    return await call_next(request)
app.add_middleware(CORSMiddleware, allow_origins=FRONTEND_ORIGINS, allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Content-Type"])
app.include_router(health.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(matters.router, prefix="/api/v1")
app.include_router(nlp.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
