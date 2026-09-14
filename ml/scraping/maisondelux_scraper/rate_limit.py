"""Persistent cooldown state used after an HTTP 429 response."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any


def parse_retry_after(value: str | bytes | None, *, now: datetime | None = None) -> int | None:
    """Parse Retry-After seconds or an HTTP date without guessing."""
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("ascii", errors="ignore")
    text = value.strip()
    if not text:
        return None
    if text.isdigit():
        return max(0, int(text))
    try:
        retry_at = parsedate_to_datetime(text)
    except (TypeError, ValueError, OverflowError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    reference = now or datetime.now(timezone.utc)
    return max(0, int((retry_at.astimezone(timezone.utc) - reference).total_seconds()))


def write_cooldown(
    path: Path,
    *,
    pause_seconds: int,
    url: str,
    retry_after_header: str | None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    payload = {
        "rate_limited_at": now.isoformat(),
        "resume_after": (now + timedelta(seconds=max(0, pause_seconds))).isoformat(),
        "pause_seconds": max(0, pause_seconds),
        "url": url,
        "retry_after_header": retry_after_header,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return payload


def active_cooldown(path: Path, *, now: datetime | None = None) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        resume_after = datetime.fromisoformat(str(payload["resume_after"]).replace("Z", "+00:00"))
        if resume_after.tzinfo is None:
            resume_after = resume_after.replace(tzinfo=timezone.utc)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        # A malformed marker is kept for manual inspection and blocks collection.
        return {"invalid": True, "path": str(path)}

    reference = now or datetime.now(timezone.utc)
    remaining = int((resume_after.astimezone(timezone.utc) - reference).total_seconds())
    if remaining > 0:
        payload["remaining_seconds"] = remaining
        return payload

    path.unlink(missing_ok=True)
    return None


__all__ = ["active_cooldown", "parse_retry_after", "write_cooldown"]
