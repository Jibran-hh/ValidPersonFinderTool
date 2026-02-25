from __future__ import annotations

from typing import List
import os

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException
from dotenv import load_dotenv

from models import RawSearchResult


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)


def _duckduckgo_serp(query: str, max_results: int) -> List[RawSearchResult]:
    """
    Primary DuckDuckGo integration using the official `duckduckgo-search`
    library (as requested in the assignment).
    """
    results: List[RawSearchResult] = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                try:
                    results.append(
                        RawSearchResult(
                            provider="duckduckgo",
                            title=item.get("title") or "",
                            url=item.get("href"),
                            snippet=item.get("body") or "",
                        )
                    )
                except Exception:
                    continue
    except RatelimitException:
        # On rate limit, return whatever partial list we have so far.
        return results
    except Exception:
        return results
    return results


def _duckduckgo_html_fallback(query: str, max_results: int) -> List[RawSearchResult]:
    """
    Fallback: scrape DuckDuckGo's HTML search results page when the library
    returns nothing. This stays within free, public access.
    """
    url = "https://duckduckgo.com/html/"
    params = {"q": query}
    headers = {"User-Agent": USER_AGENT}

    results: List[RawSearchResult] = []
    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=10.0)
        resp.raise_for_status()
    except Exception:
        return results

    soup = BeautifulSoup(resp.text, "html.parser")
    for res in soup.select(".result__body")[:max_results]:
        a = res.select_one(".result__a")
        if not a or not a.get("href"):
            continue
        title = a.get_text(strip=True)
        href = a["href"]
        snippet_el = res.select_one(".result__snippet")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        try:
            results.append(
                RawSearchResult(
                    provider="duckduckgo-html",
                    title=title,
                    url=href,
                    snippet=snippet,
                )
            )
        except Exception:
            continue

    return results


def duckduckgo_search(query: str, max_results: int = 6) -> List[RawSearchResult]:
    """
    High-level DuckDuckGo search used by the rest of the app.
    1) Try the official `duckduckgo-search` library (SERP-style results).
    2) If that yields no results (e.g. due to rate limiting), fall back to
       scraping the DuckDuckGo HTML SERP.
    """
    results = _duckduckgo_serp(query, max_results=max_results)
    if results:
        return results
    return _duckduckgo_html_fallback(query, max_results=max_results)


def brave_search(query: str, max_results: int = 10) -> List[RawSearchResult]:
    """
    Brave Web Search API integration (requires API key in BRAVE_API_KEY).
    This is a primary high-quality source for results.
    Docs: https://api-dashboard.search.brave.com/app/documentation/web-search/query
    """
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        return []

    url = "https://api.search.brave.com/res/v1/web/search"
    params = {
        "q": query,
        "count": max_results,
        "safesearch": "moderate",
        "extra_snippets": "true",
    }
    headers = {
        "X-Subscription-Token": api_key,
        "User-Agent": USER_AGENT,
    }

    results: List[RawSearchResult] = []

    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return results

    web = data.get("web", {})
    for item in web.get("results", []):
        title = item.get("title") or ""
        href = item.get("url")
        snippet = item.get("description") or ""
        if not href:
            continue
        try:
            results.append(
                RawSearchResult(
                    provider="brave",
                    title=title,
                    url=href,
                    snippet=snippet,
                )
            )
        except Exception:
            continue

    return results


def bing_search(query: str, max_results: int = 8) -> List[RawSearchResult]:
    """
    Lightweight HTML scrape of Bing SERP to act as a second, distinct search source.
    Does not require an API key but should be used responsibly.
    """
    url = "https://www.bing.com/search"
    params = {"q": query, "count": max_results}
    headers = {"User-Agent": USER_AGENT}

    results: List[RawSearchResult] = []

    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=10.0)
        resp.raise_for_status()
    except Exception:
        return results

    soup = BeautifulSoup(resp.text, "html.parser")
    for li in soup.select("li.b_algo"):
        a = li.select_one("h2 a")
        if not a or not a.get("href"):
            continue
        title = a.get_text(strip=True)
        href = a["href"]
        snippet_el = li.select_one("p")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        try:
            results.append(
                RawSearchResult(
                    provider="bing",
                    title=title,
                    url=href,
                    snippet=snippet,
                )
            )
        except Exception:
            continue

    return results
