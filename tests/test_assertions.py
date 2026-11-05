import pandas as pd
import pytest

def test_daily_summary_assertions():
    summary_path = "outputs/daily_account_summary_sample.csv"
    if not pd.io.common.file_exists(summary_path):
        pytest.skip("Summary output not generated yet.")
        
    df = pd.read_csv(summary_path)

    # 1. Not Null Assertions (Equivalent to dbt not_null tests)
    assert df["account_id"].notnull().all(), "Assertion Failed: account_id contains nulls"
    assert df["transaction_date"].notnull().all(), "Assertion Failed: transaction_date contains nulls"
    assert df["net_amount"].notnull().all(), "Assertion Failed: net_amount contains nulls"

    # 2. Uniqueness Assertion (account_id + transaction_date composite primary key)
    assert df.duplicated(subset=["account_id", "transaction_date"]).sum() == 0, "Assertion Failed: Composite key is not unique"

    # 3. Business Logic Assertion (net_amount = total_credit_amount - total_debit_amount)
    calculated_net = df["total_credit_amount"] - df["total_debit_amount"]
    assert (df["net_amount"] - calculated_net).abs().max() < 1e-5, "Assertion Failed: net_amount calculation mismatch"