import streamlit as st
import pandas as pd
from google.cloud import bigquery
import altair as alt
import seaborn as sns
import matplotlib.pyplot as plt

# Configuration
PROJECT_ID = "clarifai-news"
DATASET_ID = "news_data"
TABLE_ID = "rss_articles"
TABLE_REF = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

st.set_page_config(page_title="Analyse IA des articles de presse", layout="wide")
st.title("🔍 Détection de contenu IA dans les articles de presse")

# Connexion BigQuery
def load_data():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
        SELECT id, title, url, published_at, source,
               score_cat, score_base, score_small, score_dbdd
        FROM `{TABLE_REF}`
        WHERE score_cat IS NOT NULL
        ORDER BY published_at DESC
        LIMIT 1000
    """
    return client.query(query).to_dataframe()

@st.cache_data(ttl=600)
def get_data():
    return load_data()

df = get_data()

# Filtres
with st.sidebar:
    st.header(":mag: Filtres")
    sources = st.multiselect("Source", sorted(df["source"].dropna().unique()), default=None)
    date_range = st.date_input("Période", [])

if sources:
    df = df[df["source"].isin(sources)]

if len(date_range) == 2:
    start = pd.to_datetime(date_range[0]).tz_localize("UTC")
    end = pd.to_datetime(date_range[1]).tz_localize("UTC")
    df = df[(df["published_at"] >= start) & (df["published_at"] <= end)]
    
# Affichage des données
st.dataframe(df.sort_values("published_at", ascending=False), use_container_width=True)

# Comparaison des scores par modèle
st.subheader(":bar_chart: Comparaison des scores par modèle")
df_melted = df.melt(id_vars=["id", "source", "published_at"], 
                    value_vars=["score_cat", "score_base", "score_small", "score_dbdd"],
                    var_name="Modèle", value_name="Score")
chart = alt.Chart(df_melted).mark_boxplot(extent="min-max").encode(
    x=alt.X("Modèle:N", title="Modèle"),
    y=alt.Y("Score:Q", title="Perplexité"),
    color="Modèle:N"
).properties(width=700)
st.altair_chart(chart, use_container_width=True)

# Distribution des scores
st.subheader(":bar_chart: Distribution des scores (score_cat)")
hist = alt.Chart(df).mark_bar().encode(
    alt.X("score_cat", bin=True, title="Score de perplexité"),
    y='count()',
).properties(title="Distribution des scores_cat")
st.altair_chart(hist, use_container_width=True)

# Évolution temporelle des scores
st.subheader(":clock1: Évolution des scores dans le temps")
df["published_at"] = pd.to_datetime(df["published_at"])
daily_avg = df.groupby(df["published_at"].dt.date)[["score_cat", "score_base", "score_small", "score_dbdd"]].mean().reset_index()
daily_melted = daily_avg.melt("published_at")
line_chart = alt.Chart(daily_melted).mark_line().encode(
    x="published_at:T",
    y="value:Q",
    color="variable:N"
).properties(title="Scores moyens journaliers")
st.altair_chart(line_chart, use_container_width=True)

# Corrélation heure de publication
st.subheader("🕒 Moyenne des scores par tranche horaire")
df["hour_bin"] = pd.to_datetime(df["published_at"]).dt.hour // 3 * 3
hourly_avg = df.groupby("hour_bin")[["score_cat", "score_base", "score_small", "score_dbdd"]].mean().reset_index()
hourly_melted = hourly_avg.melt(id_vars=["hour_bin"], var_name="Modèle", value_name="Score")

hourly_chart = alt.Chart(hourly_melted).mark_bar().encode(
    x=alt.X("hour_bin:O", title="Heure de publication (tranche de 3h)"),
    y=alt.Y("Score:Q", title="Score moyen"),
    color="Modèle:N",
    tooltip=["hour_bin", "Modèle", "Score"]
).properties(
    title="Perplexité moyenne selon l'heure de publication"
)

st.altair_chart(hourly_chart, use_container_width=True)

# Déclenchement du DAG Airflow
st.subheader(":arrows_counterclockwise: Mise à jour des scores")
if st.button("Lancer le recalcul des scores manquants"):
    import os
    exit_code = os.system("airflow dags trigger score_missing_articles_pipeline")
    if exit_code == 0:
        st.success("DAG déclenché avec succès.")
    else:
        st.error("Erreur lors du déclenchement du DAG.")
