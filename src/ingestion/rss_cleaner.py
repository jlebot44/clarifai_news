import re
import html

def clean_articles(articles):
    cleaned = []

    for article in articles:
        content = article.get("content", "")
        
        if isinstance(content, str):
            # 1. Unescape HTML entities
            content = html.unescape(content)
            
            # 2. Remplacer les guillemets doubles par des simples
            content = content.replace('"', "'")
            
            # 3. Nettoyer les parenthèses éditoriales (e.g. "(Nouvelle fenêtre)")
            content = re.sub(r"\s*\(Nouvelle fenêtre\)", "", content)

            # 4. Supprimer les entêtes ou mentions non informatives (e.g. ": à lire aussi ...")
            content = re.sub(r":\s*à lire aussi.*?(?=\n|$)", "", content, flags=re.IGNORECASE)

            # 5. Supprimer les entêtes de section numériques ou titres automatiques
            content = re.sub(r"^\d+\s+", "", content)

            # 6. Normalisation des guillemets français
            content = content.replace("«", '"').replace("»", '"')

            # 7. Uniformisation des apostrophes typographiques
            content = content.replace("’", "'")

            # 8. Réduction des multiples sauts de ligne
            content = re.sub(r"\n{2,}", "\n", content)

            # 9. Nettoyage de fin de citation type "cité par ..."
            content = re.sub(r", cité par [^.]+[.]", ".", content)

            # Trim
            content = content.strip()

        article["content"] = content
        cleaned.append(article)

    return cleaned