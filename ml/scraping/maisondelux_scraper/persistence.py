"""Crash-safe CSV checkpoints and listing identity helpers."""
from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[3]
SRC_DIR = REPO_ROOT / "ml" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from data_schema import SCHEMA_V3_COLUMNS, canonicalize_url  # noqa: E402


LISTING_RE = re.compile(r"/a/(\d+)(?:/|$)")


def native_id_from_url(url: str | None) -> str | None:
    if not url:
        return None
    match = LISTING_RE.search(str(url))
    return match.group(1) if match else None


def identity_keys(
    *,
    listing_id: Any = None,
    native_id: Any = None,
    url: Any = None,
    source: str = "mubawab.ma",
) -> set[str]:
    """Return every stable identity available for conservative deduplication."""
    keys: set[str] = set()

    if listing_id is not None and str(listing_id).strip():
        keys.add(f"listing:{str(listing_id).strip()}")

    normalized_native = None
    if native_id is not None and str(native_id).strip():
        normalized_native = str(native_id).strip()
    elif url:
        normalized_native = native_id_from_url(str(url))

    if normalized_native:
        keys.add(f"native:{source.casefold()}:{normalized_native}")
        keys.add(f"listing:{source.casefold()}:native:{normalized_native}")

    canonical = canonicalize_url(str(url)) if url else None
    if canonical:
        keys.add(f"url:{canonical}")

    return keys


def _upgrade_schema(path: Path, columns: list[str]) -> None:
    """Add newly introduced columns without dropping or changing existing rows."""
    temporary = path.with_name(f".{path.name}.schema-upgrade.tmp")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        existing = reader.fieldnames
        if not existing:
            raise ValueError(f"Existing output has no CSV header: {path}")
        if existing == columns:
            return

        unexpected = [column for column in existing if column not in columns]
        if unexpected:
            raise ValueError(
                f"Existing output has unsupported columns {unexpected!r}; "
                f"choose a different --output instead of overwriting {path}"
            )

        try:
            with temporary.open("w", encoding="utf-8-sig", newline="") as target:
                writer = csv.DictWriter(target, fieldnames=columns, extrasaction="ignore")
                writer.writeheader()
                for row in reader:
                    writer.writerow({column: row.get(column) for column in columns})
                target.flush()
                os.fsync(target.fileno())
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    # Windows requires the source handle above to be closed before replacement.
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_identity_index(path: Path) -> tuple[set[str], int]:
    """Load native-ID and canonical-URL keys from an existing checkpoint."""
    if not path.exists() or path.stat().st_size == 0:
        return set(), 0

    keys: set[str] = set()
    rows = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Existing output has no CSV header: {path}")
        required_identity = {"listing_id", "url"}
        if not required_identity.intersection(reader.fieldnames):
            raise ValueError(
                f"Existing output must contain listing_id or url for resume: {path}"
            )
        for row in reader:
            rows += 1
            keys.update(
                identity_keys(
                    listing_id=row.get("listing_id"),
                    url=row.get("url"),
                    source=row.get("source") or "mubawab.ma",
                )
            )
    return keys, rows


class CheckpointCsvStore:
    """Append rows immediately while preserving an existing collection."""

    def __init__(self, path: Path, columns: Iterable[str] = SCHEMA_V3_COLUMNS):
        self.path = path
        self.columns = list(columns)
        self.known_keys: set[str] = set()
        self.existing_rows = 0
        self.rows_written = 0
        self._handle = None
        self._writer: csv.DictWriter | None = None

    def open(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and self.path.stat().st_size:
            _upgrade_schema(self.path, self.columns)
        self.known_keys, self.existing_rows = load_identity_index(self.path)

        write_header = not self.path.exists() or self.path.stat().st_size == 0
        self._handle = self.path.open("a", encoding="utf-8-sig", newline="")
        self._writer = csv.DictWriter(
            self._handle,
            fieldnames=self.columns,
            extrasaction="ignore",
        )
        if write_header:
            self._writer.writeheader()
            self._checkpoint()

    def append(self, record: Mapping[str, Any]) -> bool:
        if self._writer is None:
            raise RuntimeError("CheckpointCsvStore.open() must be called before append()")

        keys = identity_keys(
            listing_id=record.get("listing_id"),
            url=record.get("url"),
            source=str(record.get("source") or "mubawab.ma"),
        )
        if keys and keys.intersection(self.known_keys):
            return False

        self._writer.writerow({column: record.get(column) for column in self.columns})
        self._checkpoint()
        self.known_keys.update(keys)
        self.rows_written += 1
        return True

    def _checkpoint(self) -> None:
        if self._handle is None:
            return
        self._handle.flush()
        os.fsync(self._handle.fileno())

    def close(self) -> None:
        if self._handle is not None:
            self._checkpoint()
            self._handle.close()
        self._handle = None
        self._writer = None


__all__ = [
    "CheckpointCsvStore",
    "identity_keys",
    "load_identity_index",
    "native_id_from_url",
]
