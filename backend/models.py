from typing import List, Optional

from pydantic import BaseModel, HttpUrl, Field


class SearchRequest(BaseModel):
    company: str = Field(..., description="Company name, e.g. 'Meta' or 'Google'")
    designation: str = Field(..., description="Role title, e.g. 'CEO' or 'Head of HR'")


class RawSearchResult(BaseModel):
    provider: str
    title: str
    url: HttpUrl
    snippet: str


class PersonMatch(BaseModel):
    first_name: str
    last_name: str
    full_name: str
    current_title: Optional[str] = None
    company: Optional[str] = None
    source_url: HttpUrl
    source_type: str
    search_provider: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_snippet: Optional[str] = None


class SearchResponse(BaseModel):
    company: str
    designation: str
    normalized_designation_aliases: List[str]
    best_match: Optional[PersonMatch]
    candidates: List[PersonMatch]
    raw_results: List[RawSearchResult]
    message: str
