from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .embeddings import get_embedder
from .index import build_index, database_path, index_metadata, load_config
from .ingest import ingest_file
from .lint import lint_repository
from .search import format_context, hybrid_search


def repository_root(value: str | None = None) -> Path:
    if value:
        return Path(value).resolve()
    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "kbconfig.json").exists():
            return candidate
    raise FileNotFoundError("kbconfig.json not found; run the command inside the knowledge-base repository")


def _embedder(root: Path, config: dict, backend: str | None = None):
    selected = backend or str(config.get("embedding_backend", "hashing"))
    return get_embedder(selected, str(config.get("embedding_model", "")), int(config.get("embedding_dimensions", 384)))


def _ensure_index(root: Path) -> None:
    if not database_path(root).exists():
        raise FileNotFoundError("Index not found. Run: python -m relationship_kb build")


def command_build(args: argparse.Namespace) -> int:
    root = repository_root(args.root)
    config = load_config(root)
    embedder = _embedder(root, config, args.backend)
    stats = build_index(root, embedder, config)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


def _results(args: argparse.Namespace):
    root = repository_root(args.root)
    _ensure_index(root)
    config = load_config(root)
    metadata = index_metadata(root)
    backend = "hashing" if metadata.get("embedding_backend") == "hashing-v1" else "sentence-transformers"
    embedder = _embedder(root, config, backend)
    return root, hybrid_search(
        root,
        embedder,
        args.query,
        args.top_k or int(config.get("top_k", 8)),
        args.type,
        args.author,
        args.concept,
    )


def command_query(args: argparse.Namespace) -> int:
    _, results = _results(args)
    if args.json:
        print(json.dumps([result.as_dict() for result in results], ensure_ascii=False, indent=2))
    else:
        for index, result in enumerate(results, start=1):
            print(f"[{index}] {result.title} — {result.section} ({result.document_path}, score={result.score:.4f})")
            print(result.content[: args.preview].replace("\n", " "))
            print()
    return 0


def command_context(args: argparse.Namespace) -> int:
    _, results = _results(args)
    print(format_context(args.query, results))
    return 0


def command_ingest(args: argparse.Namespace) -> int:
    root = repository_root(args.root)
    target = ingest_file(root, Path(args.file), args.kind, args.title, args.source_url)
    print(target.relative_to(root).as_posix())
    print("Review the imported note, then rebuild the index.")
    return 0


def command_lint(args: argparse.Namespace) -> int:
    root = repository_root(args.root)
    config = load_config(root)
    issues = lint_repository(root, config["content_directories"])
    for issue in issues:
        print(f"{issue.path}: {issue.message}")
    print(f"{len(issues)} issue(s)")
    return 1 if issues and args.strict else 0


def command_stats(args: argparse.Namespace) -> int:
    root = repository_root(args.root)
    _ensure_index(root)
    print(json.dumps(index_metadata(root), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="relationship-kb", description="Local relationship-psychology RAG")
    parser.add_argument("--root", help="repository root (normally auto-detected)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="rebuild FTS, vector, and graph indexes")
    build.add_argument("--backend", choices=["hashing", "sentence-transformers", "auto"])
    build.set_defaults(handler=command_build)

    for name, handler, help_text in [
        ("query", command_query, "search and preview chunks"),
        ("context", command_context, "emit an AI-ready retrieval bundle"),
    ]:
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("query")
        command.add_argument("--top-k", type=int)
        command.add_argument("--type")
        command.add_argument("--author")
        command.add_argument("--concept")
        if name == "query":
            command.add_argument("--json", action="store_true")
            command.add_argument("--preview", type=int, default=280)
        command.set_defaults(handler=handler)

    ingest = subparsers.add_parser("ingest", help="extract a local source into a reviewable Markdown note")
    ingest.add_argument("file")
    ingest.add_argument("--kind", choices=["book", "paper", "case", "conversation", "dataset", "research"], default="research")
    ingest.add_argument("--title")
    ingest.add_argument("--source-url", default="")
    ingest.set_defaults(handler=command_ingest)

    lint = subparsers.add_parser("lint", help="check metadata and wikilinks")
    lint.add_argument("--strict", action="store_true")
    lint.set_defaults(handler=command_lint)

    stats = subparsers.add_parser("stats", help="show current index metadata")
    stats.set_defaults(handler=command_stats)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

