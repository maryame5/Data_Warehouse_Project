SELECT DISTINCT
    location,
    DENSE_RANK() OVER (ORDER BY location) AS location_id
FROM review.raw_reviews
