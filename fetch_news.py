#!/usr/bin/env python3
"""Fetch top stories per country from Google News RSS (free, no key),
score the signals, and write data/news.json for the dashboard."""
import json, os, re, html, time, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

# code: (name, flag, hl, gl, ceid). Add more countries by adding lines (Google News editions list: news.google.com).
COUNTRIES = {
    "IN": ("India", "🇮🇳", "en-IN", "IN", "IN:en"),
    "US": ("United States", "🇺🇸", "en-US", "US", "US:en"),
    "GB": ("United Kingdom", "🇬🇧", "en-GB", "GB", "GB:en"),
    "AU": ("Australia", "🇦🇺", "en-AU", "AU", "AU:en"),
    "CA": ("Canada", "🇨🇦", "en-CA", "CA", "CA:en"),
    "NG": ("Nigeria", "🇳🇬", "en-NG", "NG", "NG:en"),
    "ZA": ("South Africa", "🇿🇦", "en-ZA", "ZA", "ZA:en"),
    "SG": ("Singapore", "🇸🇬", "en-SG", "SG", "SG:en"),
    "PK": ("Pakistan", "🇵🇰", "en-PK", "PK", "PK:en"),
    "KE": ("Kenya", "🇰🇪", "en-KE", "KE", "KE:en"),
}
MAX_STORIES = 15
TOPICS = {
    "disaster": "earthquake flood floods storm cyclone hurricane wildfire drought landslide tsunami eruption disaster",
    "economy": "inflation rates economy market markets stocks bank gdp trade tariff jobs prices budget currency",
    "security": "police attack army military cyber terror crime arrest war missile defense kidnapped",
    "politics": "election parliament minister government senate president court bill vote law coalition",
    "health": "health hospital vaccine disease outbreak virus medical cancer drug",
    "science": "space nasa isro satellite research scientists study ai technology launch",
    "sport": "cricket football match league cup olympic tennis goal win final tournament",
    "culture": "film festival music award concert actor singer art culture",
}
TOPIC_WORDS = {t: set(w.split()) for t, w in TOPICS.items()}
TRUSTED = {"reuters", "associated press", "bbc", "afp", "bloomberg", "al jazeera", "financial times",
           "the guardian", "npr", "the new york times", "the wall street journal", "the washington post"}
OFFICIAL = re.compile(r"(\.gov(\.[a-z]{2})?|\.go\.[a-z]{2}|\.int|\.nic\.in)$")
STOP = set("the and for with that this from after over into amid says said will have has new".split())


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (country-news-desk)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return ET.fromstring(r.read())


def tokens(title):
    return {w for w in re.findall(r"[a-z0-9]{3,}", title.lower()) if w not in STOP}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def topic_of(toks):
    best, score = "general", 0
    for t, words in TOPIC_WORDS.items():
        n = len(toks & words)
        if n > score:
            best, score = t, n
    return best


def cred_of(sources, official):
    vals = [0.95 if s.lower() in TRUSTED else 0.7 for s in sources] or [0.7]
    avg = sum(vals) / len(vals)
    return round(max(avg, 0.9) if official else avg, 2)


def load_country(code):
    _, _, hl, gl, ceid = COUNTRIES[code]
    root = fetch(f"https://news.google.com/rss?hl={hl}&gl={gl}&ceid={ceid}")
    now = datetime.now(timezone.utc)
    stories = []
    for it in root.iter("item"):
        title = html.unescape((it.findtext("title") or "").strip())
        src = it.find("source")
        source = (src.text or "").strip() if src is not None else ""
        domain = urlparse(src.get("url", "")).netloc if src is not None else ""
        if source and title.endswith(" - " + source):
            title = title[: -len(source) - 3]
        try:
            hrs = max(0.0, (now - parsedate_to_datetime(it.findtext("pubDate"))).total_seconds() / 3600)
        except Exception:
            hrs = 12.0
        related = re.findall(r"<font[^>]*>([^<]+)</font>", html.unescape(it.findtext("description") or ""))
        sources = {s.strip() for s in related if s.strip()} | ({source} if source else set())
        toks = tokens(title)
        official = bool(OFFICIAL.search(domain))
        for s in stories:
            if jaccard(toks, s["toks"]) >= 0.6:
                s["sources"] |= sources
                s["hrs"] = min(s["hrs"], hrs)
                s["official"] = s["official"] or official
                break
        else:
            stories.append({"title": title, "link": it.findtext("link") or "", "hrs": hrs,
                            "sources": sources or {"unknown"}, "official": official, "toks": toks})
    return stories


def main():
    data = {}
    for code in COUNTRIES:
        try:
            data[code] = load_country(code)
        except Exception as e:
            print("skip", code, e)
        time.sleep(1)
    out = {}
    for code, stories in data.items():
        stories.sort(key=lambda s: len(s["sources"]), reverse=True)
        rows = []
        for s in stories[:MAX_STORIES]:
            others = sum(1 for c, lst in data.items() if c != code
                         and any(jaccard(s["toks"], o["toks"]) >= 0.5 for o in lst))
            n = len(s["sources"])
            # evidence = [photo, location, official data, independent sources]; photo and location need extra steps
            rows.append([s["title"], topic_of(s["toks"]), n, cred_of(s["sources"], s["official"]),
                         round(s["hrs"], 1), round(min(others / 3, 1), 2),
                         [0, 0, int(s["official"]), n], s["link"]])
        name, flag = COUNTRIES[code][:2]
        out[code] = {"name": name, "flag": flag, "stories": rows}
    os.makedirs("data", exist_ok=True)
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump({"updated": datetime.now(timezone.utc).isoformat(), "countries": out}, f, ensure_ascii=False)
    print("wrote", sum(len(c["stories"]) for c in out.values()), "stories")


if __name__ == "__main__":
    main()
