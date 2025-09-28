from pathlib import Path

from app.knowledge.ingest import build_index
from app.knowledge.retriever import InMemoryRetriever


def make_retriever(tmp_path: Path) -> InMemoryRetriever:
    """Test helper to build and load a retriever."""
    out = tmp_path / "rules_index.json"
    build_index("knowledge/rules/de", str(out))
    return InMemoryRetriever(index_path=out)


def test_retriever_year_filter(tmp_path: Path):
    r = make_retriever(tmp_path)
    hits = r.search("commute", year=2024, k=3)
    assert any(h.rule_id == "de_2024_commuting_allowance" for h in hits)
    assert not any(h.year == 2025 for h in hits)


def test_retriever_bilingual(tmp_path: Path):
    r = make_retriever(tmp_path)
    # English query for 2025
    hits_en = r.search("donations to charity 2025", year=2025, k=1)
    assert hits_en and hits_en[0].rule_id == "de_2025_charitable_donations"

    # German query for 2024
    hits_de = r.search("Arbeitsmittel Laptop", year=2024, k=1)
    assert hits_de and hits_de[0].rule_id == "de_2024_work_equipment"
