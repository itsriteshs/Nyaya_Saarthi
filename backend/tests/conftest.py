import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["NYAYA_DATABASE_URL"] = "sqlite://"
# Unit/API fixtures use disposable indexes; production startup warming is tested separately.
os.environ["NYAYA_WARM_LEGAL_INDEX"] = "false"
# Ordinary regression tests never depend on a developer's installed model.
os.environ['NYAYA_INTAKE_SLM_ENABLED'] = 'false'
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import get_session
from app.db.models import Base

@pytest.fixture
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    def test_session():
        with Session() as session:
            yield session
    app.dependency_overrides[get_session] = test_session
    with TestClient(app) as value:
        yield value
    app.dependency_overrides.clear()
    engine.dispose()
