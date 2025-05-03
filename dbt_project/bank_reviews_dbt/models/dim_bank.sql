

SELECT DISTINCT
    bank_name,
    DENSE_RANK() OVER (ORDER BY bank_name) AS bank_id
FROM review.raw_reviews
