from google.cloud import bigquery
import torch, math, time
from transformers import GPT2LMHeadModel, GPT2TokenizerFast, GPT2Tokenizer
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fonction de calcul de perplexité
def compute_perplexity(tokenizer, model, text, max_length=1024):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
    with torch.no_grad():
        outputs = model(**inputs, labels=inputs["input_ids"])
        loss = outputs.loss.item()
    return math.exp(loss)

def score_and_update(project="clarifai-news", dataset="news_data", table="rss_articles"):
    logger.info("Initialisation du client BigQuery...")
    client = bigquery.Client(project=project)
    table_ref = f"{project}.{dataset}.{table}"

    # Chargement des modèles
    MODELS = {
        "score_cat": "ClassCat/gpt2-base-french",
        "score_base": "asi/gpt-fr-cased-base",
        "score_small": "asi/gpt-fr-cased-small",
        "score_dbdd": "dbddv01/gpt2-french-small"
    }
    model_objects = {}

    logger.info("Chargement des modèles de langage...")
    for key, name in MODELS.items():
        try:
            tokenizer = GPT2TokenizerFast.from_pretrained(name)
        except:
            tokenizer = GPT2Tokenizer.from_pretrained(name)
        model = GPT2LMHeadModel.from_pretrained(name)
        model.eval()
        model_objects[key] = (tokenizer, model)
        logger.info(f"Modèle {name} chargé.")

    query = f"""
        SELECT id, content
        FROM `{table_ref}`
        WHERE score_cat IS NULL OR score_base IS NULL OR score_small IS NULL OR score_dbdd IS NULL
        LIMIT 20
    """
    logger.info("Exécution de la requête BigQuery pour récupérer les articles à scorer...")
    results = client.query(query).result()

    rows_to_update = []
    for row in results:
        id = row["id"]
        content = row["content"]
        logger.info(f"Traitement de l'article {id}...")

        update = {"id": id}
        for key, (tok, mod) in model_objects.items():
            start = time.time()
            try:
                score = compute_perplexity(tok, mod, content)
                logger.info(f"{key} => score={score:.4f}")
            except Exception as e:
                logger.error(f"Erreur sur {id} avec {key} : {e}")
                score = None
            duration = round((time.time() - start) * 1000)

            update[key] = score
            update[f"duration_{key.split('_')[1]}_ms"] = duration

        rows_to_update.append(update)

    logger.info(f"{len(rows_to_update)} lignes à mettre à jour dans BigQuery.")

    for row in rows_to_update:
        set_clause = ", ".join(
            f"{col} = {val if val is not None else 'NULL'}"
            for col, val in row.items() if col != "id"
        )
        update_query = f"""
            UPDATE `{table_ref}`
            SET {set_clause}
            WHERE id = '{row['id']}'
        """
        logger.debug(f"Requête UPDATE générée : {update_query.strip()}")
        client.query(update_query)

    logger.info("Mise à jour BigQuery terminée.")

if __name__ == "__main__":
    score_and_update()
