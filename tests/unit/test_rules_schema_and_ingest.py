from pathlib import Path

from app.knowledge.ingest import build_index
from app.knowledge.loader import load_rules_from_dir


def test_load_rules_and_write_index(tmp_path: Path):
    rules = load_rules_from_dir("knowledge/rules/de")
    assert len(rules) == 8  # 4 categories * 2 years

    # Check for uniqueness and coverage
    years = {r.year for r in rules}
    cats = {r.category for r in rules}
    assert years == {2024, 2025}
    assert cats == {"commuting", "home_office", "equipment", "donations"}

    out = tmp_path / "rules_index.json"
    build_index("knowledge/rules/de", str(out))
    assert out.exists()
