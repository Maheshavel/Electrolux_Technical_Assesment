import os
import json
import logging
from datetime import datetime, timezone
import pandas as pd
from pydantic import BaseModel, ValidationError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

VALID_CURRENCIES = {"USD", "EUR", "GBP", "CHF", "JPY", "AUD", "CAD"}
VALID_MERCHANT_CATEGORIES = {
    "e-commerce", "travel", "food_and_beverage", "groceries", 
    "electronics", "retail", "entertainment", "health", 
    "transportation", "home_and_garden", "payroll", "transfer"
}

class TransactionSchema(BaseModel):
    transaction_id: str
    account_id: str
    transaction_date: str
    amount: float
    currency: str
    transaction_type: str
    merchant_name: str
    merchant_category: str
    status: str
    country_code: str

    def validate_business_rules(self):
        errors = []
        if not (self.transaction_id.startswith("TXN-") and self.transaction_id[4:].isdigit()):
            errors.append(f"Invalid transaction_id format: {self.transaction_id}")
            
        if not (self.account_id.startswith("ACC-") and self.account_id[4:].isdigit()):
            errors.append(f"Invalid account_id format: {self.account_id}")

        try:
            dt = datetime.fromisoformat(self.transaction_date.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                errors.append("Timestamp must be timezone-aware")
        except ValueError:
            errors.append(f"Invalid ISO 8601 timestamp: {self.transaction_date}")

        if self.amount <= 0:
            errors.append(f"Amount must be > 0, got {self.amount}")

        if self.currency not in VALID_CURRENCIES:
            errors.append(f"Invalid currency: {self.currency}")

        if self.transaction_type not in {"debit", "credit"}:
            errors.append(f"Invalid transaction_type (must be lowercase debit/credit): {self.transaction_type}")

        if not self.merchant_name or not str(self.merchant_name).strip():
            errors.append("Merchant name cannot be empty or whitespace-only")

        if self.merchant_category not in VALID_MERCHANT_CATEGORIES:
            errors.append(f"Invalid merchant_category: {self.merchant_category}")

        if self.status not in {"completed", "pending", "failed", "reversed"}:
            errors.append(f"Invalid status (must be lowercase): {self.status}")

        if not (isinstance(self.country_code, str) and len(self.country_code) == 2 and self.country_code.isupper()):
            errors.append(f"Invalid ISO alpha-2 country code: {self.country_code}")

        return errors

def fetch_transactions_from_file(file_path="inputs/transactions.csv", watermark=None):
    logger.info(f"Reading transactions from local file: {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Transactions file not found at {file_path}. Please ensure input/transactions.csv exists.")
    
    df = pd.read_csv(file_path)
    
    # Handle optional watermark filtering for incremental runs
    if watermark and "transaction_date" in df.columns:
        df = df[df["transaction_date"] >= watermark]
        logger.info(f"Filtered {len(df)} records newer than watermark {watermark}")
        
    return df.to_dict(orient="records")

def process_raw_ingestion(raw_data, output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)
    valid_records = []
    quarantine_records = []
    ingestion_timestamp = datetime.now(timezone.utc).isoformat()

    for item in raw_data:
        try:
            parsed = TransactionSchema(**item)
            rule_errors = parsed.validate_business_rules()
            
            if rule_errors:
                item_q = item.copy()
                item_q["error_reason"] = "; ".join(rule_errors)
                item_q["ingestion_timestamp"] = ingestion_timestamp
                quarantine_records.append(item_q)
            else:
                item_v = item.copy()
                item_v["ingestion_timestamp"] = ingestion_timestamp
                valid_records.append(item_v)
                
        except ValidationError as e:
            item_q = item.copy()
            item_q["error_reason"] = str(e)
            item_q["ingestion_timestamp"] = ingestion_timestamp
            quarantine_records.append(item_q)

    df_valid = pd.DataFrame(valid_records)
    if not df_valid.empty:
        natural_key_cols = [c for c in df_valid.columns if c != "transaction_id" and c != "ingestion_timestamp"]
        duplicates_mask = df_valid.duplicated(subset=natural_key_cols, keep='first')
        df_duplicates = df_valid[duplicates_mask].copy()
        
        if not df_duplicates.empty:
            df_duplicates["error_reason"] = "Duplicate transaction based on natural key"
            df_duplicates["ingestion_timestamp"] = ingestion_timestamp
            quarantine_records.extend(df_duplicates.to_dict(orient="records"))
            
        df_valid_deduped = df_valid[~duplicates_mask].reset_index(drop=True)
    else:
        df_valid_deduped = df_valid

    df_quarantine = pd.DataFrame(quarantine_records)
    
    df_valid_deduped.to_json(os.path.join(output_dir, "raw_valid_transactions.json"), orient="records", indent=2)
    if not df_quarantine.empty:
        df_quarantine.to_csv(os.path.join(output_dir, "quarantine_sample.csv"), index=False)

    logger.info(f"Ingestion complete. Valid unique records: {len(df_valid_deduped)}, Quarantined records: {len(df_quarantine)}")
    return df_valid_deduped, df_quarantine

if __name__ == "__main__":
    logger.info("Starting local file ingestion job...")
    raw_data = fetch_transactions_from_file()
    if raw_data:
        process_raw_ingestion(raw_data)
        logger.info("Ingestion job completed successfully.")
    else:
        logger.warning("No records found in local file.")