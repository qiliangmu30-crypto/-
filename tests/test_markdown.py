from pathlib import Path

from relationship_kb.markdown import chunk_document, lexicalize, parse_frontmatter, read_document, wikilinks


def test_frontmatter_and_wikilinks(tmp_path: Path) -> None:
    path = tmp_path / "Concepts" / "Trust.md"
    path.parent.mkdir()
    path.write_text(
        '---\ntitle: "Trust（信任）"\ntype: "concept"\nauthors: ["A", "B"]\n---\n# Trust\n\nSee [[Concepts/Attachment|attachment]].',
        encoding="utf-8",
    )
    document = read_document(path, tmp_path)
    assert document.title == "Trust（信任）"
    assert document.metadata["authors"] == ["A", "B"]
    assert wikilinks(document.body) == ["Concepts/Attachment"]
    chunks = chunk_document(document, 1000, 100)
    assert chunks[0].doc_type == "concept"


def test_no_frontmatter() -> None:
    metadata, body = parse_frontmatter("# Plain\nText")
    assert metadata == {}
    assert body.startswith("# Plain")


def test_wikilinks_ignore_code() -> None:
    text = "Real [[Concepts/Trust]]. Inline `[[Example]]`.\n```md\n[[Fake]]\n```"
    assert wikilinks(text) == ["Concepts/Trust"]


def test_lexicalize_adds_chinese_ngrams() -> None:
    searchable = lexicalize("伴侣说没事")
    assert "没事" in searchable.split()
    assert "伴侣说" in searchable.split()


def test_link_only_section_is_not_a_retrieval_chunk(tmp_path: Path) -> None:
    path = tmp_path / "Concepts" / "Graph.md"
    path.parent.mkdir()
    path.write_text(
        '---\ntitle: "Graph"\ntype: "concept"\n---\n# Graph\n\n## Definition\nUseful evidence.\n\n## Links\n[[Concepts/Trust]]、[[Concepts/Attachment]]。',
        encoding="utf-8",
    )
    sections = [chunk.section for chunk in chunk_document(read_document(path, tmp_path), 1000, 100)]
    assert sections == ["Definition"]
