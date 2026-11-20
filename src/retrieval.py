from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .ingestion import read_text

TOKEN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    """Return Latin tokens plus Chinese character bigrams.

    Bigrams are a lightweight fallback when a production Chinese tokenizer is
    intentionally not installed. They make terms such as ``知识问答`` and
    ``客服知识库`` overlap without hiding the retrieval mechanism.
    """
    tokens: list[str] = []
    for item in TOKEN.findall(text.lower()):
        if re.fullmatch(r"[\u4e00-\u9fff]+", item):
            tokens.extend(item[index:index + 2] for index in range(len(item) - 1))
        else:
            tokens.append(item)
    return tokens


@dataclass(frozen=True)
class SearchResult:
    source: str
    excerpt: str
    score: float


class LocalKnowledgeBase:
    """A small, dependency-free TF-IDF retriever suitable for a portfolio demo."""

    def __init__(self, directory: str | Path):
        self.documents: list[tuple[str, str, Counter[str]]] = []
        for file in sorted(Path(directory).glob("*")):
            if file.suffix.lower() in {".md", ".txt"}:
                text = read_text(file)
                self.documents.append((file.name, text, Counter(tokenize(text))))
        if not self.documents:
            raise ValueError("Knowledge base is empty.")
        self.document_frequency = Counter()
        for _, _, terms in self.documents:
            self.document_frequency.update(terms.keys())

    def search(self, query: str, limit: int = 4) -> list[SearchResult]:
        terms = Counter(tokenize(query))
        total_docs = len(self.documents)
        scored: list[SearchResult] = []
        for name, text, doc_terms in self.documents:
            score = sum(
                query_count * (1 + math.log(doc_terms[token]))
                * math.log((total_docs + 1) / (self.document_frequency[token] + 1))
                for token, query_count in terms.items() if token in doc_terms
            )
            if score > 0:
                excerpt = " ".join(text.replace("\n", " ").split())[:280]
                scored.append(SearchResult(name, excerpt, round(score, 3)))
        return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]
