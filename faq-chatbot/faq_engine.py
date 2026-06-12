from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # The app still works, but requirements.txt installs sklearn.
    TfidfVectorizer = None
    cosine_similarity = None

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
except ImportError:  # Fallback keeps the demo runnable before dependencies are installed.
    nltk = None
    stopwords = None
    WordNetLemmatizer = None
    word_tokenize = None


DEFAULT_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "with",
    "you",
    "your",
}


@dataclass(frozen=True)
class FAQ:
    question: str
    answer: str
    tags: tuple[str, ...] = ()

    @property
    def searchable_text(self) -> str:
        return " ".join([self.question, self.answer, *self.tags])


class TextPreprocessor:
    """Tokenize, normalize, remove stop words, and lemmatize text when NLTK is available."""

    def __init__(self) -> None:
        self._lemmatizer = WordNetLemmatizer() if WordNetLemmatizer else None
        self._stopwords = set(DEFAULT_STOPWORDS)
        if stopwords:
            try:
                self._stopwords.update(stopwords.words("english"))
            except LookupError:
                pass

    def tokenize(self, text: str) -> List[str]:
        text = text.lower()
        if word_tokenize:
            try:
                tokens = word_tokenize(text)
            except LookupError:
                tokens = re.findall(r"[a-z0-9]+", text)
        else:
            tokens = re.findall(r"[a-z0-9]+", text)

        cleaned = []
        for token in tokens:
            if not re.fullmatch(r"[a-z0-9]+", token):
                continue
            if token in self._stopwords:
                continue
            if self._lemmatizer:
                try:
                    token = self._lemmatizer.lemmatize(token)
                except LookupError:
                    pass
            cleaned.append(token)
        return cleaned


class FAQMatcher:
    def __init__(self, faqs: Iterable[FAQ], preprocessor: TextPreprocessor | None = None) -> None:
        self.faqs = list(faqs)
        if not self.faqs:
            raise ValueError("At least one FAQ is required.")

        self.preprocessor = preprocessor or TextPreprocessor()
        self._documents = [faq.searchable_text for faq in self.faqs]
        self._use_sklearn = TfidfVectorizer is not None and cosine_similarity is not None

        if self._use_sklearn:
            self._vectorizer = TfidfVectorizer(
                tokenizer=self.preprocessor.tokenize,
                lowercase=False,
                token_pattern=None,
            )
            self._matrix = self._vectorizer.fit_transform(self._documents)
        else:
            self._document_vectors = self._build_manual_vectors(self._documents)

    @classmethod
    def from_json(cls, path: Path | str) -> "FAQMatcher":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        faqs = [
            FAQ(
                question=item["question"].strip(),
                answer=item["answer"].strip(),
                tags=tuple(item.get("tags", [])),
            )
            for item in data["faqs"]
        ]
        return cls(faqs)

    def best_matches(self, user_question: str, limit: int = 3) -> list[dict]:
        if not user_question.strip():
            return []

        if self._use_sklearn:
            query_vector = self._vectorizer.transform([user_question])
            scores = cosine_similarity(query_vector, self._matrix).flatten()
        else:
            query_vector = self._manual_vector(user_question)
            scores = [self._manual_cosine(query_vector, vector) for vector in self._document_vectors]

        ranked_indexes = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)
        matches = []
        for index in ranked_indexes[:limit]:
            faq = self.faqs[index]
            matches.append(
                {
                    "question": faq.question,
                    "answer": faq.answer,
                    "score": round(float(scores[index]), 4),
                    "tags": list(faq.tags),
                }
            )
        return matches

    def answer(self, user_question: str, threshold: float = 0.12) -> dict:
        matches = self.best_matches(user_question)
        if not matches:
            return {
                "answer": "Please ask a question so I can search the FAQ collection.",
                "confidence": 0.0,
                "matched_question": None,
                "alternatives": [],
            }

        best = matches[0]
        if best["score"] < threshold:
            return {
                "answer": "I could not find a confident FAQ match. Try rephrasing or add this question to the FAQ data.",
                "confidence": best["score"],
                "matched_question": best["question"],
                "alternatives": matches,
            }

        return {
            "answer": best["answer"],
            "confidence": best["score"],
            "matched_question": best["question"],
            "alternatives": matches[1:],
        }

    def _build_manual_vectors(self, documents: list[str]) -> list[dict[str, float]]:
        tokenized_docs = [self.preprocessor.tokenize(document) for document in documents]
        document_frequency = Counter()
        for tokens in tokenized_docs:
            document_frequency.update(set(tokens))

        total_docs = len(tokenized_docs)
        self._manual_idf = {
            token: math.log((1 + total_docs) / (1 + count)) + 1
            for token, count in document_frequency.items()
        }
        return [self._tokens_to_tfidf(tokens) for tokens in tokenized_docs]

    def _manual_vector(self, text: str) -> dict[str, float]:
        return self._tokens_to_tfidf(self.preprocessor.tokenize(text))

    def _tokens_to_tfidf(self, tokens: list[str]) -> dict[str, float]:
        if not tokens:
            return {}

        counts = Counter(tokens)
        total = sum(counts.values())
        vector = {
            token: (count / total) * self._manual_idf.get(token, 1.0)
            for token, count in counts.items()
        }
        norm = math.sqrt(sum(value * value for value in vector.values()))
        if norm == 0:
            return vector
        return {token: value / norm for token, value in vector.items()}

    @staticmethod
    def _manual_cosine(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        return sum(left_token_score * right.get(token, 0.0) for token, left_token_score in left.items())


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python faq_engine.py "How do I track my order?"')
        return 1

    data_path = Path(__file__).resolve().parent / "data" / "faqs.json"
    matcher = FAQMatcher.from_json(data_path)
    result = matcher.answer(" ".join(sys.argv[1:]))
    print(f"Answer: {result['answer']}")
    print(f"Matched FAQ: {result['matched_question']}")
    print(f"Confidence: {result['confidence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
