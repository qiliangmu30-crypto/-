from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Document:
    path: Path
    relative_path: str
    title: str
    doc_type: str
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    document_path: str
    title: str
    doc_type: str
    section: str
    content: str
    authors: list[str]
    concepts: list[str]
    source_url: str


@dataclass(slots=True)
class SearchResult:
    chunk_id: str
    document_path: str
    title: str
    doc_type: str
    section: str
    content: str
    authors: list[str]
    concepts: list[str]
    source_url: str
    doi: str
    evidence_level: str
    review_status: str
    score: float
    keyword_rank: int | None = None
    vector_rank: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_path": self.document_path,
            "title": self.title,
            "type": self.doc_type,
            "section": self.section,
            "content": self.content,
            "authors": self.authors,
            "concepts": self.concepts,
            "source_url": self.source_url,
            "doi": self.doi,
            "evidence_level": self.evidence_level,
            "review_status": self.review_status,
            "score": round(self.score, 6),
            "keyword_rank": self.keyword_rank,
            "vector_rank": self.vector_rank,
        }
