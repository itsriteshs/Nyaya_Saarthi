from contextlib import asynccontextmanager
import asyncio
import logging
import os
from app.services.legal.index import INDEX_DIR, load_index
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import FRONTEND_ORIGINS
from app.db.database import init_database
from app.api import health, datasets, matters, nlp, conversations, legal, models

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    if os.getenv('NYAYA_WARM_LEGAL_INDEX','true').lower()=='true' and (INDEX_DIR/'manifest.json').is_file():
        logging.getLogger(__name__).info('Loading the local legal index before accepting requests')
        try:
            await asyncio.to_thread(load_index)
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            logging.getLogger(__name__).warning('Legal index unavailable; legal endpoints remain fail-closed: %s',exc)
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
app.include_router(legal.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")
