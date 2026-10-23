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


@pytest.fixture(autouse=True)
def legacy_planner_input(request, monkeypatch):
    """Legacy planner/API regressions supply deterministic test data only.
    Production intake never uses this adapter. SLM integration tests opt out.
    """
    if request.module.__name__ in {'test_slm_intake','test_intake_guidance_revision','test_slm_required','test_flexible_intake','test_compact_intake'}:
        return
    from app.services.nlp.entity_extractor import extract
    from app.services.nlp.normalizer import normalize
    def fixture_entities(text, reference=None, **kwargs):
        return [normalize(e) for e in extract(text,reference)], {'method':'test_fixture','fallbackUsed':False}
    monkeypatch.setattr('app.services.nlp.pipeline.interpret',fixture_entities)
    monkeypatch.setattr('app.services.conversation.interpret',fixture_entities)
