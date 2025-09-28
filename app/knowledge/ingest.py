from __future__ import annotations

import argparse

from .loader import load_rules_from_dir, write_rules_index_json


def build_index(
    rules_dir: str = "knowledge/rules/de", out_path: str = ".data/rules_index.json"
) -> str:
    rules = load_rules_from_dir(rules_dir)
    write_rules_index_json(rules, out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest DE rules into a normalized JSON index.")
    parser.add_argument("--rules-dir", default="knowledge/rules/de", help="Root of rules directory")
    parser.add_argument("--out", default=".data/rules_index.json", help="Output JSON path")
    args = parser.parse_args()
    rules = load_rules_from_dir(args.rules_dir)
    out = args.out
    write_rules_index_json(rules, out)
    print(f"✅ Wrote index with {len(rules)} rules to: {out}")


if __name__ == "__main__":
    main()
