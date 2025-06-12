from google.cloud import bigquery
from typing import List, Dict, Set

def get_existing_ids_from_bigquery(project_id: str, dataset_id: str, table_id: str, id_list: List[str]) -> Set[str]:
    """
    Interroge BigQuery pour récupérer les IDs déjà présents.
    """
    if not id_list:
        return set()

    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    # Construction de la requête SQL
    id_list_str = ', '.join(f"'{id}'" for id in id_list)
    query = f"""
        SELECT id
        FROM `{table_ref}`
        WHERE id IN ({id_list_str})
    """

    query_job = client.query(query)
    return {row.id for row in query_job.result()}

def filter_existing_articles(articles: List[Dict], project_id: str, dataset_id: str, table_id: str) -> Set[str]:
    """
    Retourne les IDs d'articles déjà présents dans BigQuery.
    """
    all_ids = [article.get("id") for article in articles if article.get("id")]
    return get_existing_ids_from_bigquery(project_id, dataset_id, table_id, all_ids)
