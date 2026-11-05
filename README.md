# Techincal Assesment

# Setup & Run Instructions. 
Execute the instructions from the root folder of the repository. Suggestion is to create a python virtual environment

## 1. Install Dependencies:

	pip install -r requirements.txt

##  2. Run Task 1 (Ingestion, Validation & Quarantine):
Reads local CSV input, applies strict Pydantic validation rules, routes invalid rows to quarantine, and removes duplicates based on natural keys (natural key is the key combined with all columns except transaction_id).

	python -m ingestion.ingest_transactions

##  3. Run Task 2 (Daily Account Summary Transformations & Assertions):
Computes account-level daily metrics for completed transactions and runs pytest data quality checks.

	python transformations/run_transformations.py
	pytest tests/test_assertions.py -v

##  4. Run Task 3 (Incremental Ingestion & Watermarking):
Simulates incremental execution using high-water mark timestamp persistence.

	python -m ingestion.incremental_ingest

# Technology Choice & Rationale
Common python libraries like Python pandas for data processing, pydantic for data validations adn pytest assertions for test cases

# Validation & Duplicate-Handling Strategy

## Schema Validation: 
Enforces strict ISO timestamps, positive numeric amounts, and lowercase enum checks. Invalid rows are isolated into outputs/quarantine_sample.csv with explicit error_reason metadata.   
## Deduplication: 
Natural keys across all fields (excluding transaction_id and timestamps) are evaluated to quarantine duplicate submissions.  


# Incremental & Watermark Strategy 

Tracks the maximum successfully ingested transaction_date in outputs/watermark_state.json. Subsequent runs filter source data using watermark, ensuring idempotency and preventing duplicate processing.


# Known Limitations & Improvements

## Storage Layer: 
Uses local JSON/CSV files for portability; in production, this would scale to AWS S3 / Azure ADLS Delta Lake tables.

## Orchestration: 
Manual CLI execution; in production, this would be managed via Apache Airflow or Databricks Workflows.