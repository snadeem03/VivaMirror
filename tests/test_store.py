"""Tests for SQLite attempt history (US-08).

Temporary databases only — the real local database is never touched.
All answers below are fictional practice sentences, never student data.
"""

import json
import sqlite3

import pytest

from app import store
from app.evaluation import EVALUATOR_VERSION, evaluate_answer
from app.questions import load_question_bank
from app.store import (
    SchemaError,
    StoredRecordError,
    StoreError,
    compare_attempts,
    default_db_path,
    delete_all_attempts,
    delete_attempt,
    fingerprint_for_question,
    get_attempt,
    init_db,
    list_attempts,
    resolve_db_path,
    save_attempt,
    snapshot_for_question,
)


@pytest.fixture(scope="module")
def question():
    bank = load_question_bank()
    return next(q for q in bank if q["id"] == "ds-15")


def _record(question, reviewed, created_at, attempt_id,
            mode="typed", assisted=False):
    result = evaluate_answer(question, reviewed)
    return {
        "id": attempt_id,
        "created_at": created_at,
        "question_id": question["id"],
        "rubric_fingerprint": fingerprint_for_question(question),
        "rubric_snapshot": snapshot_for_question(question),
        "evaluator_version": EVALUATOR_VERSION,
        "input_mode": mode,
        "reviewed_text": reviewed,
        "result": result,
        "coverage_pct": result["coverage_pct"],
        "assisted": assisted,
    }


# --- Initialization -------------------------------------------------------------------------------


def test_init_is_idempotent_and_records_schema_version(tmp_path):
    db = tmp_path / "sub" / "history.db"
    assert init_db(db) == db
    assert init_db(db) == db  # second run changes nothing
    conn = sqlite3.connect(str(db))
    try:
        version = conn.execute(
            "SELECT value FROM schema_meta WHERE key='schema_version'"
        ).fetchone()[0]
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()
    assert version == str(store.SCHEMA_VERSION)
    assert {"attempts", "schema_meta"} <= tables


def test_unknown_schema_version_is_rejected_not_reset(tmp_path):
    db = tmp_path / "old.db"
    init_db(db)
    conn = sqlite3.connect(str(db))
    try:
        conn.execute("UPDATE schema_meta SET value='999' WHERE key='schema_version'")
        conn.commit()
    finally:
        conn.close()
    with pytest.raises(SchemaError, match="not supported"):
        init_db(db)
    # Data path still intact and readable as far as sqlite is concerned.
    assert db.exists()


def test_database_error_is_clear_not_a_crash(tmp_path):
    with pytest.raises(StoreError, match="cannot open database"):
        init_db(tmp_path)  # a directory, not a file


def test_default_path_is_ignored_local_runtime_data(monkeypatch, tmp_path):
    assert default_db_path().parent.name == "local"
    assert default_db_path().suffix == ".db"
    monkeypatch.chdir(tmp_path)  # default path ignores the working directory
    assert resolve_db_path(None) == default_db_path()


# --- Round-trips -------------------------------------------------------------------------------------


def test_round_trip_preserves_full_attempt(question, tmp_path):
    db = tmp_path / "history.db"
    reviewed = "Since network splits will eventually happen, I must choose."
    record = _record(question, reviewed, "2026-10-09T01:50:00+00:00", "a1",
                     mode="spoken", assisted=True)
    inserted, stored = save_attempt(db, record)
    assert inserted is True
    assert stored["id"] == "a1"
    assert stored["reviewed_text"] == reviewed
    assert stored["coverage_pct"] == pytest.approx(30.0)
    assert stored["input_mode"] == "spoken"
    assert stored["assisted"] is True
    assert stored["evaluator_version"] == EVALUATOR_VERSION
    assert stored["rubric_snapshot"]["question_id"] == "ds-15"
    assert len(stored["rubric_snapshot"]["concepts"]) == 4
    assert stored["result"]["coverage_pct"] == stored["coverage_pct"]


def test_stable_save_id_prevents_duplicates(question, tmp_path):
    db = tmp_path / "history.db"
    first = _record(question, "Network splits will eventually happen.",
                    "2026-10-09T01:50:00+00:00", "dup-id")
    inserted, _ = save_attempt(db, first)
    assert inserted is True
    # A rerun/double-click retries with the SAME id but altered content:
    # the stored row must come back unchanged, not rewritten.
    retry = dict(first, reviewed_text="totally different text",
                 coverage_pct=100.0)
    inserted, stored = save_attempt(db, retry)
    assert inserted is False
    assert stored["reviewed_text"] == "Network splits will eventually happen."
    assert stored["coverage_pct"] == pytest.approx(30.0)
    assert len(list_attempts(db)) == 1


def test_separate_evaluations_create_separate_attempts(question, tmp_path):
    db = tmp_path / "history.db"
    save_attempt(db, _record(question, "Network splits will eventually happen.",
                             "2026-10-09T01:50:00+00:00", "id-1"))
    save_attempt(db, _record(question, "Without partitions all three hold.",
                             "2026-10-09T01:51:00+00:00", "id-2"))
    assert [a["id"] for a in list_attempts(db)] == ["id-1", "id-2"]


def test_chronological_ordering_with_deterministic_tiebreak(question, tmp_path):
    db = tmp_path / "history.db"
    save_attempt(db, _record(question, "Network splits will eventually happen.",
                             "2026-10-09T01:52:00+00:00", "id-b"))
    save_attempt(db, _record(question, "Without partitions all three hold.",
                             "2026-10-09T01:50:00+00:00", "id-a"))
    save_attempt(db, _record(question, "Network splits will eventually happen.",
                             "2026-10-09T01:50:00+00:00", "id-0"))
    assert [a["id"] for a in list_attempts(db)] == ["id-0", "id-a", "id-b"]


def test_question_filtering(question, tmp_path):
    db = tmp_path / "history.db"
    save_attempt(db, _record(question, "Network splits will eventually happen.",
                             "2026-10-09T01:50:00+00:00", "q1"))
    other = next(q for q in load_question_bank() if q["id"] == "ds-01")
    save_attempt(db, _record(other, "A collection of autonomous nodes.",
                             "2026-10-09T01:51:00+00:00", "q2"))
    assert [a["id"] for a in list_attempts(db, "ds-15")] == ["q1"]
    assert [a["id"] for a in list_attempts(db, "ds-01")] == ["q2"]
    assert len(list_attempts(db)) == 2


def test_sql_looking_text_is_data_not_code(question, tmp_path):
    db = tmp_path / "history.db"
    evil = "'; DROP TABLE attempts; --"
    save_attempt(db, _record(question, evil, "2026-10-09T01:50:00+00:00", "evil"))
    stored = get_attempt(db, "evil")
    assert stored["reviewed_text"] == evil
    assert len(list_attempts(db)) == 1  # table intact


def test_get_missing_attempt_returns_none(tmp_path):
    assert get_attempt(tmp_path / "history.db", "nope") is None


# --- Deletion --------------------------------------------------------------------------------------------


def test_delete_one_attempt(question, tmp_path):
    db = tmp_path / "history.db"
    save_attempt(db, _record(question, "Network splits will eventually happen.",
                             "2026-10-09T01:50:00+00:00", "keep"))
    save_attempt(db, _record(question, "Without partitions all three hold.",
                             "2026-10-09T01:51:00+00:00", "drop"))
    assert delete_attempt(db, "drop") is True
    assert delete_attempt(db, "drop") is False
    assert [a["id"] for a in list_attempts(db)] == ["keep"]


def test_delete_all_attempts(question, tmp_path):
    db = tmp_path / "history.db"
    save_attempt(db, _record(question, "Network splits will eventually happen.",
                             "2026-10-09T01:50:00+00:00", "x1"))
    save_attempt(db, _record(question, "Without partitions all three hold.",
                             "2026-10-09T01:51:00+00:00", "x2"))
    assert delete_all_attempts(db) == 2
    assert list_attempts(db) == []
    assert delete_all_attempts(db) == 0


# --- Privacy: never audio -------------------------------------------------------------------------------


def test_raw_audio_is_refused_not_stored(question, tmp_path):
    db = tmp_path / "history.db"
    record = _record(question, "Network splits will eventually happen.",
                     "2026-10-09T01:50:00+00:00", "audio-probe")
    for key in ("audio", "audio_bytes", "audio_data", "recording"):
        bad = dict(record, **{key: b"\x01\x02"})
        with pytest.raises(StoreError, match="never contain raw audio"):
            save_attempt(db, bad)
    assert list_attempts(db) == []


def test_stored_payload_contains_no_audio_keys(question, tmp_path):
    db = tmp_path / "history.db"
    save_attempt(db, _record(question, "Network splits will eventually happen.",
                             "2026-10-09T01:50:00+00:00", "clean"))
    stored = get_attempt(db, "clean")
    blob = json.dumps(stored)
    assert "audio" not in blob


# --- Corrupt data ---------------------------------------------------------------------------------------------


def test_corrupt_stored_json_raises_identifying_error(question, tmp_path):
    db = tmp_path / "history.db"
    init_db(db)
    conn = sqlite3.connect(str(db))
    try:
        conn.execute(
            "INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            ("broken", "2026-10-09T01:50:00+00:00", "ds-15", "fp", "{}",
             "1", "typed", "text", "{not json", 0.0, 0),
        )
        conn.commit()
    finally:
        conn.close()
    with pytest.raises(StoredRecordError, match="attempt 'broken'"):
        get_attempt(db, "broken")
    # The database itself is untouched; nothing was deleted or reset.
    assert db.exists()


# --- Comparison ---------------------------------------------------------------------------------------------------


def _two_attempts(question):
    thin = _record(question, "Network splits will eventually happen.",
                   "2026-10-09T01:50:00+00:00", "thin")
    full = _record(
        question,
        "Since network splits will eventually happen, I must choose between "
        "consistency and availability; the trade-off applies during a "
        "partition. My CP design will refuse minority-side writes and "
        "reconcile divergent replicas afterwards, because without partitions "
        "all three hold and the pick-two slogan is misleading.",
        "2026-10-09T01:55:00+00:00", "full")
    return thin, full


def test_same_question_comparison_and_percentage_points(question):
    thin, full = _two_attempts(question)
    assert (thin["coverage_pct"], full["coverage_pct"]) == (30.0, 100.0)
    result = compare_attempts(thin, full)
    assert result["comparable"] is True
    assert result["coverage_delta_pp"] == 70.0  # points, not percent
    assert {c["concept_id"] for c in result["newly_covered"]} == {
        "ds-15-c2", "ds-15-c3", "ds-15-c4"}
    assert result["regressed"] == []
    assert result["earlier"]["id"] == "thin"
    assert result["later"]["id"] == "full"


def test_regressed_concepts_reported_with_later_status(question):
    thin, full = _two_attempts(question)
    result = compare_attempts(full, thin)  # later attempt is weaker
    assert result["coverage_delta_pp"] == -70.0
    assert result["newly_covered"] == []
    assert {c["concept_id"] for c in result["regressed"]} == {
        "ds-15-c2", "ds-15-c3", "ds-15-c4"}


def test_version_mismatch_disables_delta(question):
    thin, full = _two_attempts(question)
    full = dict(full, evaluator_version="999")
    result = compare_attempts(thin, full)
    assert result["comparable"] is False
    assert result["coverage_delta_pp"] is None
    assert "version" in result["reason"]
    assert result["earlier"]["coverage_pct"] == 30.0
    assert result["later"]["coverage_pct"] == 100.0


def test_cross_question_comparison_disabled(question):
    thin, _ = _two_attempts(question)
    other = next(q for q in load_question_bank() if q["id"] == "ds-01")
    foreign = _record(other, "A collection of autonomous nodes.",
                      "2026-10-09T01:56:00+00:00", "foreign")
    result = compare_attempts(thin, foreign)
    assert result["comparable"] is False
    assert result["coverage_delta_pp"] is None
