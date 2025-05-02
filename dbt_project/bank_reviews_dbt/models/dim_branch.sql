SELECT DISTINCT
    branch_name,
    DENSE_RANK() OVER (ORDER BY branch_name) AS branch_id
FROM review.raw_reviews
