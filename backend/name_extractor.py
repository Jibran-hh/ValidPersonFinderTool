from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from models import PersonMatch, RawSearchResult


NAME_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\b")


TRUSTED_DOMAINS = [
    "linkedin.com",
    "www.linkedin.com",
    "wikipedia.org",
    "www.wikipedia.org",
    "crunchbase.com",
    "www.crunchbase.com",
    "bloomberg.com",
    "www.bloomberg.com",
    "reuters.com",
    "www.reuters.com",
]


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _source_type_for_url(url: str) -> str:
    d = _domain(url)
    if "linkedin.com" in d:
        return "linkedin_snippet"
    if "wikipedia.org" in d:
        return "wikipedia"
    if "crunchbase.com" in d:
        return "crunchbase"
    if any(news in d for news in ("bloomberg.com", "reuters.com", "forbes.com", "ft.com", "nytimes.com")):
        return "news"
    return "web"


def _extract_from_text(
    text: str, company: str, designation_aliases: Iterable[str]
) -> Tuple[Optional[str], Optional[str]]:
    """
    Try to pull a full name and matching title from title/snippet text.
    """
    company_lower = company.lower()
    text_lower = text.lower()

    # Flags for whether the text strongly refers to our context.
    # We now require *both* the company (or its exact string) and at least
    # one designation alias to be present before we trust this snippet for
    # person extraction. This avoids generic results like movie titles,
    # poems, etc., that only match on the company string.
    has_company = company_lower in text_lower
    alias_hit = None
    for alias in designation_aliases:
        if alias.lower() in text_lower:
            alias_hit = alias
            break

    if not (has_company and alias_hit):
        # Not enough context to safely pull a person name
        return None, None

    title_match = alias_hit

    # Prefer patterns like "Name - Title - Company"
    m = re.search(r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\s*[-–]\s*([^–\-|]+)", text)
    if m:
        full_name = m.group(1).strip()
        possible_title = m.group(2).strip()
        # If the fragment after the dash looks like a title for our aliases, prefer that
        if any(a.lower() in possible_title.lower() for a in designation_aliases):
            title_match = possible_title
        # At this point we already know we have both company and alias_hit
        return full_name, title_match

    # Fallback: first multi-word capitalized phrase in the text
    for m in NAME_PATTERN.finditer(text):
        full_name = m.group(1).strip()
        # For fallback, still require both company and alias context.
        if has_company and alias_hit:
            return full_name, title_match or alias_hit

    return None, title_match


def _split_name(full_name: str) -> Tuple[str, str]:
    parts = [p for p in full_name.split() if p]
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def score_candidate(
    result: RawSearchResult,
    full_name: str,
    current_title: Optional[str],
    company: str,
    designation_aliases: Iterable[str],
) -> float:
    score = 0.3  # base

    d = _domain(str(result.url))
    if d in TRUSTED_DOMAINS:
        score += 0.3
    elif company.replace(" ", "").lower() in d.replace(" ", "").lower():
        score += 0.25

    text = f"{result.title} {result.snippet}".lower()
    if company.lower() in text:
        score += 0.15

    if any(alias.lower() in text for alias in designation_aliases):
        score += 0.15

    if current_title:
        score += 0.1

    # Cap between 0 and 1
    return max(0.0, min(1.0, score))


def build_candidates(
    raw_results: Iterable[RawSearchResult],
    company: str,
    designation_aliases: Iterable[str],
) -> List[PersonMatch]:
    candidates_by_name: dict[str, List[PersonMatch]] = defaultdict(list)

    # First pass: strict extraction that requires both company and designation
    # context to be present in the snippet.
    for r in raw_results:
        text = f"{r.title} - {r.snippet}"
        full_name, maybe_title = _extract_from_text(text, company, designation_aliases)
        if not full_name:
            continue
        first_name, last_name = _split_name(full_name)
        confidence = score_candidate(r, full_name, maybe_title, company, designation_aliases)
        match = PersonMatch(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            current_title=maybe_title,
            company=company,
            source_url=r.url,
            source_type=_source_type_for_url(str(r.url)),
            search_provider=r.provider,
            confidence=confidence,
            evidence_snippet=r.snippet or r.title,
        )
        key = full_name.lower()
        candidates_by_name[key].append(match)

    # If we found at least one strict candidate, aggregate and return them.
    if candidates_by_name:
        merged: List[PersonMatch] = []
        for key, group in candidates_by_name.items():
            avg_conf = sum(m.confidence for m in group) / len(group)
            best = max(group, key=lambda m: m.confidence)
            best.confidence = max(min(avg_conf, 1.0), 0.0)
            merged.append(best)
        merged.sort(key=lambda m: m.confidence, reverse=True)
        return merged

    # Fallback pass: user requested that we still surface *something* even
    # when there is no strong match. Here we relax the constraints and try
    # to pull the first plausible person-like name from trusted domains,
    # marking it with a low confidence score so the UI makes it clear that
    # this is only a weak hint.
    fallback_candidates: List[PersonMatch] = []
    for r in raw_results:
        text = f"{r.title} - {r.snippet}"
        m = NAME_PATTERN.search(text)
        if not m:
            continue
        full_name = m.group(1).strip()
        first_name, last_name = _split_name(full_name)

        # Very conservative, low confidence for fallback guesses
        base_conf = 0.2
        if _domain(str(r.url)) in TRUSTED_DOMAINS:
            base_conf += 0.1

        match = PersonMatch(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            current_title=None,
            company=company,
            source_url=r.url,
            source_type=_source_type_for_url(str(r.url)),
            search_provider=r.provider,
            confidence=max(0.0, min(0.5, base_conf)),
            evidence_snippet=r.snippet or r.title,
        )
        fallback_candidates.append(match)

    # Sort fallback candidates by confidence (though they will all be low)
    fallback_candidates.sort(key=lambda m: m.confidence, reverse=True)
    return fallback_candidates
