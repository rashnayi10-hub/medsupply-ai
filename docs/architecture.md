# MedSupply AI architecture

Synthetic inventory + historical consumption → CSV ingestion → validation →
inventory risk analytics → SQLite reporting.

Synthetic historical medicine consumption → time-series feature engineering →
Random Forest forecasting → holdout MAE comparison to trailing-average baseline.

## Limits
- Portfolio simulation only, not a medical device or clinical decision tool.
- No real patient data and no true hospital stock information.
- Stockout flags use simple inventory thresholds, not guaranteed shortage predictions.
- The forecast is trained on synthetic demand. Its performance does not establish
  reliability under live supply-chain disruptions.
- AWS, Spark, optimization, FDA API integration, and Generative AI are future work.
