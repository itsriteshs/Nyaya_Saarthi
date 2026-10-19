from pathlib import Path
import os

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
DATASET_DIR = Path(os.getenv("NYAYA_DATASET_DIR", str(REPO_DIR / "data" / "Dataset 2")))
REPORT_DIR = Path(os.getenv("NYAYA_REPORT_DIR", str(BACKEND_DIR / "reports")))
DATABASE_URL = os.getenv("NYAYA_DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'nyaya.db'}")
FRONTEND_ORIGINS = [origin.strip() for origin in os.getenv("NYAYA_FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()]
