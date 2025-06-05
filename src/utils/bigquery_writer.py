from google.cloud import bigquery
from typing import List, Dict
import logging



def upload_to_bigquery(data: List[Dict], table_id: str):
    # Si la liste est vide, on n'envoie rien
    if not data:
        logging.info("Aucune donnée à uploader.")
        return

    # Crée un client BigQuery basé sur les credentials GCP
    client = bigquery.Client()

    # Envoie les données (insert_rows_json = upload par lignes JSON)
    errors = client.insert_rows_json(table_id, data)

    # Si erreurs, on loggue et on lève une exception
    if errors:
        logging.error(f"Erreurs lors de l'envoi vers BigQuery : {errors}")
        raise RuntimeError(errors)

    logging.info(f"{len(data)} lignes insérées avec succès dans {table_id}")