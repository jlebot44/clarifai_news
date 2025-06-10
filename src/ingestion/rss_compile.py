import json
import logging
from google.cloud import storage

# Configure le logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def archive_blob(blob, folder_prefix):
    client = storage.Client()
    bucket = blob.bucket

    blob_name = blob.name
    if blob_name.startswith(folder_prefix + "archived_"):
        return

    filename = blob_name[len(folder_prefix):]
    new_name = folder_prefix + "archived_" + filename

    bucket.copy_blob(blob, bucket, new_name)
    blob.delete()

    logger.info(f"Archivé : {blob_name} → {new_name}")

def collect_articles_from_gcs(bucket_name, folder_prefix):
    """
    Récupère tous les articles JSON depuis un dossier GCS, 
    en éliminant les doublons basés sur l'ID.
    
    Retourne :
        List[dict] : articles uniques
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=folder_prefix)

    articles_by_id = {}
    fichiers_traites = 0

    for blob in blobs:
        if blob.name.endswith('/'):
            continue

        relative_name = blob.name[len(folder_prefix):]
        if relative_name.startswith("archived_"):
            continue

        try:
            content = blob.download_as_text()
            data = json.loads(content)

            successfully_parsed = False

            if isinstance(data, list):
                for article in data:
                    if isinstance(article, dict):
                        article_id = article.get("id")
                        if article_id and article_id not in articles_by_id:
                            articles_by_id[article_id] = article
                            successfully_parsed = True
            elif isinstance(data, dict):
                article_id = data.get("id")
                if article_id and article_id not in articles_by_id:
                    articles_by_id[article_id] = data
                    successfully_parsed = True

            if successfully_parsed:
                archive_blob(blob, folder_prefix)
                fichiers_traites += 1

        except Exception as e:
            logger.warning(f"Erreur de parsing JSON dans {blob.name} : {e}")

    logger.info(f"{fichiers_traites} fichiers traités et archivés.")
    logger.info(f"{len(articles_by_id)} articles uniques collectés.")

    return list(articles_by_id.values())
