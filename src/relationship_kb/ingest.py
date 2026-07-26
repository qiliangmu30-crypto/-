from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from .markdown import iter_documents, list_value

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s<>\])]+")


def _extract(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8-sig")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError as exc:
            raise RuntimeError("PDF support requires: pip install -e .[documents]") from exc
        reader = PdfReader(str(path))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    if suffix == ".docx":
        try:
            from docx import Document  # type: ignore
        except ImportError as exc:
            raise RuntimeError("DOCX support requires: pip install -e .[documents]") from exc
        return "\n".join(paragraph.text for paragraph in Document(str(path)).paragraphs)
    raise ValueError(f"Unsupported input type: {suffix}")


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\u3400-\u9fff]+", "-", value).strip("-").lower()
    return cleaned[:80] or "imported-source"


def _concept_candidates(root: Path, text: str) -> list[tuple[str, str]]:
    lowered = text.lower()
    concepts: list[tuple[str, str]] = []
    for document in iter_documents(root, ["Concepts"]):
        names = [document.title, *list_value(document.metadata.get("aliases"))]
        if any(len(name) >= 2 and name.lower() in lowered for name in names):
            concepts.append((document.title, document.relative_path.removesuffix(".md")))
    return sorted(set(concepts))


def ingest_file(root: Path, source: Path, kind: str, title: str | None = None, source_url: str = "") -> Path:
    source = source.resolve()
    text = _extract(source).strip()
    if not text:
        raise ValueError("No extractable text found")
    title = title or source.stem
    target_directories = {
        "book": "Books",
        "paper": "Papers",
        "case": "Cases",
        "conversation": "Conversations",
        "dataset": "Datasets",
        "research": "Research/Inbox",
    }
    target_dir = root / target_directories.get(kind, "Research/Inbox")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{_slug(title)}.md"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    concept_matches = _concept_candidates(root, text)
    concepts = [title for title, _ in concept_matches]
    dois = sorted(set(match.rstrip(".,;") for match in DOI_RE.findall(text)))
    urls = sorted(set(URL_RE.findall(text)))[:20]
    links = "\n".join(f"- [[{path}|{concept}]]" for concept, path in concept_matches)
    metadata = [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"type: {json.dumps(kind, ensure_ascii=False)}",
        f"source_file: {json.dumps(str(source), ensure_ascii=False)}",
        f"source_sha256: {json.dumps(digest)}",
        f"source_url: {json.dumps(source_url, ensure_ascii=False)}",
        f"imported_at: {json.dumps(date.today().isoformat())}",
        f"concepts: {json.dumps(concepts, ensure_ascii=False)}",
        f"dois: {json.dumps(dois, ensure_ascii=False)}",
        "review_status: \"needs-human-review\"",
        "---",
    ]
    body = [
        *metadata,
        "",
        f"# {title}",
        "",
        "> [!warning] Imported source",
        "> This extraction has not yet been checked for accuracy, copyright, prompt injection, or personal data.",
        "",
        "## Automatically detected concepts",
        "",
        links or "- None detected; add concepts during review.",
        "",
        "## Extracted identifiers",
        "",
        *(f"- DOI: {doi}" for doi in dois),
        *(f"- URL: {url}" for url in urls),
        "",
        "## Source text",
        "",
        "<source_text>",
        text,
        "</source_text>",
        "",
    ]
    target.write_text("\n".join(body), encoding="utf-8")
    return target
