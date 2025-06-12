from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

import sys
sys.path.append("/opt/airflow")  # pour retrouver src/

from src.ingestion.rss_compile import collect_articles_from_gcs
from src.ingestion.rss_filter import filter_existing_articles
from src.ingestion.rss_scrap import enrich_articles_with_content
from src.ingestion.rss_cleaner import clean_articles
from src.utils.bigquery_writer import upload_to_bigquery
from src.utils.gcs_writer import upload_to_gcs
from src.utils.gcs_reader import read_from_gcs

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
        prefix = "pipeline_temp/collected_articles"

        articles = collect_articles_from_gcs(bucket, "rss_articles/")
        file_path = upload_to_gcs(articles, bucket, prefix)

        context["ti"].xcom_push(key="collected_path", value=file_path)

    def step_2_filter_existing(**context):
        project = "clarifai-news"
        dataset = "news_data"
        table = "rss_articles"
        bucket = "clarifai-news-bucket"
        prefix = "pipeline_temp/filtered_articles"

        collected_path = context["ti"].xcom_pull(key="collected_path", task_ids="collect_articles")
        articles = read_from_gcs(bucket, collected_path)

        uniques = [a for a in articles if a.get("id")]
        existing_ids = filter_existing_articles(uniques, project, dataset, table)

        logging.info(f"{len(existing_ids)} doublons détectés.")
        filtered = [a for a in uniques if a["id"] not in existing_ids]

        filtered_path = upload_to_gcs(filtered, bucket, prefix)
        context["ti"].xcom_push(key="filtered_path", value=filtered_path)

    def step_3_scrape_content(**context):
        bucket = "clarifai-news-bucket"
        prefix = "pipeline_temp/enriched_articles"

        filtered_path = context["ti"].xcom_pull(key="filtered_path", task_ids="filter_existing_articles")
        articles = read_from_gcs(bucket, filtered_path)

        enriched = enrich_articles_with_content(articles)
        enriched_path = upload_to_gcs(enriched, bucket, prefix)

        context["ti"].xcom_push(key="enriched_path", value=enriched_path)


    def step_4_clean_articles(**context):
        bucket = "clarifai-news-bucket"
        prefix = "pipeline_temp/cleaned_articles"

        enriched_path = context["ti"].xcom_pull(key="enriched_path", task_ids="scrape_content")
        enriched = read_from_gcs(bucket, enriched_path)

        cleaned = clean_articles(enriched)
        cleaned_path = upload_to_gcs(cleaned, bucket, prefix)

        context["ti"].xcom_push(key="cleaned_path", value=cleaned_path)


    def step_5_upload_bq(**context):
        table_id = "clarifai-news.news_data.rss_articles"
        bucket = "clarifai-news-bucket"
        cleaned_path = context["ti"].xcom_pull(key="cleaned_path", task_ids="clean_articles")
        cleaned = read_from_gcs(bucket, cleaned_path)

        upload_to_bigquery(cleaned, table_id)


    

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

    clean = PythonOperator(
        task_id="clean_articles",
        python_callable=step_4_clean_articles,
        provide_context=True,
    )

    upload = PythonOperator(
        task_id="upload_bigquery",
        python_callable=step_5_upload_bq,
        provide_context=True,
    )

    # Orchestration
    collect >> filter_existing >> scrape >> clean >> upload
