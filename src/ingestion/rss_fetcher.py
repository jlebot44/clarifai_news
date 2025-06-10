# src/ingestion/rss_fetcher.py

import feedparser
from datetime import datetime, timezone
from typing import List, Dict
import logging
import hashlib
from email.utils import parsedate_to_datetime
from google.cloud import bigquery

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def generate_id_from_url(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest()

def parse_rss_datetime(published_raw: str) -> str:
    try:
        published_dt = parsedate_to_datetime(published_raw).astimezone(timezone.utc)
        return published_dt.isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()

# --------------------------------------------------
# Extraction
# --------------------------------------------------

def fetch_articles_from_rss(rss_url: str, source_name: str, language: str = "fr") -> List[Dict]:
    feed = feedparser.parse(rss_url)
    articles = []

    for entry in feed.entries:
        try:
            article = {
                "id": generate_id_from_url(entry.link),
                "title": entry.title,
                "summary": entry.get("summary", ""),
                "url": entry.link,
                "published_at": parse_rss_datetime(entry.get("published", "")),
                "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "source": source_name,
                "language": language
            }
            articles.append(article)
        except Exception as e:
            logging.warning(f"Erreur lors du parsing d’un article RSS : {e}")

    return articles

# --------------------------------------------------
# Filtrage
# --------------------------------------------------

def get_existing_ids(table_id: str) -> set:
    client = bigquery.Client()
    query = f"SELECT id FROM `{table_id}`"
    results = client.query(query)
    return {row.id for row in results}

def filter_new_articles(articles: List[Dict], existing_ids: set) -> List[Dict]:
    return [a for a in articles if a["id"] not in existing_ids]
