import feedparser
from datetime import datetime, timezone
from typing import List, Dict
import logging

def fetch_articles_from_rss(rss_url: str, source_name: str, language: str = "fr") -> List[Dict]:
    feed = feedparser.parse(rss_url)
    articles = []

    for entry in feed.entries:
        try:
            article = {
                "title": entry.title,
                "summary": entry.get("summary", ""),
                "url": entry.link,
                "published_at": entry.get("published", datetime.now(timezone.utc).isoformat()),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "source": source_name,
                "language": language
            }
            articles.append(article)
        except Exception as e:
            logging.warning(f"Erreur lors du parsing d’un article RSS : {e}")

    return articles

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rss_url = "https://www.franceinfo.fr/titres.rss"
    articles = fetch_articles_from_rss(rss_url, source_name="franceinfo")
    logging.info(f"{len(articles)} articles récupérés")
