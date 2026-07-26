"""Locate or obtain the Relationship Knowledge Base checkout."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


REMOTE_URL = "https://github.com/qiliangmu30-crypto/-.git"
REMOTE_SUFFIX = "github.com/qiliangmu30-crypto/-"
REQUIRED_PATHS = (
    "kbconfig.json",
    "AGENTS.md",
    "Prompt/SYSTEM_PROMPT.md",
    "src/relationship_kb",
)


@dataclass(frozen=True)
class RepositoryLocation:
    root: str
    source: str
    updated: bool


def _is_knowledge_base(path: Path) -> bool:
    return path.is_dir() and all((path / item).exists() for item in REQUIRED_PATHS)


def _find_root(start: Path) -> Path | None:
    resolved = start.expanduser().resolve()
    for candidate in (resolved, *resolved.parents):
        if _is_knowledge_base(candidate):
            return candidate
    return None


def _run_git(arguments: list[str], cwd: Path | None = None, timeout: int = 180) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Git is required but was not found on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Git operation timed out") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(detail)
    return result.stdout.strip()


def _normalized_remote(value: str) -> str:
    normalized = value.strip().replace("\\", "/").removesuffix(".git").rstrip("/").lower()
    normalized = normalized.replace("git@github.com:", "github.com/")
    normalized = normalized.replace("ssh://git@github.com/", "github.com/")
    normalized = normalized.removeprefix("https://").removeprefix("http://")
    return normalized


def _verify_managed_checkout(root: Path) -> None:
    if not _is_knowledge_base(root) or not (root / ".git").exists():
        raise RuntimeError(f"Cache path is not a Relationship Knowledge Base checkout: {root}")
    remote = _normalized_remote(_run_git(["remote", "get-url", "origin"], cwd=root))
    if remote != REMOTE_SUFFIX:
        raise RuntimeError("Refusing to use a knowledge-base cache with an unexpected origin")


def _update_managed_checkout(root: Path) -> bool:
    if _run_git(["status", "--porcelain"], cwd=root):
        print("warning: knowledge-base cache has local changes; update skipped", file=sys.stderr)
        return False
    branch = _run_git(["branch", "--show-current"], cwd=root)
    if branch != "main":
        print(f"warning: knowledge-base cache is on {branch!r}; update skipped", file=sys.stderr)
        return False
    try:
        is_shallow = _run_git(["rev-parse", "--is-shallow-repository"], cwd=root) == "true"
        if is_shallow:
            _run_git(["fetch", "--unshallow", "origin", "main"], cwd=root)
            _run_git(["merge", "--ff-only", "FETCH_HEAD"], cwd=root)
        else:
            _run_git(["pull", "--ff-only", "origin", "main"], cwd=root)
    except RuntimeError as exc:
        print(f"warning: knowledge-base update failed; using cached copy: {exc}", file=sys.stderr)
        return False
    return True


def _default_cache_path() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    return (codex_home / "cache" / "relationship-knowledge-base").resolve()


def _clone_managed_checkout(cache: Path) -> None:
    cache.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(prefix=".relationship-kb-", dir=cache.parent))
    checkout = staging_root / "repo"
    try:
        _run_git(
            ["clone", "--depth", "1", "--branch", "main", REMOTE_URL, str(checkout)],
            timeout=300,
        )
        _verify_managed_checkout(checkout)
        if cache.exists():
            _verify_managed_checkout(cache)
            return
        checkout.replace(cache)
    except RuntimeError as exc:
        raise RuntimeError(
            "Unable to clone the private Relationship Knowledge Base. "
            "Authenticate Git for GitHub on this computer, confirm repository access, and retry. "
            f"Git reported: {exc}"
        ) from exc
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)


def ensure_repository(
    explicit_root: str | None = None,
    *,
    update: bool = True,
) -> RepositoryLocation:
    if explicit_root:
        root = Path(explicit_root).expanduser().resolve()
        if not _is_knowledge_base(root):
            raise RuntimeError(f"Not a Relationship Knowledge Base root: {root}")
        return RepositoryLocation(str(root), "explicit", False)

    skill_repository = _find_root(Path(__file__).resolve().parent)
    if skill_repository:
        return RepositoryLocation(str(skill_repository), "skill-repository", False)

    override = os.environ.get("RELATIONSHIP_KB_HOME")
    if override:
        root = Path(override).expanduser().resolve()
        if not _is_knowledge_base(root):
            raise RuntimeError(f"RELATIONSHIP_KB_HOME is not a knowledge-base root: {root}")
        return RepositoryLocation(str(root), "environment", False)

    cache = _default_cache_path()
    if cache.exists():
        _verify_managed_checkout(cache)
        updated = _update_managed_checkout(cache) if update else False
        return RepositoryLocation(str(cache), "cache", updated)

    _clone_managed_checkout(cache)
    return RepositoryLocation(str(cache), "cache", True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="use an existing knowledge-base checkout")
    parser.add_argument("--no-update", action="store_true", help="do not update a cached checkout")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        location = ensure_repository(args.root, update=not args.no_update)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(asdict(location), ensure_ascii=False))
    else:
        print(location.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
