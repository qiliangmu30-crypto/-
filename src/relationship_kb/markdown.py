from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from .models import Chunk, Document

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
FENCED_CODE_RE = re.compile(r"^```.*?^```\s*$", re.MULTILINE | re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
CJK_RUN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")


def _scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        lowered = value.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        if value.startswith("[") and value.endswith("]"):
            return [part.strip().strip("\"'") for part in value[1:-1].split(",") if part.strip()]
        return value.strip("\"'")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    metadata: dict[str, Any] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = _scalar(value)
    return metadata, text[match.end() :]


def list_value(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def read_document(path: Path, root: Path) -> Document:
    text = path.read_text(encoding="utf-8-sig")
    metadata, body = parse_frontmatter(text)
    heading = HEADING_RE.search(body)
    title = str(metadata.get("title") or (heading.group(2) if heading else path.stem))
    relative = path.relative_to(root).as_posix()
    doc_type = str(metadata.get("type") or path.parent.name.rstrip("s").lower())
    return Document(path, relative, title, doc_type, body.strip(), metadata)


def iter_documents(root: Path, directories: Iterable[str]) -> Iterable[Document]:
    for directory in directories:
        folder = root / directory
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*.md")):
            if any(part.startswith(".") for part in path.relative_to(root).parts):
                continue
            yield read_document(path, root)


def _windows(text: str, limit: int, overlap: int) -> list[str]:
    if len(text) <= limit:
        return [text.strip()] if text.strip() else []
    windows: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        if end < len(text):
            boundary = max(text.rfind("\n\n", start, end), text.rfind("。", start, end), text.rfind(". ", start, end))
            if boundary > start + limit // 2:
                end = boundary + 1
        part = text[start:end].strip()
        if part:
            windows.append(part)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return windows


def chunk_document(document: Document, chunk_size: int, overlap: int) -> list[Chunk]:
    matches = list(HEADING_RE.finditer(document.body))
    sections: list[tuple[str, str]] = []
    if not matches:
        sections.append((document.title, document.body))
    else:
        prefix = document.body[: matches[0].start()].strip()
        if prefix:
            sections.append((document.title, prefix))
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(document.body)
            sections.append((match.group(2).strip(), document.body[start:end].strip()))

    chunks: list[Chunk] = []
    authors = list_value(document.metadata.get("authors") or document.metadata.get("author"))
    concepts = list_value(document.metadata.get("concepts") or document.metadata.get("related_concepts"))
    source_url = str(document.metadata.get("source_url") or document.metadata.get("url") or "")
    for section, content in sections:
        for part_number, part in enumerate(_windows(content, chunk_size, overlap), start=1):
            # A section containing only wikilinks is useful for the graph but
            # not as stand-alone retrieval evidence.
            without_links = WIKILINK_RE.sub("", part)
            if not re.search(r"[A-Za-z0-9\u3400-\u4dbf\u4e00-\u9fff]{3,}", without_links):
                continue
            digest = hashlib.sha256(f"{document.relative_path}:{section}:{part_number}".encode()).hexdigest()[:20]
            chunks.append(
                Chunk(
                    chunk_id=digest,
                    document_path=document.relative_path,
                    title=document.title,
                    doc_type=document.doc_type,
                    section=section,
                    content=part,
                    authors=authors,
                    concepts=concepts,
                    source_url=source_url,
                )
            )
    return chunks


def wikilinks(text: str) -> list[str]:
    # Example links inside code snippets are syntax documentation, not graph edges.
    searchable = FENCED_CODE_RE.sub("", text)
    searchable = INLINE_CODE_RE.sub("", searchable)
    return sorted({match.group(1).strip().replace("\\", "/") for match in WIKILINK_RE.finditer(searchable)})


def lexicalize(text: str) -> str:
    """Add CJK bi/tri-grams so SQLite unicode61 can retrieve unsegmented Chinese."""
    grams: list[str] = []
    for run in CJK_RUN_RE.findall(text):
        grams.extend(run[index : index + 2] for index in range(max(0, len(run) - 1)))
        grams.extend(run[index : index + 3] for index in range(max(0, len(run) - 2)))
    return f"{text} {' '.join(grams)}".strip()
