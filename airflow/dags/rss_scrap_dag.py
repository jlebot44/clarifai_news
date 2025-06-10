from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

import sys
sys.path.append("/opt/airflow")  # pour retrouver src/

from src.ingestion.rss_compile import collect_articles_from_gcs
from src.ingestion.rss_filter import filter_existing_articles
from src.ingestion.rss_scrap import enrich_articles_with_content
from src.utils.bigquery_writer import upload_to_bigquery

# Paramètres du DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="news_ingestion_pipeline",
    default_args=default_args,
    start_date=datetime(2025, 6, 8),
    # schedule_interval="0 */2 * * *",  # toutes les 2 heures
    schedule_interval=None,  
    catchup=False,
    tags=["news", "gcs", "bq"],
) as dag:

    def step_1_collect_articles(**context):
        bucket = "clarifai-news-bucket"
        prefix = "rss_articles/"
        articles = collect_articles_from_gcs(bucket, prefix)
        context["ti"].xcom_push(key="collected_articles", value=articles)

    def step_2_filter_existing(**context):
        project = "clarifai-news"
        dataset = "news_data"
        table = "rss_articles"

        collected = context["ti"].xcom_pull(key="collected_articles", task_ids="collect_articles")
        uniques = [a for a in collected if a.get("id")]

        # ✅ Appel corrigé
        existing_ids = filter_existing_articles(uniques, project, dataset, table)

        # ✅ Sélection des articles à insérer (ID pas encore en BQ)
        filtered = [a for a in uniques if a["id"] not in existing_ids]

        context["ti"].xcom_push(key="filtered_articles", value=filtered)

    def step_3_scrape_content(**context):
        articles = context["ti"].xcom_pull(key="filtered_articles", task_ids="filter_existing_articles")
        enriched = enrich_articles_with_content(articles)
        context["ti"].xcom_push(key="enriched_articles", value=enriched)

    def step_4_upload_bq(**context):
        table_id = "clarifai-news.news_data.rss_articles"
        enriched = context["ti"].xcom_pull(key="enriched_articles", task_ids="scrape_content")
        upload_to_bigquery(enriched, table_id)

    # Définition des tâches
    collect = PythonOperator(
        task_id="collect_articles",
        python_callable=step_1_collect_articles,
        provide_context=True,
    )

    filter_existing = PythonOperator(
        task_id="filter_existing_articles",
        python_callable=step_2_filter_existing,
        provide_context=True,
    )

    scrape = PythonOperator(
        task_id="scrape_content",
        python_callable=step_3_scrape_content,
        provide_context=True,
    )

    upload = PythonOperator(
        task_id="upload_bigquery",
        python_callable=step_4_upload_bq,
        provide_context=True,
    )

    # Orchestration
    collect >> filter_existing >> scrape >> upload
