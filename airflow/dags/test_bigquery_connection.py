from airflow.decorators import dag, task
from datetime import datetime
import logging
from google.cloud import bigquery

@dag(
    start_date=datetime(2024, 1, 1),
    schedule="@once",
    catchup=False,
    tags=["test", "bigquery"]
)
def test_bigquery_connection_dag():

    @task()
    def test_connection():
        logging.info("Initialisation du client BigQuery...")
        client = bigquery.Client()

        logging.info("Exécution de la requête...")
        query = "SELECT 'Airflow OK' AS message"
        result = client.query(query).result()

        for row in result:
            logging.info(f"✅ Réponse de BigQuery: {row['message']}")

    test_connection()

test_dag = test_bigquery_connection_dag()