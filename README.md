# 🏦 Bank Review Data Pipeline - README

## 📌 Objectif du projet
L’objectif de ce projet est de construire une solution de bout-en-bout pour collecter, transformer, modéliser, stocker et analyser les avis clients des agences bancaires au Maroc à partir de Google Maps. Le pipeline est entièrement automatisé à l’aide d’Airflow, et les résultats sont visualisés dans Looker Studio sous forme de dashboards interactifs. Le projet met en œuvre un ensemble d’outils modernes de traitement de données, NLP et Business Intelligence.

##  Technologies utilisées
- **Airflow** : Orchestration du pipeline.
- **PostgreSQL** : Stockage des données brutes et modélisées.
- **DBT** : Transformation des données via modèles SQL.
- **Google Maps API** : Extraction des avis clients.
- **Looker Studio** : Visualisation interactive.
- **Python** : Traitement, analyse sémantique et intégration API.
- **Docker** : Conteneurisation et déploiement local.



## 📁 Structure du projet

📆 airflow_doc
🔼— dags/

│   ├— airflowdag.py # DAG principal orchestrant toutes les étapes

│   └— storeData.py             # Fonctions Python : scraping, NLP, insertions SQL

🔼— input/

│   └— reviews.csv              # Fichier temporaire des reviews

🔼— output/

│   └— export_reviews.csv       # Données finales exportées vers Looker Studio

🔼— dbt_project/

│   └— bank_reviews_dbt         # DBT models, sources, tests

🔼— Dockerfile                   # Image Docker custom

🔼— docker-compose.yml          # Configuration complète avec services Airflow, PostgreSQL, Redis

🔼— README.md                    # Ce fichier


## 🔁 Étapes du pipeline

### 1️⃣ Collecte de données - Google Maps API
📍 Script : `fetch_google_reviews()` (dans `storeData.py`)
- Recherche des agences bancaires dans différentes villes du Maroc via coordonnées GPS.
- Les coordonnées GPS couvrent tout le Maroc via une grille de 30 points.
- Utilisation de `googlemaps.Client.places()` et `.place()` pour obtenir les avis (review_text, rating, date, etc.).
- Enregistrement dans `reviews.csv`.

### 2️⃣ Chargement initial - PostgreSQL
📍 Script : `Load_reviews1()`
- Lecture du fichier CSV.
- Création du schéma `review` et de la table `raw_reviews` si elle n'existe pas.
- Insertion des données avec dédoublonnage conditionnel.

### 3️⃣ Nettoyage & normalisation
📍 Script : `normalize_and_clean_data()`
- Passage des textes en minuscules.
- Suppression de la ponctuation et des stop words.
- Remplissage des valeurs manquantes : `review_text` → "Avis non disponible", `rating` → moyenne.

### 4️⃣ Détection de la langue
📍 Script : `detect_language_reviews()`
- Utilise `langdetect` pour détecter la langue de chaque review.
- Met à jour le champ `language`.

### 5️⃣ Analyse de sentiment
📍 Script : `analyze_sentiment()`
- Utilise `TextBlob` pour classifier chaque avis : Positif, Négatif ou Neutre.
- Met à jour le champ `sentiment` dans la base.

### 6️⃣ Extraction des thématiques (topics)
📍 Script : `extract_topics()`
- Utilisation de `gensim.LDA` sur le texte prétraité.
- Identification des 3 topics dominants.
- Mise à jour du champ `topic` par review.

### 7️⃣ Modélisation des données (Star Schema)
📍 Script : `model_data()`
- Création des tables dimensionnelles : `dim_bank`, `dim_branch`, `dim_location`, `dim_sentiment`.
- Table de faits : `fact_reviews`.
- Jointure des données nettoyées avec les dimensions.
- L’utilisation de `ON CONFLICT DO NOTHING` et des clés uniques garantit l’unicé des reviews.


### 8️⃣ Transformation via DBT
📍 Chemin : `dbt_project/bank_reviews_dbt/models/`
- `dim_*.sql` et `fact_reviews.sql`
- Tests sur les clés primaires et non-null.
- `dbt run` + `dbt test` lancés via Airflow DAG.

### 9️⃣ Export des données finales
📍 Script : `export_data()`
- Jointure finale entre `raw_reviews` et les dimensions.
- Export CSV dans `/output/export_reviews.csv`.
- Source connectée dans Looker Studio.

---

## 📊 Visualisation - Looker Studio

1. **🌐 Sentiment trend par banque et agence**
   - ✅ Type : graphique en ligne
   - Dimensions : `bank_name`, `branch_name`, `review_date`
   - Métrique : Moyenne de `rating` ou répartition `sentiment`
   - Filtre dynamique : Date, Banque, Sentiment

2. **🎡 Top sujets positifs et négatifs**
   - ✅ Type : Tableau ou graphique à barres empilées
   - Dimension : `topic`
   - Métrique : Nombre de reviews avec `sentiment = 'Positive'` ou `'Negative'`
   - Tri par fréquence

3. **📈 Classement des agences par performance**
   - ✅ Type : Bar chart
   - Dimension : `branch_name`
   - Métrique : Moyenne `rating`
   - Filtres : `bank_name`, `location`, `language`

4. **📊 Customer Experience Insights**
   - ✅ Objectif : Vue synthétique de l'expérience client
   - Visualisations utilisées :
     - Répartition des sentiments (camembert)
     - Langue des avis (camembert)
     - Distribution des notes (histogramme)
     - Courbe d’évolution de l’expérience client (graphe temporel)
     - Top agences les mieux notées (bar chart)
   - ## Exemples de graphiques inclus :
    - Répartition des sentiments
    - Langue des avis
    - Distribution des notes
    - Courbe d’évolution de l’expérience client
    - Top agences les mieux notées

⚙️ Filtres dynamiques configurés : `bank_name`, `sentiment`, `language`, `review_date`

---

## 🛠️ Déploiement Docker
- Base PostgreSQL avec volume persistant
- Airflow Scheduler + Webserver avec SMTP configuré
- dbt CLI intégré dans l’image personnalisée

Commandes utiles :
```bash
docker-compose up -d
```

---

## 📬 Alertes par e-mail
- Configurées via SMTP Gmail dans `docker-compose.yml`
- Email envoyé en cas d’échec de tâche grâce au paramètre `email_on_failure=True` dans le DAG

---

## 📝 Fichiers livrables
- ✅ `storeData.py` – Fonctions Python
- ✅ `airflowdag.py` – DAG principal
- ✅ DBT Models – `/dbt_project/bank_reviews_dbt/`
- ✅ export_reviews.csv – Données prêtes pour Looker Studio
- ✅ `README.md` – Ce fichier
- ✅ `create_schema.sql` – Script SQL de création du modèle étoile 


