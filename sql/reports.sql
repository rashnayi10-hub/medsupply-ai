-- Run after python -m src.pipeline; database at output/inventory.db
SELECT hospital_id, medicine_id, medicine_name, on_hand,
       avg_daily_demand, days_of_supply, lead_time_days
FROM inventory_risk
WHERE at_stockout_risk = 1
ORDER BY days_of_supply ASC;

SELECT hospital_id,
       COUNT(*) AS tracked_medicines,
       SUM(at_stockout_risk) AS flagged_medicines
FROM inventory_risk
GROUP BY hospital_id
ORDER BY hospital_id;
