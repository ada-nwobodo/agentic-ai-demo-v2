from typing import List, Dict, Optional
import requests
import json
import os
import datetime
from pathlib import Path

class GuidelinesClient:
    """
    Generic REST client. Your endpoint should support GET ?q=<query>
    and return a JSON array of items with fields:
    {title, summary, url, source, published_at}
    """
    def __init__(self, base_url: str, timeout: int = 20):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        params = {"q": query, "limit": max_results}
        r = requests.get(self.base_url, params=params, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            raise ValueError("Guidelines API must return a JSON list.")
        # Normalize & truncate
        out = []
        for item in data[:max_results]:
            out.append({
                "title": item.get("title", "Untitled"),
                "summary": item.get("summary", ""),
                "url": item.get("url", ""),
                "source": item.get("source", "unknown"),
                "published_at": item.get("published_at", ""),
            })
        return out

class DemoGuidelinesClient:
    """
    Offline demo client backed by a small local dataset so you can test the flow end-to-end.
    Replace with GuidelinesClient(base_url=...) to use a real API.
    """
    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_guidelines.json")
        self.data_path = str(Path(data_path).resolve())

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        with open(self.data_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        # Naive ranking: keyword presence in title/summary
        q = (query or "").lower()
        def score(it):
            text = (it.get("title","") + " " + it.get("summary","")).lower()
            return (q in text) + sum(1 for token in q.split() if token in text)
        ranked = sorted(items, key=score, reverse=True)
        return ranked[:max_results]
