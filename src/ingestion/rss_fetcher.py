import feedparser
from google.cloud import bigquery
from datetime import datetime, timezone
from typing import List, Dict
import logging
import hashlib
from dotenv import load_dotenv
from email.utils import parsedate_to_datetime


from src.utils.bigquery_writer import upload_to_bigquery

# Charge les variables depuis .env
load_dotenv()

def get_existing_ids(table_id: str) -> set:
    client = bigquery.Client()
    query = f"SELECT id FROM `{table_id}`"
    results = client.query(query)
    return {row.id for row in results}


def generate_id_from_url(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest()

def fetch_articles_from_rss(rss_url: str, source_name: str, language: str = "fr") -> List[Dict]:
    feed = feedparser.parse(rss_url)
    articles = []

    for entry in feed.entries:
        try:
            # Convertit la date du RSS (ex: 'Thu, 05 Jun 2025 21:25:45 +0200') en datetime UTC ISO
            published_raw = entry.get("published", "")
            if published_raw:
                published_dt = parsedate_to_datetime(published_raw).astimezone(timezone.utc)
                published_at = published_dt.isoformat()
            else:
                published_at = datetime.now(timezone.utc).isoformat()

            fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

            article = {
                "id": generate_id_from_url(entry.link),
                "title": entry.title,
                "summary": entry.get("summary", ""),
                "url": entry.link,
                "published_at": published_at,
                "fetched_at": fetched_at,
                "source": source_name,
                "language": language
            }
            articles.append(article)
        except Exception as e:
            logging.warning(f"Erreur lors du parsing d’un article RSS : {e}")

    return articles

def main():
    logging.basicConfig(level=logging.INFO)

    rss_url = "https://www.franceinfo.fr/titres.rss"
    table_id = "clarifai-news.news_data.rss_articles"

    articles = fetch_articles_from_rss(rss_url, source_name="franceinfo")
    
    existing_ids = get_existing_ids(table_id)
    total = len(articles)
    articles = [a for a in articles if a["id"] not in existing_ids]
    new = len(articles)
    logging.info(f"{new} nouveaux articles sur {total} récupérés (doublons ignorés : {total - new})")
    upload_to_bigquery(articles, table_id)

if __name__ == "__main__":
    main()
