# tests/conftest.py
import sys
import pytest
from unittest.mock import MagicMock


def _mock_heavy_modules():
    """keybert / transformers / sentence_transformers / konlpy 등
    무거운 ML 패키지가 없어도 테스트가 돌아가도록 sys.modules에 미리 심어둔다."""
    for mod_name in [
        "keybert",
        "transformers",
        "sentence_transformers",
        "sentence_transformers.SentenceTransformer",
        "konlpy",
        "konlpy.tag",
        "konlpy.tag._okt",
    ]:
        if mod_name not in sys.modules:
            sys.modules[mod_name] = MagicMock()

    # nlp_handler 자체도 아직 로드됐으면 제거해 재-임포트 막기
    for mod_name in list(sys.modules.keys()):
        if mod_name in ("nlp_handler", "db", "main") or mod_name.startswith("routers"):
            del sys.modules[mod_name]


@pytest.fixture
def client():
    """NLP 모델 로드 없이 TestClient 반환."""
    _mock_heavy_modules()

    # db.supabase 를 MagicMock 으로 교체한 뒤 앱을 임포트한다
    import importlib
    import db as db_module
    db_module.supabase = MagicMock()

    # nlp_handler 의 무거운 객체를 mock 으로 덮어씌운다
    import nlp_handler as nlp_module
    nlp_module.kw_model = MagicMock()
    nlp_module.sentiment_pipeline = MagicMock()
    nlp_module.okt = MagicMock()

    from fastapi.testclient import TestClient
    from main import app
    yield TestClient(app)
