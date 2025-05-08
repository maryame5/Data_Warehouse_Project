import pandas as pd
import glob 
import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from storeData import *
from airflow.operators.bash_operator import BashOperator
from airflow.operators.email import EmailOperator


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['elkhalfimaryame@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': True,
    'email_on_success': True,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'google_maps_reviews',
    default_args=default_args,
    schedule_interval='@daily',  # Runs daily
    catchup=False,
    tags=['bank_reviews']
) as dag:
    fetch_reviews_task = PythonOperator(   
        task_id='fetch_google_reviews',  
        python_callable=fetch_google_reviews 
        )


    load_task = PythonOperator(
        task_id='Load_reviews1',
        python_callable=Load_reviews1 
    )
    remove_duplicates_task = PythonOperator(
    task_id='remove_duplicates',
    python_callable=remove_duplicates
)
    normalize_and_clean_task = PythonOperator(
    task_id='normalize_and_clean_data',
    python_callable=normalize_and_clean_data
)
    detect_language_task = PythonOperator(
        task_id='detect_language',
        python_callable=detect_language_reviews
    )
    analyze_sentiment_task = PythonOperator(
        task_id='analyze_sentiment',
        python_callable=analyze_sentiment
    )

    extract_topics_task = PythonOperator(
        task_id='extract_topics',
        python_callable=extract_topics
    )

    model_data_task = PythonOperator(
    task_id='model_data',
    python_callable=model_data,
    dag=dag
)
    dbt_run_task = BashOperator(
    task_id='run_dbt_models',
    bash_command='cd /opt/airflow/dbt_project/bank_reviews_dbt && dbt run --profiles-dir .',
    dag=dag
)
    dbt_test_task = BashOperator(
    task_id='test_dbt_models',
    bash_command='cd /opt/airflow/dbt_project/bank_reviews_dbt && dbt test --profiles-dir .',
    dag=dag
)
    dbt_docs_task = BashOperator(
    task_id='generate_dbt_docs',
    bash_command='cd /opt/airflow/dbt_project/bank_reviews_dbt && dbt docs generate',
    dag=dag
)
    export_data_to_csv = PythonOperator(
        task_id='export_to_csv',
        python_callable=export_data )
    
    send_email = EmailOperator(
    task_id='send_test_email',
    to='elkhalfimaryame@gmail.com',
    subject='Test Email from Airflow',
    html_content='<p>This is a test email.</p><p>Google reviews data pipeline has been successfully </p>' ,
       dag=dag,
    )

    #dbt_docs_serve_task = BashOperator(
    #task_id='serve_dbt_docs',
    #bash_command='cd /opt/airflow/dbt_project/bank_reviews_dbt && dbt docs serve --port 8081 --host 0.0.0.0',
    #dag=dag)
    #>> dbt_docs_serve_task


# Définir l'ordre d'exécution
fetch_reviews_task >> load_task >> remove_duplicates_task >> normalize_and_clean_task >> detect_language_task >> analyze_sentiment_task  >> extract_topics_task >> model_data_task  >> dbt_run_task >> dbt_test_task >> dbt_docs_task >> export_data_to_csv