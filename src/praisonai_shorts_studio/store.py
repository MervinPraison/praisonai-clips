from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path


def digest_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{uuid.uuid4().hex}.tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


class Cancelled(Exception):
    pass


class Store:
    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = self.root / "jobs.sqlite3"
        with self.connect() as con:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("""CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, source TEXT NOT NULL, fingerprint TEXT NOT NULL,
                config TEXT NOT NULL, status TEXT NOT NULL, stage TEXT NOT NULL,
                cancel INTEGER NOT NULL DEFAULT 0, error TEXT,
                created REAL NOT NULL, updated REAL NOT NULL)""")

    def connect(self):
        con = sqlite3.connect(self.db, timeout=30)
        con.row_factory = sqlite3.Row
        return con

    def create(self, source: Path, config: dict):
        source = source.resolve(strict=True)
        job_id = uuid.uuid4().hex[:16]
        now = time.time()
        with self.connect() as con:
            con.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,0,NULL,?,?)",
                        (job_id, str(source), digest_file(source), json.dumps(config),
                         "pending", "created", now, now))
        self.job_dir(job_id).mkdir(parents=True)
        return job_id

    def job_dir(self, job_id):
        # IDs are generated locally, never paths supplied by API/model output.
        if len(job_id) != 16 or any(c not in "0123456789abcdef" for c in job_id):
            raise ValueError("Invalid job ID")
        return self.root / "jobs" / job_id

    def get(self, job_id):
        with self.connect() as con:
            row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise ValueError("Job does not exist")
        return dict(row)

    def list(self):
        with self.connect() as con:
            return [dict(r) for r in con.execute("SELECT * FROM jobs ORDER BY created DESC")]

    def update(self, job_id, **values):
        allowed = {"status", "stage", "cancel", "error"}
        if not values or not set(values) <= allowed:
            raise ValueError("Invalid job update")
        values["updated"] = time.time()
        with self.connect() as con:
            con.execute("UPDATE jobs SET " + ",".join(f"{k}=?" for k in values) + " WHERE id=?",
                        (*values.values(), job_id))

    def check(self, job_id):
        if self.get(job_id)["cancel"]:
            raise Cancelled("Cancellation requested")

    def cache(self, job_id, name, inputs, compute):
        self.check(job_id)
        signature = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
        path = self.job_dir(job_id) / "cache" / f"{name}-{signature}.json"
        if path.exists():
            return json.loads(path.read_text())
        self.update(job_id, stage=name)
        result = compute()
        # Preserve completed, billed requests even if cancellation arrived during the call.
        write_json(path, result)
        self.check(job_id)
        return result
