from pathlib import Path

from relationship_kb.ingest import ingest_file


def test_ingest_detects_concept_and_preserves_real_link(tmp_path: Path) -> None:
    concepts = tmp_path / "Concepts"
    concepts.mkdir()
    (concepts / "Attachment.md").write_text(
        '---\ntitle: "Attachment（依恋）"\ntype: "concept"\naliases: ["依恋"]\n---\n# Attachment',
        encoding="utf-8",
    )
    source = tmp_path / "source.txt"
    source.write_text("这是一段关于依恋和信任的研究笔记。DOI: 10.1000/example", encoding="utf-8")

    target = ingest_file(tmp_path, source, "research", title="Imported note")
    imported = target.read_text(encoding="utf-8")
    assert "[[Concepts/Attachment|Attachment（依恋）]]" in imported
    assert "10.1000/example" in imported
    assert "needs-human-review" in imported

