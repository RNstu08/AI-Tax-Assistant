from app.infra.config import AppSettings
from app.services.telemetry import configure_logging
from app.memory.store import ProfileStore
from tools.constants import CONST

def test_imports_and_basic_objects():
    # Config should load with defaults
    cfg = AppSettings()
    assert cfg.environment == "dev"

    # Logging should configure without error
    configure_logging(json_logs=True, level="INFO")

    # Store stub should return a dummy snapshot
    store = ProfileStore(db_path=".data/profile.db")
    snap = store.get_profile(user_id="u1")
    assert snap.version == 1

    # Constants should contain expected data
    assert 2024 in CONST and "commute" in CONST[2024]