FROM apache/airflow:2.10.5

# Set user to root to install system dependencies
USER airflow
RUN pip install nltk googlemaps langdetect textblob gensim dbt-postgres
# Install system dependencies
USER root
RUN apt-get update && apt-get install -y git nano
# Upgrade pip and install necessary Python packages


# Switch back to the airflow user

USER airflow
