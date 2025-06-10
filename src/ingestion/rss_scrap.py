from newspaper import Article
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def extract_article_content(url):
    """Extrait le texte principal d'un article à partir de son URL."""
    try:
        article = Article(url, language="fr")
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        logger.warning(f"❌ Erreur avec {url} : {e}")
        return None

def enrich_articles_with_content(articles, limit=None):
    """
    Enrichit une liste d'articles en ajoutant le champ 'content' via scraping.

    Args:
        articles (List[dict]): Liste d'articles avec au moins le champ 'url'.
        limit (int, optional): Pour restreindre le nombre traité.

    Returns:
        List[dict]: Liste enrichie avec le champ 'content'.
    """
    enriched = []
    to_process = articles if limit is None else articles[:limit]

    for article in to_process:
        url = article.get("url")
        if not url:
            continue

        logger.info(f"Scraping : {url}")
        content = extract_article_content(url)

        if content:
            enriched_article = article.copy()
            enriched_article["content"] = content
            enriched.append(enriched_article)

    logger.info(f"{len(enriched)} articles enrichis avec le champ 'content'.")
    return enriched