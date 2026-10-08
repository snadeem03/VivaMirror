"""SQLite attempt history (US-08).

Stdlib only, independent of UI, speech, and Streamlit. Stores reviewed
answer text and evaluation results — never raw audio, secrets, or model
caches. All SQL is parameterized; connections are committed explicitly and
always closed. The database lives under ignored local runtime data
(``data/local/``); tests inject temporary paths.

Schema version is recorded in the database (``SCHEMA_VERSION``) and
initialization is idempotent: an existing database is never silently
deleted or reset. Malformed stored records raise :class:`StoredRecordError`
identifying the attempt instead of being dropped quietly.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1

_INPUT_MODES = ("typed", "spoken")

_COLUMNS = (
    "id",
    "created_at",
    "question_id",
    "rubric_fingerprint",
    "rubric_snapshot",
    "evaluator_version",
    "input_mode",
    "reviewed_text",
    "result_json",
    "coverage_pct",
    "assisted",
)


class StoreError(Exception):
    """Base class for persistence failures (never silently destructive)."""


class SchemaError(StoreError):
    """The database schema is missing or from an unknown version."""


class StoredRecordError(StoreError):
    """A stored attempt cannot be interpreted (e.g. corrupt JSON)."""


def default_db_path() -> Path:
    """Absolute default database path, independent of working directory."""
    return Path(__file__).resolve().parent.parent / "data" / "local" / "vivamirror.db"


def resolve_db_path(path: str | Path | None) -> Path:
    """Explicit path, or the ignored local default when None."""
    return Path(path).expanduser() if path is not None else default_db_path()


def fingerprint_for_question(question: dict) -> str:
    """Stable fingerprint of the rubric content that scoring depends on."""
    try:
        canonical = {
            "id": question["id"],
            "concepts": [
                {
                    "id": c["id"],
                    "label": c["label"],
                    "weight": float(c["weight"]),
                    "accepted_phrases": list(c["accepted_phrases"]),
                }
                for c in question["concepts"]
            ],
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise StoreError(f"cannot fingerprint malformed question: {exc}") from exc
    blob = json.dumps(canonical, sort_keys=True, ensure_ascii=True)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def snapshot_for_question(question: dict) -> dict:
    """Self-contained rubric snapshot so history stays interpretable."""
    try:
        return {
            "question_id": question["id"],
            "topic": question.get("topic", ""),
            "question_text": question.get("question_text", ""),
            "reference_answer": question.get("reference_answer", ""),
            "follow_up": question.get("follow_up", ""),
            "concepts": [
                {
                    "id": c["id"],
                    "label": c["label"],
                    "weight": float(c["weight"]),
                    "explanation": c.get("explanation", ""),
                    "accepted_phrases": list(c["accepted_phrases"]),
                }
                for c in question["concepts"]
            ],
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise StoreError(f"cannot snapshot malformed question: {exc}") from exc


@contextlib.contextmanager
def _db(path: Path):
    """Open a connection with explicit commit/rollback and reliable close."""
    try:
        conn = sqlite3.connect(str(path), timeout=10)
    except sqlite3.Error as exc:
        raise StoreError(f"cannot open database at {path}: {exc}") from exc
    try:
        yield conn
        conn.commit()
    except StoreError:
        conn.rollback()
        raise
    except sqlite3.Error as exc:
        conn.rollback()
        raise StoreError(f"database operation failed: {exc}") from exc
    finally:
        conn.close()


def init_db(path: str | Path | None = None) -> Path:
    """Create parent dirs, schema-meta, and attempts table if missing.

    Idempotent: running twice changes nothing. An existing database with an
    unknown schema version raises instead of being migrated or wiped.
    """
    resolved = resolve_db_path(path)
    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StoreError(f"cannot create database directory: {exc}") from exc
    with _db(resolved) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_meta "
            "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        row = conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO schema_meta (key, value) VALUES (?, ?)",
                ("schema_version", str(SCHEMA_VERSION)),
            )
        elif row[0] != str(SCHEMA_VERSION):
            raise SchemaError(
                f"database schema version {row[0]} is not supported "
                f"(this build reads {SCHEMA_VERSION}); refusing to migrate "
                f"or reset existing data"
            )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS attempts ("
            "id TEXT PRIMARY KEY, "
            "created_at TEXT NOT NULL, "
            "question_id TEXT NOT NULL, "
            "rubric_fingerprint TEXT NOT NULL, "
            "rubric_snapshot TEXT NOT NULL, "
            "evaluator_version TEXT NOT NULL, "
            "input_mode TEXT NOT NULL, "
            "reviewed_text TEXT NOT NULL, "
            "result_json TEXT NOT NULL, "
            "coverage_pct REAL NOT NULL, "
            "assisted INTEGER NOT NULL)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_attempts_question "
            "ON attempts (question_id, created_at, id)"
        )
    return resolved


def _validate_record(record: object) -> dict:
    if not isinstance(record, dict):
        raise StoreError(f"attempt record must be a dict, got {type(record).__name__}")
    for field in (
        "id", "created_at", "question_id", "rubric_fingerprint",
        "evaluator_version", "input_mode",
    ):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            raise StoreError(f"attempt record needs nonempty string '{field}'")
    if record["input_mode"] not in _INPUT_MODES:
        raise StoreError(
            f"attempt input_mode must be one of {list(_INPUT_MODES)}"
        )
    if not isinstance(record.get("rubric_snapshot"), dict):
        raise StoreError("attempt record needs a 'rubric_snapshot' object")
    if not isinstance(record.get("result"), dict):
        raise StoreError("attempt record needs a 'result' object")
    coverage = record.get("coverage_pct")
    if (
        isinstance(coverage, bool)
        or not isinstance(coverage, (int, float))
        or coverage != coverage  # NaN check without math import games
        or coverage in (float("inf"), float("-inf"))
    ):
        raise StoreError("attempt record needs a finite numeric 'coverage_pct'")
    if not isinstance(record.get("reviewed_text"), str):
        raise StoreError("attempt record needs string 'reviewed_text'")
    assisted = record.get("assisted", False)
    if not isinstance(assisted, (bool, int)):
        raise StoreError("attempt 'assisted' must be boolean")
    # The record schema carries text only — raw audio must never arrive here.
    for forbidden in ("audio", "audio_bytes", "audio_data", "recording"):
        if forbidden in record:
            raise StoreError(
                f"attempt record must never contain raw audio ('{forbidden}')"
            )
    return record


def save_attempt(path: str | Path | None, record: dict) -> tuple[bool, dict]:
    """Insert one attempt; duplicate ids return the stored row, unchanged.

    Returns (inserted, stored_record). A repeated save of the same attempt
    (Streamlit rerun/double-click) is therefore idempotent, while a genuinely
    new evaluation carries a new id and creates a new row.
    """
    record = _validate_record(record)
    resolved = resolve_db_path(path)
    init_db(resolved)
    row = (
        record["id"],
        record["created_at"],
        record["question_id"],
        record["rubric_fingerprint"],
        json.dumps(record["rubric_snapshot"], sort_keys=True),
        record["evaluator_version"],
        record["input_mode"],
        record["reviewed_text"],
        json.dumps(record["result"], sort_keys=True),
        float(record["coverage_pct"]),
        1 if record.get("assisted", False) else 0,
    )
    with _db(resolved) as conn:
        try:
            conn.execute(
                "INSERT INTO attempts (id, created_at, question_id, "
                "rubric_fingerprint, rubric_snapshot, evaluator_version, "
                "input_mode, reviewed_text, result_json, coverage_pct, "
                "assisted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )
        except sqlite3.IntegrityError:
            existing = get_attempt(resolved, record["id"])
            if existing is None:  # pragma: no cover - cannot happen, defensive
                raise StoreError("duplicate attempt vanished mid-save")
            return False, existing
    stored = get_attempt(resolved, record["id"])
    if stored is None:  # pragma: no cover - cannot happen, defensive
        raise StoreError("saved attempt could not be read back")
    return True, stored


def _parse_row(row: tuple) -> dict:
    values = dict(zip(_COLUMNS, row))
    where = f"attempt '{values.get('id')}'"
    try:
        snapshot = json.loads(values["rubric_snapshot"])
        result = json.loads(values["result_json"])
    except (json.JSONDecodeError, TypeError) as exc:
        raise StoredRecordError(f"{where}: stored JSON is corrupt: {exc}") from exc
    if not isinstance(snapshot, dict) or not isinstance(result, dict):
        raise StoredRecordError(f"{where}: stored JSON has wrong structure")
    try:
        coverage = float(values["coverage_pct"])
    except (TypeError, ValueError) as exc:
        raise StoredRecordError(f"{where}: stored coverage is invalid") from exc
    return {
        "id": values["id"],
        "created_at": values["created_at"],
        "question_id": values["question_id"],
        "rubric_fingerprint": values["rubric_fingerprint"],
        "rubric_snapshot": snapshot,
        "evaluator_version": values["evaluator_version"],
        "input_mode": values["input_mode"],
        "reviewed_text": values["reviewed_text"],
        "result": result,
        "coverage_pct": coverage,
        "assisted": bool(values["assisted"]),
    }


def list_attempts(
    path: str | Path | None, question_id: str | None = None
) -> list[dict]:
    """All attempts, oldest first; id tie-breaks identical timestamps."""
    resolved = resolve_db_path(path)
    init_db(resolved)
    with _db(resolved) as conn:
        try:
            if question_id is None:
                cursor = conn.execute(
                    f"SELECT {', '.join(_COLUMNS)} FROM attempts "
                    "ORDER BY created_at ASC, id ASC"
                )
            else:
                cursor = conn.execute(
                    f"SELECT {', '.join(_COLUMNS)} FROM attempts "
                    "WHERE question_id = ? ORDER BY created_at ASC, id ASC",
                    (question_id,),
                )
            rows = cursor.fetchall()
        except sqlite3.Error as exc:
            raise StoreError(f"cannot list attempts: {exc}") from exc
    return [_parse_row(row) for row in rows]


def get_attempt(path: str | Path | None, attempt_id: str) -> dict | None:
    """One attempt by id, or None; corrupt rows raise StoredRecordError."""
    resolved = resolve_db_path(path)
    init_db(resolved)
    with _db(resolved) as conn:
        try:
            row = conn.execute(
                f"SELECT {', '.join(_COLUMNS)} FROM attempts WHERE id = ?",
                (attempt_id,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise StoreError(f"cannot read attempt: {exc}") from exc
    return _parse_row(row) if row is not None else None


def delete_attempt(path: str | Path | None, attempt_id: str) -> bool:
    """Delete one attempt; True when a row was actually removed."""
    resolved = resolve_db_path(path)
    init_db(resolved)
    with _db(resolved) as conn:
        try:
            cursor = conn.execute(
                "DELETE FROM attempts WHERE id = ?", (attempt_id,)
            )
        except sqlite3.Error as exc:
            raise StoreError(f"cannot delete attempt: {exc}") from exc
        return cursor.rowcount > 0


def delete_all_attempts(path: str | Path | None) -> int:
    """Delete every attempt; returns the number of rows removed."""
    resolved = resolve_db_path(path)
    init_db(resolved)
    with _db(resolved) as conn:
        try:
            cursor = conn.execute("DELETE FROM attempts")
        except sqlite3.Error as exc:
            raise StoreError(f"cannot delete attempts: {exc}") from exc
        return cursor.rowcount


def _covered_ids(result: dict) -> dict[str, dict]:
    concepts = result.get("concepts", [])
    if not isinstance(concepts, list):
        raise StoredRecordError("stored result has malformed 'concepts'")
    return {
        c["concept_id"]: c
        for c in concepts
        if isinstance(c, dict) and c.get("status") == "covered"
    }


def compare_attempts(earlier: dict, later: dict) -> dict:
    """Compare two attempts of the SAME question without reinterpreting them.

    Coverage delta is reported in percentage points (never "percent
    improvement"). When rubric fingerprint or evaluator version differ, the
    direct delta is disabled with a warning instead of an invalid comparison.
    """
    if earlier["question_id"] != later["question_id"]:
        return {
            "comparable": False,
            "reason": "attempts are for different questions; comparison disabled",
            "earlier": _compare_side(earlier),
            "later": _compare_side(later),
            "coverage_delta_pp": None,
            "newly_covered": [],
            "regressed": [],
        }
    if (
        earlier["rubric_fingerprint"] != later["rubric_fingerprint"]
        or earlier["evaluator_version"] != later["evaluator_version"]
    ):
        return {
            "comparable": False,
            "reason": (
                "rubric or evaluator version differs between attempts; "
                "historical answers are not reinterpreted, so the direct "
                "delta is disabled"
            ),
            "earlier": _compare_side(earlier),
            "later": _compare_side(later),
            "coverage_delta_pp": None,
            "newly_covered": [],
            "regressed": [],
        }
    before = _covered_ids(earlier["result"])
    after = _covered_ids(later["result"])
    later_status = {
        c["concept_id"]: c.get("status")
        for c in later["result"].get("concepts", [])
        if isinstance(c, dict)
    }
    newly = [
        {"concept_id": cid, "label": after[cid].get("label", "")}
        for cid in sorted(set(after) - set(before))
    ]
    regressed = [
        {
            "concept_id": cid,
            "label": before[cid].get("label", ""),
            "later_status": later_status.get(cid),
        }
        for cid in sorted(set(before) - set(after))
    ]
    return {
        "comparable": True,
        "reason": "",
        "earlier": _compare_side(earlier),
        "later": _compare_side(later),
        "coverage_delta_pp": round(later["coverage_pct"] - earlier["coverage_pct"], 1),
        "newly_covered": newly,
        "regressed": regressed,
    }


def _compare_side(attempt: dict) -> dict:
    return {
        "id": attempt["id"],
        "created_at": attempt["created_at"],
        "coverage_pct": attempt["coverage_pct"],
        "input_mode": attempt["input_mode"],
        "assisted": attempt["assisted"],
    }
