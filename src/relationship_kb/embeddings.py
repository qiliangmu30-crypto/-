from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from array import array
from typing import Protocol, Sequence

LATIN_RE = re.compile(r"[a-z0-9][a-z0-9_-]*")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


class Embedder(Protocol):
    name: str
    dimensions: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Deterministic multilingual feature hashing for offline bootstrap retrieval."""

    name = "hashing-v1"

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def _features(self, text: str) -> list[str]:
        normalized = unicodedata.normalize("NFKC", text).lower()
        words = LATIN_RE.findall(normalized)
        chars = CJK_RE.findall(normalized)
        features = words + [f"w:{a}_{b}" for a, b in zip(words, words[1:])]
        features.extend(f"c:{char}" for char in chars)
        features.extend(f"g:{a}{b}" for a, b in zip(chars, chars[1:]))
        return features

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        result: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for feature in self._features(text):
                digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
                number = int.from_bytes(digest, "little")
                index = number % self.dimensions
                sign = -1.0 if number & (1 << 63) else 1.0
                vector[index] += sign
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            result.append([value / norm for value in vector])
        return result


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        self.model = SentenceTransformer(model_name)
        self.name = model_name
        self.dimensions = int(self.model.get_sentence_embedding_dimension())

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self.model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
        return [list(map(float, vector)) for vector in vectors]


def get_embedder(backend: str, model_name: str, dimensions: int = 384) -> Embedder:
    if backend == "hashing":
        return HashingEmbedder(dimensions)
    if backend in {"sentence-transformers", "auto"}:
        try:
            return SentenceTransformerEmbedder(model_name)
        except (ImportError, OSError, RuntimeError):
            if backend == "sentence-transformers":
                raise
    return HashingEmbedder(dimensions)


def pack(vector: Sequence[float]) -> bytes:
    return array("f", vector).tobytes()


def unpack(blob: bytes) -> list[float]:
    vector = array("f")
    vector.frombytes(blob)
    return list(vector)


def dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))

