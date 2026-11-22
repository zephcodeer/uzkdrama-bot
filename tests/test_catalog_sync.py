import base64
import json
import sqlite3
from unittest.mock import patch

import pytest

from scripts.catalog_sync import publish_catalog_snapshot


def test_catalog_sync_rejects_nonproduction_database(tmp_path):
    with pytest.raises(ValueError, match="production catalog path"):
        publish_catalog_snapshot(tmp_path / "test.db")


def test_catalog_sync_skips_unchanged_snapshot(tmp_path):
    db_path = tmp_path / "doramas.db"
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE episodes (id INTEGER)")

    def fake_run(args, *, cwd, input_text=None):
        if args[:2] == ["gh", "api"]:
            assert input_text is None
            return json.dumps({"sha": "same-sha", "content": base64.b64encode(db_path.read_bytes()).decode("ascii")})
        raise AssertionError(f"Unexpected command: {args}")

    with patch("scripts.catalog_sync.EXPECTED_DB_PATH", db_path), patch("scripts.catalog_sync._run", side_effect=fake_run) as run:
        assert publish_catalog_snapshot(db_path) is False
        assert run.call_count == 1


def test_catalog_sync_publishes_consistent_database_snapshot(tmp_path):
    db_path = tmp_path / "doramas.db"
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE episodes (id INTEGER)")
        db.execute("INSERT INTO episodes VALUES (17)")
    remote_path = tmp_path / "remote.db"
    with sqlite3.connect(remote_path) as db:
        db.execute("CREATE TABLE episodes (id INTEGER)")

    def fake_run(args, *, cwd, input_text=None):
        if args[:2] == ["gh", "api"] and "--method" not in args:
            return json.dumps({"sha": "old-sha", "content": base64.b64encode(remote_path.read_bytes()).decode("ascii")})
        if "--method" in args:
            payload = json.loads(input_text)
            assert payload["sha"] == "old-sha"
            assert payload["branch"] == "main"
            assert base64.b64decode(payload["content"]).startswith(b"SQLite format 3")
            return "updated"
        raise AssertionError(f"Unexpected command: {args}")

    with patch("scripts.catalog_sync.EXPECTED_DB_PATH", db_path), patch("scripts.catalog_sync._run", side_effect=fake_run):
        assert publish_catalog_snapshot(db_path) is True
