"""Create a reproducible, non-destructive repository inventory."""
from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


GENERATED_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp"}
DATA_SUFFIXES = {".csv", ".xlsx", ".xls", ".json", ".jsonl", ".parquet", ".geojson"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_status(root: Path) -> dict[str, str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"], cwd=root,
        check=True, capture_output=True,
    )
    entries: dict[str, str] = {}
    parts = result.stdout.decode("utf-8", errors="replace").split("\0")
    index = 0
    while index < len(parts) and parts[index]:
        item = parts[index]
        status, path = item[:2], item[3:]
        entries[path.replace("\\", "/")] = status
        if status[0] in {"R", "C"}:
            index += 1
        index += 1
    return entries


def purpose_for(relative: str, suffix: str) -> str:
    normalized = relative.replace("\\", "/").lower()
    if "/__pycache__/" in f"/{normalized}" or suffix in GENERATED_SUFFIXES:
        return "generated cache"
    if suffix in {".ipynb"}:
        return "notebook"
    if suffix in DATA_SUFFIXES:
        if "checkpoint" in normalized:
            return "scraper checkpoint"
        if "error" in normalized:
            return "scraping error log"
        if "report" in normalized:
            return "generated report"
        return "dataset or geographic artifact"
    if suffix == ".py":
        return "Python source or test"
    if suffix in {".md", ".txt"}:
        return "documentation or dependency manifest"
    if suffix in {".html", ".css", ".js"}:
        return "application source"
    return "project file"


def recommendation(relative: str, purpose: str, duplicates: int) -> str:
    normalized = relative.replace("\\", "/").lower()
    if purpose == "generated cache":
        return "archive_then_delete"
    if normalized.startswith("ml/notebooks/data/"):
        return "move_to_canonical_data_archive_source"
    if normalized.endswith("data_maisondelux_fast_resume.ipynb") or normalized.endswith("data_maisondelux_scraper.ipynb"):
        return "archive_after_master_notebook_created"
    if duplicates > 1 and purpose in {"dataset or geographic artifact", "scraper checkpoint"}:
        return "preserve_one_archive_redundant_copies"
    return "preserve"


def create_inventory(root: Path, csv_path: Path, md_path: Path) -> list[dict[str, object]]:
    statuses = git_status(root)
    files = [
        path for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
        and "outputs" not in path.relative_to(root).parts
    ]
    hash_groups: dict[str, list[str]] = defaultdict(list)
    metadata: list[tuple[Path, str]] = []
    for path in files:
        digest = sha256(path)
        relative = path.relative_to(root).as_posix()
        hash_groups[digest].append(relative)
        metadata.append((path, digest))

    rows: list[dict[str, object]] = []
    for path, digest in sorted(metadata, key=lambda item: item[0].as_posix().lower()):
        relative = path.relative_to(root).as_posix()
        suffix = path.suffix.lower() or "[none]"
        purpose = purpose_for(relative, suffix)
        copies = len(hash_groups[digest])
        rows.append({
            "current_path": relative,
            "file_type": suffix,
            "size_bytes": path.stat().st_size,
            "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            "git_status": statuses.get(relative, "tracked_clean_or_ignored"),
            "sha256": digest,
            "duplicate_count": copies,
            "duplicate_paths": " | ".join(hash_groups[digest]) if copies > 1 else "",
            "purpose": purpose,
            "recommended_action": recommendation(relative, purpose, copies),
        })

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(row["recommended_action"] for row in rows)
    duplicate_sets = {digest: paths for digest, paths in hash_groups.items() if len(paths) > 1}
    lines = [
        "# MaisonDeLUX repository inventory",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Files inspected: {len(rows)}",
        f"Duplicate content groups: {len(duplicate_sets)}",
        "",
        "## Recommended actions",
        "",
        "| Action | Files |",
        "|---|---:|",
        *[f"| `{action}` | {count} |" for action, count in sorted(counts.items())],
        "",
        "The CSV beside this report is the authoritative row-level inventory. Pre-existing Git modifications and deletions are recorded but never reverted by this audit.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--name", default="repository_inventory", help="Output stem under reports/inventory")
    args = parser.parse_args()
    root = args.root.resolve()
    rows = create_inventory(
        root,
        root / "reports" / "inventory" / f"{args.name}.csv",
        root / "reports" / "inventory" / f"{args.name}.md",
    )
    print(f"inventoried_files={len(rows)}")


if __name__ == "__main__":
    main()
