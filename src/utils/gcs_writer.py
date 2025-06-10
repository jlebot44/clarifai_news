from google.cloud import storage
import json
from datetime import datetime
import uuid

def upload_to_gcs(data: list, bucket_name: str, prefix: str):
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Crée un nom de fichier unique
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    file_name = f"{prefix}/rss_{timestamp}_{uuid.uuid4().hex[:6]}.json"

    blob = bucket.blob(file_name)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=2), content_type='application/json')

    return file_name  # Optionnel : utile pour le log