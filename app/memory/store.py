from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.safety.files import sanitize_filename, sha256_hex, validate_file


class DecimalEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)


class ProfileSnapshot(BaseModel):
    version: int = 0
    data: dict[str, Any] = Field(default_factory=dict)


def _utc_ms() -> int:
    return int(time.time() * 1000)


def _connect(sqlite_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(sqlite_path, isolation_level="DEFERRED", check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    return con


def _deep_merge(source: dict, destination: dict) -> dict:
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            _deep_merge(value, node)
        else:
            destination[key] = value
    return destination


def _flatten(d: dict, prefix: str = "") -> dict:
    flat: dict[str, Any] = {}
    for k, v in d.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            flat.update(_flatten(v, path))
        else:
            flat[path] = v
    return flat


def _compute_diff(old: dict, new: dict) -> list:
    flat_old, flat_new = _flatten(old), _flatten(new)
    paths = set(flat_old.keys()) | set(flat_new.keys())
    return [
        {"path": p, "old": flat_old.get(p), "new": flat_new.get(p)}
        for p in sorted(paths)
        if flat_old.get(p) != flat_new.get(p)
    ]


def _apply_diff_reverse(data: dict, diffs: list) -> dict:
    out = json.loads(json.dumps(data))
    for item in diffs:
        path, cur = item["path"].split("."), out
        for key in path[:-1]:
            cur = cur.setdefault(key, {})
        last = path[-1]
        if item["old"] is None:
            if last in cur:
                del cur[last]
        else:
            cur[last] = item["old"]
    return out


# def sanitize_filename(name: str) -> str:
#     # Remove potentially dangerous characters for all OSes
#     name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
#     # prevent blank, dot, or reserved names
#     if not name or name.strip(" .") == "":
#         return "uploaded_file"
#     return name[:80]


# def sha256_hex(data: bytes) -> str:
#     return hashlib.sha256(data).hexdigest()


class ProfileStore:
    def __init__(self, sqlite_path: str = ".data/profile.db", upload_dir: str = ".data/uploads"):
        self.sqlite_path = sqlite_path
        self.upload_dir = upload_dir
        Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        with _connect(self.sqlite_path) as con:
            self._ensure_schema(con)

    def _ensure_schema(self, con: sqlite3.Connection) -> None:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                user_id TEXT PRIMARY KEY, version INTEGER NOT NULL,
                data TEXT NOT NULL, updated_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS actions (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, kind TEXT NOT NULL,
                payload TEXT NOT NULL, payload_hash TEXT NOT NULL,
                committed INTEGER NOT NULL, version_after INTEGER, diff TEXT,
                created_at INTEGER NOT NULL, undo_of TEXT
            );
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                turn_id TEXT, action_id TEXT, kind TEXT NOT NULL,
                payload TEXT,
                payload_hash TEXT, /* FIX: Add column for hash */
                result TEXT, created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evidence_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                filename TEXT NOT NULL, content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL,
                category TEXT, turn_id TEXT, created_at INTEGER NOT NULL,
                path TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS receipt_parses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, attachment_id INTEGER NOT NULL,
                user_id TEXT NOT NULL, text TEXT, parsed_data TEXT, engine TEXT,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(attachment_id) REFERENCES evidence_files(id)
            );
            """
        )

    def get_profile(self, user_id: str) -> ProfileSnapshot:
        with _connect(self.sqlite_path) as con:
            row = con.execute(
                "SELECT version, data FROM profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
            if not row:
                empty = ProfileSnapshot(version=0, data={"preferences": {"language": "auto"}})
                con.execute(
                    "INSERT INTO profiles VALUES (?, ?, ?, ?)",
                    (user_id, empty.version, json.dumps(empty.data), _utc_ms()),
                )
                return empty
            return ProfileSnapshot(version=row[0], data=json.loads(row[1]))

    def apply_patch(self, user_id: str, patch: dict) -> tuple[ProfileSnapshot, list[dict]]:
        with _connect(self.sqlite_path) as con:
            current = self.get_profile(user_id)
            old_data, new_data = current.data, current.data.copy()
            _deep_merge(patch, new_data)
            new_version = current.version + 1
            diff = _compute_diff(old_data, new_data)
            con.execute(
                "UPDATE profiles SET version=?, data=?, updated_at=? WHERE user_id=?",
                (new_version, json.dumps(new_data), _utc_ms(), user_id),
            )
            return ProfileSnapshot(version=new_version, data=new_data), diff

    def commit_action(
        self,
        user_id: str,
        action_id: str,
        kind: str,
        payload: dict,
        payload_hash: str,
        diff: list,
        committed: bool,
        undo_of: str | None = None,
    ) -> None:
        with _connect(self.sqlite_path) as con:
            v_after = self.get_profile(user_id).version if committed else None
            con.execute(
                "INSERT INTO actions VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    action_id,
                    user_id,
                    kind,
                    json.dumps(payload),
                    payload_hash,
                    1 if committed else 0,
                    v_after,
                    json.dumps(diff),
                    _utc_ms(),
                    undo_of,
                ),
            )

    def _get_last_committed_action(self, user_id: str) -> dict | None:
        with _connect(self.sqlite_path) as con:
            sql = (
                "SELECT id, diff FROM actions WHERE user_id=? AND committed=1 "
                "AND diff IS NOT NULL ORDER BY created_at DESC LIMIT 1"
            )
            row = con.execute(sql, (user_id,)).fetchone()
            return {"id": row[0], "diff": json.loads(row[1])} if row else None

    def undo_action(self, user_id: str, new_action_id: str) -> ProfileSnapshot:
        last_action = self._get_last_committed_action(user_id)
        if not last_action:
            raise ValueError("No undoable action found.")
        current_profile = self.get_profile(user_id)
        reverted_data = _apply_diff_reverse(current_profile.data, last_action["diff"])
        with _connect(self.sqlite_path) as con:
            new_version = current_profile.version + 1
            con.execute(
                "UPDATE profiles SET version=?, data=?, updated_at=? WHERE user_id=?",
                (new_version, json.dumps(reverted_data), _utc_ms(), user_id),
            )
            new_snapshot = ProfileSnapshot(version=new_version, data=reverted_data)
        self.commit_action(
            user_id,
            new_action_id,
            "undo",
            {"ref_action_id": last_action["id"]},
            "",
            last_action["diff"],
            True,
            undo_of=last_action["id"],
        )
        return new_snapshot

    def add_attachment(
        self,
        user_id: str,
        filename: str,
        content_type: str | None,
        data: bytes,
        category: str | None,
        turn_id: str,
    ) -> dict:
        is_valid, reason = validate_file(content_type, len(data))
        if not is_valid:
            raise ValueError(reason)
        fname = sanitize_filename(filename)
        hash_val = sha256_hex(data)
        dest_path = Path(self.upload_dir) / f"{hash_val[:16]}_{fname}"
        with open(dest_path, "wb") as f:
            f.write(data)
        meta = {
            "user_id": user_id,
            "filename": fname,
            "content_type": content_type,
            "size_bytes": len(data),
            "sha256": hash_val,
            "category": category,
            "turn_id": turn_id,
            "created_at": _utc_ms(),
            "path": str(dest_path),
        }
        with _connect(self.sqlite_path) as con:
            cur = con.execute(
                (
                    "INSERT INTO evidence_files (user_id, filename, content_type, size_bytes, "
                    "sha256, category, turn_id, created_at, path) "
                    "VALUES (?,?,?,?,?,?,?,?,?)"
                ),
                (
                    meta["user_id"],
                    meta["filename"],
                    meta["content_type"],
                    meta["size_bytes"],
                    meta["sha256"],
                    meta["category"],
                    meta["turn_id"],
                    meta["created_at"],
                    meta["path"],
                ),
            )
            meta["id"] = cur.lastrowid
        return meta

    def get_attachment(self, attachment_id: int) -> dict | None:
        with _connect(self.sqlite_path) as con:
            con.row_factory = sqlite3.Row
            row = con.execute(
                "SELECT * FROM evidence_files WHERE id=?", (attachment_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_attachments(self, user_id: str, limit: int = 100) -> list[dict]:
        with _connect(self.sqlite_path) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT * FROM evidence_files WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def save_receipt_parse(
        self, user_id: str, attachment_id: int, text: str, parsed_data: Any, engine: str
    ) -> int:
        if hasattr(parsed_data, "model_dump"):
            serializable_data = parsed_data.model_dump()
        elif hasattr(parsed_data, "__dict__"):
            serializable_data = asdict(parsed_data)
        else:
            serializable_data = parsed_data
        with _connect(self.sqlite_path) as con:
            cur = con.execute(
                (
                    "INSERT INTO receipt_parses (attachment_id, user_id, text, "
                    "parsed_data, engine, created_at) VALUES (?, ?, ?, ?, ?, ?)"
                ),
                (
                    attachment_id,
                    user_id,
                    text,
                    json.dumps(serializable_data, cls=DecimalEncoder),
                    engine,
                    _utc_ms(),
                ),
            )
            return cur.lastrowid or 0

    def get_receipt_parse_by_attachment(self, attachment_id: int) -> dict | None:
        """Retrieves the most recent parse for a given attachment ID."""
        with _connect(self.sqlite_path) as con:
            con.row_factory = sqlite3.Row
            # Reformat the long SQL string to be multi-line
            row = con.execute(
                "SELECT * FROM receipt_parses WHERE attachment_id = ? "
                "ORDER BY created_at DESC LIMIT 1",
                (attachment_id,),
            ).fetchone()
            if not row:
                return None

            parse = dict(row)
            parse["parsed_data"] = json.loads(parse["parsed_data"])
            return parse

    def list_actions(self, user_id: str, limit: int = 100) -> list[dict]:
        with _connect(self.sqlite_path) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT * FROM actions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def log_evidence(
        self, user_id: str, turn_id: str | None, kind: str, payload: dict, result: dict
    ) -> int:
        """Logs a read-only event, now including a hash of the payload for integrity."""
        with _connect(self.sqlite_path) as con:
            payload_str = json.dumps(payload, sort_keys=True)
            payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
            cur = con.execute(
                (
                    "INSERT INTO evidence (user_id, turn_id, kind, payload, "
                    "payload_hash, result, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                (user_id, turn_id, kind, payload_str, payload_hash, json.dumps(result), _utc_ms()),
            )
            return cur.lastrowid or 0

    def get_all_evidence_for_scan(self, user_id: str) -> list[dict]:
        """Fetches all evidence records for a user for an integrity scan."""
        with _connect(self.sqlite_path) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT id, kind, payload, payload_hash FROM evidence WHERE user_id = ?", (user_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def list_evidence(self, user_id: str, limit: int = 100) -> list[dict]:
        with _connect(self.sqlite_path) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT * FROM evidence WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_all_user_ids(self) -> list[str]:
        """Retrieves a list of all user_ids in the profiles table."""
        with _connect(self.sqlite_path) as con:
            rows = con.execute("SELECT user_id FROM profiles").fetchall()
            return [row[0] for row in rows]

    def list_attachments_older_than(self, user_id: str, cutoff_ms: int) -> list[dict]:
        """Lists attachment records older than a given timestamp for a dry run."""
        with _connect(self.sqlite_path) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT * FROM evidence_files WHERE user_id = ? AND created_at < ?",
                (user_id, cutoff_ms),
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_attachments_older_than(self, user_id: str, cutoff_ms: int) -> int:
        """Finds and deletes old attachment files and their database records."""
        with _connect(self.sqlite_path) as con:
            rows = con.execute(
                "SELECT path FROM evidence_files WHERE user_id = ? AND created_at < ?",
                (user_id, cutoff_ms),
            ).fetchall()
            for row in rows:
                try:
                    os.remove(row[0])
                except OSError:
                    pass  # Ignore if file is already gone

            cur = con.execute(
                "DELETE FROM evidence_files WHERE user_id = ? AND created_at < ?",
                (user_id, cutoff_ms),
            )
            return cur.rowcount or 0

    def list_evidence_older_than(self, user_id: str, cutoff_ms: int) -> list[dict]:
        """Lists evidence records older than a given timestamp for a dry run."""
        with _connect(self.sqlite_path) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT * FROM evidence WHERE user_id = ? AND created_at < ?", (user_id, cutoff_ms)
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_evidence_older_than(self, user_id: str, cutoff_ms: int) -> int:
        """Deletes old evidence records from the database."""
        with _connect(self.sqlite_path) as con:
            cur = con.execute(
                "DELETE FROM evidence WHERE user_id = ? AND created_at < ?",
                (user_id, cutoff_ms),
            )
            return cur.rowcount or 0
