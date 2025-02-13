-- This query returns the summary statistics of the film duration.





SELECT
  MIN(length) AS min_length,
  MAX(length) AS max_length,
  SUM(length) AS total_length,
  CAST(AVG(length) AS DECIMAL(8,2)) AS avg_length
FROM film;