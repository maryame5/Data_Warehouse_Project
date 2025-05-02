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
LEFT JOIN review.dim_sentiment ds ON rr.sentiment = ds.sentiment_label
