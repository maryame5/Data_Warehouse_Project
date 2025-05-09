
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
