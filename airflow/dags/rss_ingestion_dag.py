import sys
sys.path.append("/opt/airflow")  # pour retrouver src/

from airflow.decorators import dag, task
from datetime import datetime
from src.ingestion.rss_fetcher import fetch_articles_from_rss, get_existing_ids, filter_new_articles
from src.utils.gcs_writer import upload_to_gcs
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
        # existing_ids = get_existing_ids(table_id)

        total = len(articles)
        # articles = filter_new_articles(articles, existing_ids)
        new = len(articles)

        logging.info(f"{new} nouveaux articles sur {total} récupérés (doublons ignorés : {total - new})")
        
        bucket_name = "clarifai-news-bucket"
        prefix = "rss_articles"
        file_path = upload_to_gcs(articles, bucket_name, prefix)
        logging.info(f"Données sauvegardées dans GCS à {file_path}")

    extract_and_load()

dag = rss_ingestion_dag()