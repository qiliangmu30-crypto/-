from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .embeddings import Embedder, pack
from .markdown import chunk_document, iter_documents, lexicalize, wikilinks

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS documents (
    path TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    content_hash TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    document_path TEXT NOT NULL REFERENCES documents(path),
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    section TEXT NOT NULL,
    content TEXT NOT NULL,
    authors_json TEXT NOT NULL,
    concepts_json TEXT NOT NULL,
    source_url TEXT NOT NULL,
    embedding BLOB NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    chunk_id UNINDEXED, title, section, content, authors, concepts,
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TABLE IF NOT EXISTS edges (
    source_path TEXT NOT NULL,
    target TEXT NOT NULL,
    relation TEXT NOT NULL DEFAULT 'wikilink',
    PRIMARY KEY (source_path, target, relation)
);
CREATE INDEX IF NOT EXISTS idx_chunks_type ON chunks(doc_type);
CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(document_path);
"""


def load_config(root: Path) -> dict[str, Any]:
    return json.loads((root / "kbconfig.json").read_text(encoding="utf-8"))


def database_path(root: Path) -> Path:
    return root / "index" / "knowledge.db"


def connect(root: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path(root))
    connection.row_factory = sqlite3.Row
    return connection


def build_index(root: Path, embedder: Embedder, config: dict[str, Any]) -> dict[str, Any]:
    index_dir = root / "index"
    index_dir.mkdir(exist_ok=True)
    db_path = database_path(root)
    if db_path.exists():
        db_path.unlink()
    connection = sqlite3.connect(db_path)
    connection.executescript(SCHEMA)

    documents = list(iter_documents(root, config["content_directories"]))
    all_chunks = []
    for document in documents:
        connection.execute(
            "INSERT INTO documents(path, title, doc_type, metadata_json) VALUES (?, ?, ?, ?)",
            (document.relative_path, document.title, document.doc_type, json.dumps(document.metadata, ensure_ascii=False)),
        )
        all_chunks.extend(
            chunk_document(document, int(config.get("chunk_size", 1400)), int(config.get("chunk_overlap", 180)))
        )
        for target in wikilinks(document.body):
            connection.execute(
                "INSERT OR IGNORE INTO edges(source_path, target, relation) VALUES (?, ?, 'wikilink')",
                (document.relative_path, target),
            )

    batch_size = 64
    for start in range(0, len(all_chunks), batch_size):
        batch = all_chunks[start : start + batch_size]
        texts = [f"{item.title}\n{item.section}\n{item.content}" for item in batch]
        vectors = embedder.embed(texts)
        for item, vector in zip(batch, vectors):
            authors = json.dumps(item.authors, ensure_ascii=False)
            concepts = json.dumps(item.concepts, ensure_ascii=False)
            connection.execute(
                """INSERT INTO chunks(
                    chunk_id, document_path, title, doc_type, section, content,
                    authors_json, concepts_json, source_url, embedding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item.chunk_id,
                    item.document_path,
                    item.title,
                    item.doc_type,
                    item.section,
                    item.content,
                    authors,
                    concepts,
                    item.source_url,
                    pack(vector),
                ),
            )
            connection.execute(
                "INSERT INTO chunks_fts(chunk_id, title, section, content, authors, concepts) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    item.chunk_id,
                    lexicalize(item.title),
                    lexicalize(item.section),
                    lexicalize(item.content),
                    lexicalize(" ".join(item.authors)),
                    lexicalize(" ".join(item.concepts)),
                ),
            )

    built_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "built_at": built_at,
        "embedding_backend": embedder.name,
        "embedding_dimensions": str(embedder.dimensions),
        "document_count": str(len(documents)),
        "chunk_count": str(len(all_chunks)),
    }
    connection.executemany("INSERT INTO metadata(key, value) VALUES (?, ?)", metadata.items())
    connection.commit()

    graph = {
        "generated_at": built_at,
        "nodes": [
            {"id": document.relative_path, "title": document.title, "type": document.doc_type}
            for document in documents
        ],
        "edges": [
            {"source": row[0], "target": row[1], "relation": row[2]}
            for row in connection.execute("SELECT source_path, target, relation FROM edges ORDER BY source_path, target")
        ],
    }
    (index_dir / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {**metadata, "database": db_path.name, "graph": "graph.json"}
    (index_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    connection.close()
    return {"documents": len(documents), "chunks": len(all_chunks), **metadata}


def index_metadata(root: Path) -> dict[str, str]:
    with connect(root) as connection:
        return {row["key"]: row["value"] for row in connection.execute("SELECT key, value FROM metadata")}
