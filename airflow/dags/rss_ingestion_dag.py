import sys
sys.path.append("/opt/airflow")  # pour retrouver src/

from airflow.decorators import dag, task
from datetime import datetime
from src.ingestion.rss_fetcher import fetch_articles_from_rss, get_existing_ids
from src.utils.bigquery_writer import upload_to_bigquery
import logging


@dag(
    start_date=datetime(2024, 1, 1),
    schedule="*/15 * * * *",
    catchup=False,
    tags=["rss", "bigquery"]
)
def rss_ingestion_dag():

    @task()
    def extract_and_load():
        rss_url = "https://www.franceinfo.fr/titres.rss"
        table_id = "clarifai-news.news_data.rss_articles"

        articles = fetch_articles_from_rss(rss_url, source_name="franceinfo")
        existing_ids = get_existing_ids(table_id)

        total = len(articles)
        articles = [a for a in articles if a["id"] not in existing_ids]
        new = len(articles)

        logging.info(f"{new} nouveaux articles sur {total} récupérés (doublons ignorés : {total - new})")
        upload_to_bigquery(articles, table_id)

    extract_and_load()

rss_ingestion_dag = rss_ingestion_dag()