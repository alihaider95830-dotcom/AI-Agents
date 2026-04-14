from __future__ import annotations

import re

KEY_FACTS_MAX_RESULTS = 20
STATISTICS_MAX_RESULTS = 30
STATISTICS_CONTEXT_CHARS = 60
MIN_KEY_FACT_LENGTH = 30
MAX_KEY_FACT_LENGTH = 300

SENTENCE_SPLIT_PATTERN = re.compile(r"\.\s+")
NUMERIC_SIGNAL_PATTERN = re.compile(r"(\d|%|\$|€|£|¥|\b(?:19|20)\d{2}\b)")
PERCENTAGE_PATTERN = re.compile(r"\d+\.?\d*\s*%")
DOLLAR_PATTERN = re.compile(r"\$[\d,]+\.?\d*[MBKmb]?")
LARGE_NUMBER_PATTERN = re.compile(r"\b\d{1,3}(,\d{3})+\b")
YEAR_PATTERN = re.compile(r"\b(20\d{2}|19\d{2})\b")
STATISTIC_PATTERNS = (
    PERCENTAGE_PATTERN,
    DOLLAR_PATTERN,
    LARGE_NUMBER_PATTERN,
    YEAR_PATTERN,
)


class DataExtractor:
    def extract_key_facts(self, text: str, topic: str) -> list[str]:
        if not text or not topic:
            return []

        topic_words = {
            word.lower()
            for word in re.findall(r"\w+", topic)
            if word.strip()
        }
        sentences = SENTENCE_SPLIT_PATTERN.split(text)
        results: list[str] = []
        seen: set[str] = set()

        for sentence in sentences:
            cleaned = sentence.strip()
            if not cleaned:
                continue
            if len(cleaned) < MIN_KEY_FACT_LENGTH or len(cleaned) > MAX_KEY_FACT_LENGTH:
                continue
            if not NUMERIC_SIGNAL_PATTERN.search(cleaned):
                continue

            lowered = cleaned.lower()
            sentence_words = {
                word.lower()
                for word in re.findall(r"\w+", lowered)
                if word.strip()
            }
            if not sentence_words.intersection(topic_words):
                continue
            if cleaned in seen:
                continue

            seen.add(cleaned)
            results.append(cleaned)
            if len(results) >= KEY_FACTS_MAX_RESULTS:
                break

        return results

    def extract_statistics(self, text: str) -> list[str]:
        if not text:
            return []

        results: list[str] = []
        seen: set[str] = set()
        for pattern in STATISTIC_PATTERNS:
            for match in pattern.finditer(text):
                start = max(0, match.start() - STATISTICS_CONTEXT_CHARS)
                end = min(len(text), match.end() + STATISTICS_CONTEXT_CHARS)
                context = re.sub(r"\s+", " ", text[start:end]).strip()
                if context in seen:
                    continue
                seen.add(context)
                results.append(context)
                if len(results) >= STATISTICS_MAX_RESULTS:
                    return results
        return results

    def extract_competitor_mentions(
        self,
        text: str,
        known_competitors: list[str],
    ) -> dict[str, int]:
        if not text or not known_competitors:
            return {}

        counts: dict[str, int] = {}
        for competitor in known_competitors:
            match_count = len(re.findall(re.escape(competitor), text, flags=re.IGNORECASE))
            if match_count > 0:
                counts[competitor] = match_count
        return counts
