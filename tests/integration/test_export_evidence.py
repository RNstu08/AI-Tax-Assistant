from pathlib import Path

from app.knowledge.ingest import build_index
from app.memory.store import ProfileStore
from app.orchestrator.graph import run_turn
from app.reports.pdf import export_pdf_and_log


def setup_module(module):
    build_index()


def test_export_generates_pdf(tmp_path: Path):
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    uid = "u_export"
    r = run_turn(user_id=uid, user_text="Commute 30km for 220 days, 100 home office", store=store)
    pdf_bytes, evid_id = export_pdf_and_log(uid, r, store)
    assert len(pdf_bytes) > 1000  # Check that a non-trivial PDF was created
