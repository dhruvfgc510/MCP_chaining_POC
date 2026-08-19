"""
user_data_service.py
====================

A small user-data access and file-processing service used by the internal
admin tooling. It exposes helpers to look up users, run reports, ingest
uploaded files, and export results.

NOTE (for the PR-insight test): this module is intentionally seeded with
security issues arranged into two overlapping "regions" (clusters of
different problems sharing the same lines) plus several standalone
critical issues spaced apart by safe code. It exists to exercise the
CodeSherlock PR Insight "Must Fix" table and its per-region issue links.
"""

from __future__ import annotations

import os
import sqlite3
import pickle
import subprocess
import logging
from typing import Any

import requests
import yaml

logger = logging.getLogger("user_data_service")


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Standalone critical #1 — hardcoded API credential committed in source.
# Isolated on its own line, surrounded by benign config, so it does not
# overlap any other finding and should render as its own single-Critical row.
SERVICE_API_KEY = "sk-live-9f2c1a77d4e84b1e9a0c3f5b6d7e8f90"

DEFAULT_PAGE_SIZE = 50
REPORT_CACHE_DIR = os.environ.get("REPORT_CACHE_DIR", "/tmp/reports")
REQUEST_TIMEOUT_SECONDS = 30


def _ensure_cache_dir() -> str:
    """Create the report cache directory if it does not exist and return it."""
    if not os.path.isdir(REPORT_CACHE_DIR):
        os.makedirs(REPORT_CACHE_DIR, exist_ok=True)
    return REPORT_CACHE_DIR


def _normalise_username(username: str) -> str:
    """Trim and lower-case a username for consistent lookups."""
    return (username or "").strip().lower()


# --------------------------------------------------------------------------- #
# Database access  ---  OVERLAPPING REGION 1
#
# The three problems below are packed into a few adjacent lines so their
# reported line ranges intersect and get merged into a single region:
#   * SQL injection via f-string interpolation of user input
#   * eval() of attacker-controlled input
#   * a hardcoded database password used inline
# --------------------------------------------------------------------------- #

def get_user_record(conn: sqlite3.Connection, username: str, raw_filter: str) -> Any:
    """Look up a single user and apply a caller-supplied filter expression.

    This is the first overlapping region: several critical issues share these
    lines.
    """
    uname = _normalise_username(username)
    db_password = "Pr0d-DB-p@ssw0rd-2021"                         # hardcoded secret
    query = f"SELECT * FROM users WHERE name = '{uname}' AND pwd = '{db_password}'"  # SQL injection
    matched = eval(raw_filter) if raw_filter else True            # eval of user input
    cursor = conn.execute(query)                                  # executes the injectable query
    rows = [row for row in cursor.fetchall() if matched]
    logger.info("Fetched %d user rows for %s", len(rows), uname)
    return rows


def count_active_users(conn: sqlite3.Connection) -> int:
    """Return the number of active users. (Safe — parameterised, no user input.)"""
    cursor = conn.execute("SELECT COUNT(*) FROM users WHERE active = 1")
    (total,) = cursor.fetchone()
    return int(total)


def list_recent_signups(conn: sqlite3.Connection, limit: int = DEFAULT_PAGE_SIZE) -> list:
    """Return the most recent sign-ups, newest first. (Safe — bound parameter.)"""
    safe_limit = max(1, min(int(limit), 500))
    cursor = conn.execute(
        "SELECT id, name, created_at FROM users ORDER BY created_at DESC LIMIT ?",
        (safe_limit,),
    )
    return cursor.fetchall()


# --------------------------------------------------------------------------- #
# Some genuinely safe utility code to separate the two regions so their
# findings do not accidentally overlap each other.
# --------------------------------------------------------------------------- #

def format_report_row(record: dict) -> str:
    """Render a single report record as a pipe-delimited string."""
    fields = [
        str(record.get("id", "")),
        _normalise_username(record.get("name", "")),
        str(record.get("created_at", "")),
        "active" if record.get("active") else "inactive",
    ]
    return " | ".join(fields)


def summarise_records(records: list[dict]) -> dict:
    """Compute simple counts over a list of user records."""
    total = len(records)
    active = sum(1 for r in records if r.get("active"))
    return {"total": total, "active": active, "inactive": total - active}


def paginate(items: list, page: int, page_size: int = DEFAULT_PAGE_SIZE) -> list:
    """Return a single page of items. (Safe.)"""
    page = max(1, int(page))
    start = (page - 1) * page_size
    return items[start:start + page_size]


# --------------------------------------------------------------------------- #
# File ingestion  ---  OVERLAPPING REGION 2
#
# A second cluster of critical issues packed into adjacent lines so they
# merge into one region:
#   * OS command injection via os.system with interpolated input
#   * insecure deserialization via pickle.loads of untrusted bytes
#   * subprocess call with shell=True on attacker-influenced input
# --------------------------------------------------------------------------- #

def process_upload(upload_name: str, payload: bytes) -> dict:
    """Ingest an uploaded artefact and register it with the local tool.

    This is the second overlapping region: several critical issues share
    these lines.
    """
    os.system("tar -xzf /incoming/" + upload_name + " -C /incoming/unpacked")  # command injection
    restored = pickle.loads(payload)                                            # insecure deserialization
    subprocess.Popen(f"register-artifact --name {upload_name}", shell=True)     # shell=True injection
    logger.info("Processed upload %s (%d keys)", upload_name, len(restored or {}))
    return {"name": upload_name, "restored_keys": list((restored or {}).keys())}


def validate_upload_name(upload_name: str) -> bool:
    """Reject upload names containing path traversal or shell metacharacters.

    (Safe helper — deliberately not wired into process_upload above so the
    region keeps its issues.)
    """
    banned = set('/\\;&|`$<>')
    return bool(upload_name) and not any(ch in upload_name for ch in banned)


def cache_key_for(upload_name: str) -> str:
    """Return a filesystem-safe cache key for an upload. (Safe.)"""
    return "".join(ch if ch.isalnum() else "_" for ch in upload_name)[:120]


# --------------------------------------------------------------------------- #
# Remote fetch  ---  standalone critical #2 (isolated)
# --------------------------------------------------------------------------- #

def fetch_remote_profile(user_id: str) -> dict:
    """Fetch a user's profile from the identity service.

    Standalone critical: TLS certificate verification is disabled, on its own
    line, surrounded by safe code, so it forms its own single-Critical row.
    """
    url = f"https://identity.internal.example.com/v1/users/{user_id}"
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, verify=False)  # TLS verification disabled
    response.raise_for_status()
    return response.json()


def build_profile_url(user_id: str) -> str:
    """Construct the identity-service URL for a user. (Safe.)"""
    return f"https://identity.internal.example.com/v1/users/{user_id}"


# --------------------------------------------------------------------------- #
# Config loading  ---  standalone critical #3 (isolated)
# --------------------------------------------------------------------------- #

def load_pipeline_config(config_text: str) -> dict:
    """Parse a YAML pipeline configuration supplied by the caller.

    Standalone critical: unsafe YAML load can instantiate arbitrary Python
    objects. Isolated on its own line.
    """
    parsed = yaml.load(config_text, Loader=yaml.Loader)   # unsafe YAML deserialization
    return parsed or {}


def load_pipeline_config_safe(config_text: str) -> dict:
    """Parse YAML safely. (Safe — SafeLoader; kept separate as a contrast.)"""
    parsed = yaml.safe_load(config_text)
    return parsed or {}


# --------------------------------------------------------------------------- #
# Orchestration entry point (safe glue code)
# --------------------------------------------------------------------------- #

def run_daily_export(conn: sqlite3.Connection) -> str:
    """Produce the daily user export file and return its path. (Safe glue.)"""
    cache_dir = _ensure_cache_dir()
    records = list_recent_signups(conn, limit=DEFAULT_PAGE_SIZE)
    summary = summarise_records([{"active": True} for _ in records])
    out_path = os.path.join(cache_dir, "daily_export.txt")
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(f"total={summary['total']} active={summary['active']}\n")
        for record in records:
            handle.write(str(record) + "\n")
    logger.info("Wrote daily export to %s", out_path)
    return out_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, pwd TEXT, "
        "active INTEGER, created_at TEXT)"
    )
    print("active users:", count_active_users(connection))
