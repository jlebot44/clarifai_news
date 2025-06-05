from google.cloud import bigquery
from dotenv import load_dotenv
import os

load_dotenv()

def test_bigquery_connection():
    try:
        client = bigquery.Client()
        project = client.project
        datasets = list(client.list_datasets())
        
        print(f"✅ Connexion réussie au projet : {project}")
        if datasets:
            print("📦 Datasets disponibles :")
            for ds in datasets:
                print(f" - {ds.dataset_id}")
        else:
            print("⚠️ Aucun dataset trouvé dans ce projet.")
    except Exception as e:
        print(f"❌ Erreur de connexion à BigQuery : {e}")

if __name__ == "__main__":
    test_bigquery_connection()
