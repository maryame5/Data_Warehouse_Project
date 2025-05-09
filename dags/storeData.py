import pandas as pd
import glob
import os
from datetime import datetime, timedelta
import string
import time
import nltk
from nltk.corpus import stopwords 
from langdetect import detect
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import execute_values
from textblob import TextBlob
from gensim import corpora, models
from nltk.tokenize import word_tokenize
import googlemaps
nltk.download('stopwords')
nltk.download('punkt_tab')




#docker exec -it airflow_doc-airflow-webserver-1 bash

#airflow connections add 'postgres_defaut'     --conn-uri 'postgresql+psycopg2://airflow:airflow@postgres:5432/airflow'

#docker exec -it airflow-doc-airflow-webserver-1 psql -h postgres -U airflow -d airflow

#ALTER TABLE review.raw_reviews ADD COLUMN language TEXT DEFAULT '';
#error: there is no unique or exclusion constraint matching the ON CONFLICT specification
    # ALTER TABLE review.dim_bank ADD CONSTRAINT unique_bank_name UNIQUE (bank_name);
    # ALTER TABLE review.dim_branch ADD CONSTRAINT unique_branch_name UNIQUE (branch_name);
   # ALTER TABLE review.dim_location ADD CONSTRAINT unique_location UNIQUE (location);
   # ALTER TABLE review.dim_sentiment ADD CONSTRAINT unique_sentiment_label UNIQUE (sentiment_label);
#vider les tableau 
# TRUNCATE TABLE review.dim_bank RESTART IDENTITY CASCADE;
# TRUNCATE TABLE review.dim_branch RESTART IDENTITY CASCADE;
# TRUNCATE TABLE review.dim_location RESTART IDENTITY CASCADE;
# TRUNCATE TABLE review.dim_sentiment RESTART IDENTITY CASCADE;
# TRUNCATE TABLE review.fact_reviews RESTART IDENTITY CASCADE;
# TRUNCATE TABLE review.raw_reviews RESTART IDENTITY CASCADE;
#drop table review.dim_bank cascade;
#drop table review.dim_branch cascade;
#drop table review.dim_location cascade;
#drop table review.dim_sentiment cascade;
#drop table review.fact_reviews cascade;
#drop table review.raw_reviews cascade;


#export database to csv
def export_data():
    pg_hook = PostgresHook(postgres_conn_id="postgres_defaut")
    conn = pg_hook.get_conn()
    cur = conn.cursor()
    
    query="""
SELECT 
         rr.place_id,
            rr.bank_name,
            rr.branch_name,
            rr.location,
            rr.language,
            rr.sentiment,
            rr.topic,
            rr.review_text,
            rr.rating,
            rr.review_date,
            db.bank_id,
            br.branch_id,
            dl.location_id,
            ds.sentiment_id
FROM review.raw_reviews rr
LEFT JOIN review.dim_bank db ON rr.bank_name = db.bank_name
LEFT JOIN review.dim_branch br ON rr.branch_name = br.branch_name
LEFT JOIN review.dim_location dl ON rr.location = dl.location
LEFT JOIN review.dim_sentiment ds ON rr.sentiment = ds.sentiment_label
GROUP BY
         rr.place_id,
            rr.bank_name,
            rr.branch_name,
            rr.location,
            rr.language,
            rr.sentiment,
            rr.topic,
            rr.review_text,
            rr.rating,
            rr.review_date,
            db.bank_id,
            br.branch_id,
            dl.location_id,
            ds.sentiment_id

ORDER BY rr.PLACE_ID DESC;
"""

    cur.execute(query)
    conn.commit()
    # Charger les données dans un DataFrame
    df = pd.read_sql_query(query, conn)

# Exporter vers CSV
    csv_path = "/opt/airflow/dags/output/export_reviews.csv"

    # Append new data to existing CSV or create a new file if it doesn't exist
    df.to_csv(csv_path, index=False)


    print("✅ Données exportées avec succès vers reviews_export.csv")
    cur.close()
    conn.close()





#data modeling
def model_data():
    pg_hook = PostgresHook(postgres_conn_id="postgres_defaut")
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    # Exécuter le script SQL pour créer les tables
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS review.dim_bank (
    bank_id SERIAL PRIMARY KEY,
    bank_name TEXT UNIQUE,
    CONSTRAINT unique_bank_name UNIQUE (bank_name)
);

CREATE TABLE IF NOT EXISTS review.dim_branch (
    branch_id SERIAL PRIMARY KEY,
    branch_name TEXT UNIQUE,
    CONSTRAINT unique_branch_name UNIQUE (branch_name)
);

CREATE TABLE IF NOT EXISTS review.dim_location (
    location_id SERIAL PRIMARY KEY,
    location TEXT UNIQUE,
    CONSTRAINT unique_location UNIQUE (location)
);

CREATE TABLE IF NOT EXISTS review.dim_sentiment (
    sentiment_id SERIAL PRIMARY KEY,
    sentiment_label TEXT UNIQUE,
    CONSTRAINT unique_sentiment_label UNIQUE (sentiment_label)
);

CREATE TABLE IF NOT EXISTS review.fact_reviews (
    review_id SERIAL PRIMARY KEY,
    place_id TEXT,
    bank_id INT REFERENCES review.dim_bank(bank_id),
    branch_id INT REFERENCES review.dim_branch(branch_id),
    location_id INT REFERENCES review.dim_location(location_id),
    sentiment_id INT REFERENCES review.dim_sentiment(sentiment_id),
    review_text TEXT,
    rating FLOAT,
    review_date TIMESTAMP
);
    """
    query="""
     ALTER TABLE review.dim_bank ADD CONSTRAINT unique_bank_name UNIQUE (bank_name);
    ALTER TABLE review.dim_branch ADD CONSTRAINT unique_branch_name UNIQUE (branch_name);
   ALTER TABLE review.dim_location ADD CONSTRAINT unique_location UNIQUE (location);
   ALTER TABLE review.dim_sentiment ADD CONSTRAINT unique_sentiment_label UNIQUE (sentiment_label);"""
    

    # Peupler les tables de dimension
    populate_dim_sql = """
    INSERT INTO review.dim_bank (bank_name) 
SELECT DISTINCT bank_name FROM review.raw_reviews
ON CONFLICT (bank_name) DO NOTHING
;

INSERT INTO review.dim_branch (branch_name) 
SELECT DISTINCT branch_name FROM review.raw_reviews
ON CONFLICT (branch_name) DO NOTHING
;

INSERT INTO review.dim_location (location) 
SELECT DISTINCT location FROM review.raw_reviews
ON CONFLICT (location) DO NOTHING
;

INSERT INTO review.dim_sentiment (sentiment_label) 
SELECT DISTINCT sentiment FROM review.raw_reviews
ON CONFLICT (sentiment_label) DO NOTHING
;


    """

    # Insérer les données dans fact_reviews
    populate_fact_sql = """
    INSERT INTO review.fact_reviews (place_id, bank_id, branch_id, location_id, sentiment_id, review_text, rating, review_date)
SELECT 
    rr.place_id,
    db.bank_id,
    br.branch_id,
    dl.location_id,
    ds.sentiment_id,
    rr.review_text,
    rr.rating,
    rr.review_date
FROM review.raw_reviews rr
LEFT JOIN review.dim_bank db ON rr.bank_name = db.bank_name
LEFT JOIN review.dim_branch br ON rr.branch_name = br.branch_name
LEFT JOIN review.dim_location dl ON rr.location = dl.location
LEFT JOIN review.dim_sentiment ds ON rr.sentiment = ds.sentiment_label;

    """
    try:
        cur.execute(create_tables_sql)
        cur.execute(query)
        cur.execute(populate_dim_sql)
        cur.execute(populate_fact_sql)
        
        conn.commit()

        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

#extract topics from reviews using LDA
def extract_topics():
    pg_hook = PostgresHook(postgres_conn_id="postgres_defaut")
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    # 1. Récupérer les avis
    cur.execute("SELECT id, review_text FROM review.raw_reviews;")
    rows = cur.fetchall()

    ids = [row[0] for row in rows]
    reviews = [row[1] for row in rows]

    # 2. Prétraitement + LDA
    tokenized_reviews = [word_tokenize(review.lower()) for review in reviews]
    dictionary = corpora.Dictionary(tokenized_reviews)
    corpus = [dictionary.doc2bow(text) for text in tokenized_reviews]
    lda_model = models.LdaModel(corpus, num_topics=3, id2word=dictionary, passes=10)

    # 3. Associer le texte du topic dominant
    dominant_topic_labels = []
    for bow in corpus:
        topic_distribution = lda_model.get_document_topics(bow)
        dominant_topic_id = max(topic_distribution, key=lambda x: x[1])[0]
        # Extraire le libellé du topic dominant (mots-clés)
        topic_terms = lda_model.show_topic(dominant_topic_id, topn=3)
        topic_label = ", ".join([word for word, _ in topic_terms])
        dominant_topic_labels.append(topic_label)

    # 4. Mise à jour de la base
    for review_id, topic_text in zip(ids, dominant_topic_labels):
        cur.execute("""
            UPDATE review.raw_reviews
            SET topic = %s
            WHERE id = %s;
        """, (topic_text, review_id))
    
    

    conn.commit()
    cur.close()
    conn.close()



#extract sentiment from reviews
def analyze_sentiment():
    pg_hook = PostgresHook(postgres_conn_id="postgres_defaut")
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    cur.execute("SELECT review_text, id FROM review.raw_reviews WHERE sentiment IS NULL;")
    rows = cur.fetchall()

    for review_text, review_id in rows:
        polarity = TextBlob(review_text).sentiment.polarity
        sentiment = "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral"

        cur.execute("UPDATE review.raw_reviews SET sentiment = %s WHERE id = %s;", (sentiment, review_id))
    
    


    conn.commit()
    cur.close()
    conn.close()
    print("Sentiment analysis completed.")


#detect language of reviews
def detect_language_reviews():
    pg_hook = PostgresHook(postgres_conn_id="postgres_defaut")
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    cur.execute("SELECT review_text, id FROM review.raw_reviews WHERE language IS NULL;")
    rows = cur.fetchall()

    for review_text, review_id in rows:
        try:
            language = detect(review_text)
        except:
            language = "unknown"

        cur.execute("UPDATE review.raw_reviews SET language = %s WHERE id = %s;", (language, review_id))
    
    # Commit the changes


    conn.commit()
    cur.close()
    conn.close()
    print("Language detection completed.")



#1.	Clean the Data (DBT & SQL)
def normalize_and_clean_data():
    pg_hook = PostgresHook(postgres_conn_id="postgres_defaut")
    conn = pg_hook.get_conn()
    cur = conn.cursor()
    # Récupérer les données
    df = pd.read_sql("SELECT * FROM review.raw_reviews", conn)
    # Convertir en minuscule
    df['review_text'] = df['review_text'].str.lower()
    # Supprimer la ponctuation
    df['review_text'] = df['review_text'].apply(lambda x: x.translate(str.maketrans('', '', string.punctuation)))
    # Supprimer les stop words
    stop_words = set(stopwords.words('english'))  # Changer pour 'english' si nécessaire
    df['review_text'] = df['review_text'].apply(lambda x: ' '.join([word for word in x.split() if word not in stop_words]))
    # Gérer les valeurs manquantes
    df['review_text'].fillna("Avis non disponible", inplace=True)
    df['rating'].fillna(df['rating'].mean(), inplace=True)

    # Mettre à jour les données dans la base PostgreSQL
    for _, row in df.iterrows():
        
        cur.execute("""
            UPDATE review.raw_reviews
            SET review_text = %s, rating = %s
            WHERE id = %s
        """, (row['review_text'], row['rating'], int(row['id'])))



    # Commit the changes

    conn.commit()
    cur.close()
    conn.close()
    print("Data normalized and cleaned successfully.")


#remove duplicates

def remove_duplicates():
    pg_hook = PostgresHook(postgres_conn_id="postgres_defaut")
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    # Suppression des doublons en gardant la première occurrence
    delete_sql = """
        DELETE FROM review.raw_reviews
        WHERE ctid NOT IN (
            SELECT MIN(ctid)
            FROM review.raw_reviews
            GROUP BY place_id, bank_name, branch_name, location, review_text, rating, review_date
        );
    """
    cur.execute(delete_sql)
    

    conn.commit()
    cur.close()
    conn.close()

    print("Duplicate reviews removed.")
#load reviews from csv to postgres 
def Load_reviews1():
    # Get the path to the CSV file
    current_dir = os.path.dirname(__file__)
    data_path = glob.glob(os.path.join(current_dir, "input", "*.csv"))

    if not data_path:
        raise FileNotFoundError("No CSV files found in the input folder.")

    # Read the first CSV file found
    df = pd.read_csv(data_path[0])
    
    print(f"Current directory: {current_dir}")
    print(f"Data path: {data_path[0]}")
    
    if df.empty:
        print("No data found in the CSV file.")
        return
    df["review_date"] = pd.to_datetime(df["review_date"])  # Convertit timestamp Unix en datetime

    df = df.astype(object)

    # Connect to PostgreSQL via Airflow
    pg_hook = PostgresHook(postgres_conn_id="postgres_defaut")  # ✅ Correction ici
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    # Create table if not exists
    cur.execute("CREATE SCHEMA IF NOT EXISTS review;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS review.raw_reviews (
            id SERIAL PRIMARY KEY, 
            place_id TEXT,
            bank_name TEXT,
            branch_name TEXT,
            location TEXT,
            language TEXT DEFAULT NULL,
            sentiment TEXT DEFAULT NULL,
            topic TEXT DEFAULT NULL,
            review_text TEXT,
            rating FLOAT,
            review_date TIMESTAMP
        );
    """)
        # Add unique constraint (run once)
  
    # Convert DataFrame to a list of tuples for batch insertion
    records = df.to_records(index=False)
    values = [tuple(row) for row in records]

    # Insert data in batch for better performance
    insert_sql = """
        INSERT INTO review.raw_reviews 
            (place_id, bank_name, branch_name, location, review_text, rating, review_date)
        VALUES %s
       ;


    """
    execute_values(cur, insert_sql, values)
    query = """
    select * from review.raw_reviews;
    """
  
    cur.execute(query)
    conn.commit()
    # Charger les données dans un DataFrame
    df = pd.read_sql_query(query, conn)

# Exporter vers CSV
    csv_path = "/opt/airflow/dags/output/reviewsl.csv"

    # Append new data to existing CSV or create a new file if it doesn't exist
    df.to_csv(csv_path, index=False)


    # Commit the transaction
    conn.commit()

    # Close the connection
    cur.close()
    conn.close()

    print("Data stored in PostgreSQL.")



# Replace with your Google Maps API key (consider using environment variables for security)
API_KEY = "AIzaSyAj9vlR595TR2PTZFGQbhUdns91voLFMZA"
gmaps = googlemaps.Client(key=API_KEY)


def fetch_google_reviews():
    seen_places = set()
    all_reviews = []

    # Bounding box approximative du Maroc
    
    grid_points = [
        (35.7595, -5.8339), (35.5785, -5.3684), (35.1718, -5.2697), (35.2442, -3.9315),
        (34.6836, -1.9094), (35.1688, -2.9335), (34.9180, -2.3184), (34.0331, -5.0003),
        (33.8950, -5.5547), (34.2134, -4.0117), (34.2610, -6.5802), (34.0209, -6.8416),
        (34.0371, -6.7985), (33.5731, -7.5898), (33.6868, -7.3820), (33.2540, -8.5090),
        (33.0012, -7.6166), (32.8820, -6.9063), (32.3395, -6.3608), (31.9632, -6.5717),
        (32.9344, -5.6689), (32.6812, -4.7357), (31.9319, -4.4240), (31.6295, -7.9811),
        (31.5085, -9.7595), (32.2994, -9.2372), (30.4278, -9.5981), (29.6979, -9.7322),
        (28.9870, -10.0574), (27.1253, -13.1625)
    ]
    for lat, lng in grid_points:
            try:
            
                places_result = gmaps.places(
                    location=(lat, lng),
                    radius=70000,
                    type="bank",
                   
                )

                for place in places_result.get("results", []):
                    place_id = place["place_id"]
                    if place_id in seen_places:
                        continue

                    seen_places.add(place_id)
                    details = gmaps.place(
                        place_id=place_id,
                        fields=["name", "formatted_address", "review"]
                    ).get("result", {})

                    for review in details.get("reviews", []):
                        all_reviews.append({
                            'place_id': place_id,
                            'bank_name': details.get('name', ''),
                            'branch_name': details.get('name', '') + " Branch",
                            'location': details.get('formatted_address', ''),
                            'review_text': review.get('text', ''),
                            'rating': review.get('rating', 0),
                            'review_date': datetime.utcfromtimestamp(review['time'])
                        })

                
            except Exception as e:
                print(f"Error at point ({lat}, {lng}): {e}")
                break

       

    df = pd.DataFrame(all_reviews)
    df.to_csv("/opt/airflow/dags/input/reviews.csv", index=False)
    print(f"{len(df)} reviews collected from {len(seen_places)} bank branches.")
    