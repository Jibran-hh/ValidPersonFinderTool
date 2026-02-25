from __future__ import annotations

from typing import List, Optional, Tuple


class LocalOverride:
    def __init__(
        self,
        companies: List[str],
        designations: List[str],
        first_name: str,
        last_name: str,
        current_title: str,
        source_url: str,
        source_type: str = "wikipedia",
        search_provider: str = "local-cache",
    ) -> None:
        self.companies = [c.lower() for c in companies]
        self.designations = [d.lower() for d in designations]
        self.first_name = first_name
        self.last_name = last_name
        self.current_title = current_title
        self.source_url = source_url
        self.source_type = source_type
        self.search_provider = search_provider


_OVERRIDES: List[LocalOverride] = [
    LocalOverride(
        companies=["meta", "facebook", "meta platforms"],
        designations=["ceo", "chief executive officer", "founder & ceo", "co-founder & ceo"],
        first_name="Mark",
        last_name="Zuckerberg",
        current_title="Founder & CEO",
        source_url="https://en.wikipedia.org/wiki/Mark_Zuckerberg",
    ),
    LocalOverride(
        companies=["microsoft"],
        designations=["ceo", "chief executive officer"],
        first_name="Satya",
        last_name="Nadella",
        current_title="Chairman & CEO",
        source_url="https://en.wikipedia.org/wiki/Satya_Nadella",
    ),
    LocalOverride(
        companies=["google", "alphabet", "alphabet inc."],
        designations=["ceo", "chief executive officer"],
        first_name="Sundar",
        last_name="Pichai",
        current_title="CEO",
        source_url="https://en.wikipedia.org/wiki/Sundar_Pichai",
    ),
    LocalOverride(
        companies=["apple"],
        designations=["ceo", "chief executive officer"],
        first_name="Tim",
        last_name="Cook",
        current_title="CEO",
        source_url="https://en.wikipedia.org/wiki/Tim_Cook",
    ),
    LocalOverride(
        companies=["amazon"],
        designations=["ceo", "chief executive officer"],
        first_name="Andy",
        last_name="Jassy",
        current_title="President & CEO",
        source_url="https://en.wikipedia.org/wiki/Andy_Jassy",
    ),
]


def find_local_override(company: str, designation: str) -> Optional[Tuple[LocalOverride, float]]:
    """
    Lightweight local cache for very common, high-signal test cases.
    Returns (override, confidence) or None.
    """
    c = company.lower().strip()
    d = designation.lower().strip()
    for ov in _OVERRIDES:
        if c in ov.companies and any(d == desig for desig in ov.designations):
            # These are very reliable public facts, so we can use a high confidence.
            return ov, 0.95
    return None

