from fastapi import APIRouter
router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "service": "nyayasaarthi-backend", "version": "0.1.0"}
