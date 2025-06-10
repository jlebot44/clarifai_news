from google.cloud import bigquery

def get_existing_ids_from_bigquery(project_id, dataset_id, table_id, id_list):
    """
    Interroge BigQuery pour trouver les IDs déjà présents.
    
    Retourne :
        Set[str] des IDs trouvés
    """
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    # Convertir en chaîne de valeurs SQL-safe
    id_list_str = ', '.join(f"'{id}'" for id in id_list)

    query = f"""
        SELECT id
        FROM `{table_ref}`
        WHERE id IN ({id_list_str})
    """

    query_job = client.query(query)
    results = query_job.result()
    return {row.id for row in results}

def filter_existing_articles(articles, project_id, dataset_id, table_id):
    """
    Filtre les articles dont l'ID existe déjà dans BigQuery.
    
    Retourne :
        List[dict] : articles trouvés dans BigQuery
    """
    all_ids = [article.get("id") for article in articles if article.get("id")]
    existing_ids = get_existing_ids_from_bigquery(project_id, dataset_id, table_id, all_ids)

    return [article for article in articles if article.get("id") in existing_ids]