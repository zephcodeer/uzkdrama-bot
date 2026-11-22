"""Publish a consistent local catalog snapshot for the hosted bot to pull."""

import base64
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile


REPO = "zephcodeer/uzkdrama-bot"
BRANCH = "main"
EXPECTED_DB_PATH = Path(__file__).resolve().parent.parent / "doramas.db"


def _run(args, *, cwd, input_text=None):
    result = subprocess.run(
        args,
        cwd=cwd,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    if result.returncode:
        raise RuntimeError(f"{args[0]} exited with code {result.returncode}: {result.stderr.strip()[:300]}")
    return result.stdout.strip()


def _logical_digest(db_path: Path) -> str:
    digest = hashlib.sha256()
    with closing(sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)) as db:
        for statement in db.iterdump():
            digest.update(statement.encode("utf-8"))
            digest.update(b"\n")
    return digest.hexdigest()


def publish_catalog_snapshot(db_path: Path) -> bool:
    """Return True when a new doramas.db commit was published to GitHub."""
    db_path = Path(db_path)
    if db_path.resolve() != EXPECTED_DB_PATH.resolve():
        raise ValueError("Refusing to publish a database outside the production catalog path")
    project_dir = db_path.parent
    endpoint = f"repos/{REPO}/contents/doramas.db"

    with tempfile.TemporaryDirectory(prefix="catalog-sync-", dir=project_dir) as tmp:
        snapshot = Path(tmp) / "doramas.db"
        with closing(sqlite3.connect(str(db_path), timeout=30)) as source:
            with closing(sqlite3.connect(str(snapshot))) as target:
                source.backup(target)

        local_digest = _logical_digest(snapshot)
        content = base64.b64encode(snapshot.read_bytes()).decode("ascii")

        for attempt in range(3):
            remote = json.loads(_run(["gh", "api", f"{endpoint}?ref={BRANCH}"], cwd=project_dir))
            if not remote.get("content"):
                raise RuntimeError("GitHub catalog content is unavailable for comparison")
            remote_path = Path(tmp) / "remote.db"
            remote_path.write_bytes(base64.b64decode(remote["content"]))
            if _logical_digest(remote_path) == local_digest:
                return False

            payload = json.dumps(
                {
                    "message": "chore(catalog): publish autopilot episodes",
                    "content": content,
                    "sha": remote["sha"],
                    "branch": BRANCH,
                }
            )
            try:
                _run(["gh", "api", "--method", "PUT", endpoint, "--input", "-"], cwd=project_dir, input_text=payload)
                return True
            except RuntimeError as exc:
                if attempt == 2 or not any(code in str(exc) for code in ("409", "422")):
                    raise

    raise RuntimeError("Catalog publish could not resolve a concurrent GitHub update")
