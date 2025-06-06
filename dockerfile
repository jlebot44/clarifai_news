FROM apache/airflow:2.8.1-python3.10

# Installe les extras nécessaires à Celery, Postgres, Redis
RUN pip install --no-cache-dir \
    apache-airflow[celery,postgres,redis]==2.8.1

# Installe tes dépendances perso
COPY ./airflow/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
