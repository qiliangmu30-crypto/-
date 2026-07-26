from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .markdown import iter_documents, wikilinks


@dataclass(slots=True)
class Issue:
    path: str
    message: str


def lint_repository(root: Path, directories: list[str]) -> list[Issue]:
    documents = list(iter_documents(root, directories))
    known = set()
    # Links may legitimately target non-indexed operational notes such as Prompt/.
    for path in root.rglob("*.md"):
        if any(part in {".git", ".venv", "index"} for part in path.relative_to(root).parts):
            continue
        without_suffix = path.relative_to(root).as_posix().removesuffix(".md")
        known.update({without_suffix.lower(), Path(without_suffix).name.lower()})
    for document in documents:
        known.add(document.title.lower())

    issues: list[Issue] = []
    required = {"title", "type"}
    for document in documents:
        for key in sorted(required - document.metadata.keys()):
            issues.append(Issue(document.relative_path, f"missing frontmatter field: {key}"))
        for target in wikilinks(document.body):
            normalized = target.removesuffix(".md").lower()
            if normalized not in known and Path(normalized).name not in known:
                issues.append(Issue(document.relative_path, f"broken wikilink: [[{target}]]"))
    return issues
