from __future__ import annotations

from typing import List


_DESIGNATION_ALIASES = {
    "ceo": ["CEO", "Chief Executive Officer", "Founder & CEO", "Co-founder & CEO"],
    "cto": ["CTO", "Chief Technology Officer", "VP Engineering"],
    "cfo": ["CFO", "Chief Financial Officer"],
    "coo": ["COO", "Chief Operating Officer"],
    "cmo": ["CMO", "Chief Marketing Officer"],
    "head of engineering": ["Head of Engineering", "Director of Engineering", "VP Engineering"],
    "head of hr": ["Head of HR", "Head of Human Resources", "HR Director"],
    "head of sales": ["Head of Sales", "VP Sales", "Sales Director"],
}


def get_designation_aliases(designation: str) -> List[str]:
    base = designation.strip().lower()
    aliases: List[str] = [designation.strip()]

    for key, values in _DESIGNATION_ALIASES.items():
        if key in base:
            aliases.extend(values)

    # Always include a title-cased version as a fallback variant
    if designation.strip().title() not in aliases:
        aliases.append(designation.strip().title())

    # Deduplicate while preserving order
    seen = set()
    unique_aliases: List[str] = []
    for a in aliases:
        if a.lower() not in seen:
            seen.add(a.lower())
            unique_aliases.append(a)

    return unique_aliases
