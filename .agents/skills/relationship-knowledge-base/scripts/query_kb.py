"""Build the local index when needed and emit a retrieval context bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from ensure_kb import ensure_repository


FINGERPRINT_VERSION = b"relationship-knowledge-base-index-v1\0"


def _tracked_inputs(root: Path) -> list[Path]:
    config_path = root / "kbconfig.json"
    inputs = [config_path]
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read kbconfig.json: {exc}") from exc
    for directory in config.get("content_directories", []):
        content_root = root / str(directory)
        if content_root.is_dir():
            inputs.extend(content_root.rglob("*.md"))
    source_root = root / "src" / "relationship_kb"
    if source_root.is_dir():
        inputs.extend(source_root.rglob("*.py"))
    return sorted(set(inputs), key=lambda path: path.relative_to(root).as_posix())


def _input_fingerprint(root: Path) -> str:
    digest = hashlib.sha256(FINGERPRINT_VERSION)
    for path in _tracked_inputs(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _index_is_stale(root: Path) -> bool:
    database = root / "index" / "knowledge.db"
    manifest = root / "index" / "manifest.json"
    fingerprint_path = root / "index" / "skill-inputs.sha256"
    if not database.exists() or not manifest.exists() or not fingerprint_path.exists():
        return True
    try:
        metadata = json.loads(manifest.read_text(encoding="utf-8"))
        recorded = fingerprint_path.read_text(encoding="ascii").strip()
    except (OSError, json.JSONDecodeError, UnicodeError):
        return True
    if metadata.get("embedding_backend") != "hashing-v1":
        return True
    return recorded != _input_fingerprint(root)


def _record_fingerprint(root: Path) -> None:
    target = root / "index" / "skill-inputs.sha256"
    target.write_text(_input_fingerprint(root) + "\n", encoding="ascii")


def _python_environment(root: Path) -> dict[str, str]:
    environment = os.environ.copy()
    source = str(root / "src")
    previous = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = source if not previous else source + os.pathsep + previous
    environment["PYTHONUTF8"] = "1"
    return environment


def _run_module(root: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "relationship_kb", "--root", str(root), *arguments],
            cwd=root,
            env=_python_environment(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Knowledge-base command timed out") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "knowledge-base command failed"
        raise RuntimeError(detail)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="the complete user question")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--type", dest="document_type")
    parser.add_argument("--author")
    parser.add_argument("--concept")
    parser.add_argument("--root", help="use an existing knowledge-base checkout")
    parser.add_argument("--no-update", action="store_true", help="do not update a cached checkout")
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    if sys.version_info < (3, 10):
        print("error: Python 3.10 or newer is required", file=sys.stderr)
        return 2
    if args.top_k < 1:
        print("error: --top-k must be at least 1", file=sys.stderr)
        return 2
    try:
        location = ensure_repository(args.root, update=not args.no_update)
        root = Path(location.root)
        if _index_is_stale(root):
            print("Building the offline relationship-knowledge index...", file=sys.stderr)
            _run_module(root, ["build", "--backend", "hashing"])
            _record_fingerprint(root)
        command = ["context", args.question, "--top-k", str(args.top_k)]
        if args.document_type:
            command.extend(["--type", args.document_type])
        if args.author:
            command.extend(["--author", args.author])
        if args.concept:
            command.extend(["--concept", args.concept])
        result = _run_module(root, command)
    except (OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
