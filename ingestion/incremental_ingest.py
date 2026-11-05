import os
import json
import logging
from datetime import datetime, timezone
from ingestion.ingest_transactions import fetch_transactions_from_file, process_raw_ingestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

WATERMARK_STORE_PATH = "outputs/watermark_state.json"

def get_current_watermark():
    if os.path.exists(WATERMARK_STORE_PATH):
        with open(WATERMARK_STORE_PATH, "r") as f:
            state = json.load(f)
            return state.get("high_watermark")
    return None

def save_watermark(watermark_value, run_label="run1"):
    os.makedirs("outputs", exist_ok=True)
    state = {"high_watermark": watermark_value, "updated_at": datetime.now(timezone.utc).isoformat()}
    with open(WATERMARK_STORE_PATH, "w") as f:
        json.dump(state, f, indent=2)
    with open(f"outputs/watermark_{run_label}.json", "w") as f:
        json.dump(state, f, indent=2)

def run_incremental_pipeline(run_label="run1"):
    current_watermark = get_current_watermark()
    logger.info(f"Running incremental ingestion from local file. Current Watermark: {current_watermark}")

    raw_data = fetch_transactions_from_file(watermark=current_watermark)
    
    if not raw_data:
        logger.info("No new records found in local file for incremental run.")
        return

    df_valid, df_quarantine = process_raw_ingestion(raw_data)

    if not df_valid.empty:
        max_dt = df_valid["transaction_date"].max()
        save_watermark(max_dt, run_label=run_label)
        logger.info(f"Updated high-water mark to: {max_dt}")

if __name__ == "__main__":
    run_incremental_pipeline(run_label="run1")