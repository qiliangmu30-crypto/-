from pathlib import Path

from relationship_kb.embeddings import HashingEmbedder
from relationship_kb.index import build_index
from relationship_kb.search import hybrid_search


def test_hybrid_search(tmp_path: Path) -> None:
    (tmp_path / "Concepts").mkdir()
    (tmp_path / "index").mkdir()
    (tmp_path / "Concepts" / "Trust.md").write_text(
        '---\ntitle: "Trust"\ntype: "concept"\nconcepts: ["attachment"]\ndoi: "10.1000/example"\nevidence_level: "Tier B"\nreview_status: "reviewed"\n---\n# Trust\n\nReliable responsiveness supports felt safety. 伴侣说没事。',
        encoding="utf-8",
    )
    config = {"content_directories": ["Concepts"], "chunk_size": 1000, "chunk_overlap": 100}
    embedder = HashingEmbedder(64)
    build_index(tmp_path, embedder, config)
    results = hybrid_search(tmp_path, embedder, "felt safety and trust", top_k=3)
    assert results
    assert results[0].title == "Trust"
    assert results[0].doi == "10.1000/example"
    assert results[0].evidence_level == "Tier B"
    assert results[0].review_status == "reviewed"
    chinese_results = hybrid_search(tmp_path, embedder, "没事", top_k=3)
    assert chinese_results[0].keyword_rank == 1
