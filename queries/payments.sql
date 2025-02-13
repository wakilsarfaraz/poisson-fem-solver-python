-- This query returns the summary statistics for the payments column.



SELECT
  COUNT(amount) AS Num_records,
  MIN(amount) AS Min_amount,
  MAX(amount) AS Max_amount,
  SUM(amount) AS Total_amount,
  AVG(amount) AS Avg_amount
FROM payment; 