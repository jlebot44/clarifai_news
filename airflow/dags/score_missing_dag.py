from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

import sys
sys.path.append("/opt/airflow")  # pour retrouver src/

from src.scoring.score_missing_articles import score_and_update

# Paramètres du DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="score_missing_articles_pipeline",
    default_args=default_args,
    start_date=datetime(2025, 6, 10),
    schedule_interval=None,  # déclenchement manuel ou via API
    catchup=False,
    tags=["scoring", "perplexity", "bigquery"],
) as dag:

    score_missing = PythonOperator(
        task_id="score_missing_articles",
        python_callable=score_and_update
    )

    score_missing
