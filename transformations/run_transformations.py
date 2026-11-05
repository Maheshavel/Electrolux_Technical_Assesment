import os
import pandas as pd
from datetime import datetime, timezone

def generate_daily_account_summary(input_path="outputs/raw_valid_transactions.json", output_dir="outputs"):
    if not os.path.exists(input_path):
        print("Raw valid transactions file not found.")
        return

    df = pd.read_json(input_path)
    if df.empty:
        print("No records available for transformation.")
        return

    # Filter completed transactions only
    df_completed = df[df["status"] == "completed"].copy()
    
    # Extract UTC calendar date (YYYY-MM-DD)
    df_completed["transaction_date"] = df_completed["transaction_date"].str.slice(0, 10)
    
    # Calculate amounts
    df_completed["debit_amt"] = df_completed.apply(lambda r: r["amount"] if r["transaction_type"] == "debit" else 0.0, axis=1)
    df_completed["credit_amt"] = df_completed.apply(lambda r: r["amount"] if r["transaction_type"] == "credit" else 0.0, axis=1)

    # Aggregate by account_id and transaction_date
    grouped = df_completed.groupby(["account_id", "transaction_date"])

    summary_rows = []
    for (acc_id, tx_date), group in grouped:
        total_debit = group["debit_amt"].sum()
        total_credit = group["credit_amt"].sum()
        net_amount = total_credit - total_debit
        txn_count = len(group)
        distinct_merchants = group["merchant_name"].nunique()
        
        # Determine top category by highest total spend for the day
        cat_spend = group.groupby("merchant_category")["amount"].sum()
        top_category = cat_spend.idxmax() if not cat_spend.empty else None

        # Distinct currencies as comma-separated string
        currencies = ", ".join(sorted(group["currency"].unique()))

        summary_rows.append({
            "account_id": acc_id,
            "transaction_date": tx_date,
            "total_debit_amount": round(total_debit, 2),
            "total_credit_amount": round(total_credit, 2),
            "net_amount": round(net_amount, 2),
            "transaction_count": txn_count,
            "distinct_merchants": distinct_merchants,
            "top_category": top_category,
            "currencies": currencies,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

    df_summary = pd.DataFrame(summary_rows)
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "daily_account_summary_sample.csv")
    df_summary.to_csv(out_file, index=False)
    print(f"Daily account summary generated successfully at {out_file}")
    return df_summary


if __name__ == "__main__":
    print("Starting daily account summary transformation...")
    generate_daily_account_summary()
    print("Transformation completed.")