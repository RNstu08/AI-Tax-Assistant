from app.infra.config import AppSettings
from app.memory.store import ProfileStore
from app.services.telemetry import configure_logging
from tools.constants import CONST


def test_imports_and_basic_objects(tmp_path):
    cfg = AppSettings()
    assert cfg.environment == "dev"
    configure_logging(json_logs=True, level="INFO")
    # FIX: Use correct argument and isolated path
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    snap = store.get_profile(user_id="u1")
    assert snap.version == 0
    assert 2024 in CONST
