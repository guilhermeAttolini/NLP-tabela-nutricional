from __future__ import annotations
import re, httpx
from bs4 import BeautifulSoup
from trafilatura import extract as trafi_extract

def to_plain_text(input_type: str, content: str) -> str:
    t = (input_type or "auto").lower()
    if t == "text":
        return content
    if t == "html":
        soup = BeautifulSoup(content, "lxml")
        return soup.get_text(separator=" ", strip=True)
    if t == "url" or (t == "auto" and content.strip().startswith("http")):
        try:
            r = httpx.get(content, timeout=15)
            r.raise_for_status()
            txt = trafi_extract(r.text, include_comments=False, include_tables=False) or ""
            if not txt:
                soup = BeautifulSoup(r.text, "lxml")
                txt = soup.get_text(separator=" ", strip=True)
            return txt
        except Exception:
            return content
    if "<html" in content.lower():
        soup = BeautifulSoup(content, "lxml")
        return soup.get_text(separator=" ", strip=True)
    return content
