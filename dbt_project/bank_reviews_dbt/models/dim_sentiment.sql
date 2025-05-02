SELECT DISTINCT
    sentiment AS sentiment_label,
    DENSE_RANK() OVER (ORDER BY sentiment) AS sentiment_id
FROM review.raw_reviews

