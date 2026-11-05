
# Product and Platform Design Note:

* **Disclaimer** Since I couldn't get the API credentials, The current pipline is desgined to load data from local file system but in ideal scenario, the data should be fetched from the exteranl APIs. The design notes are provided with an assumption that, the current solution is using APIs.

## 1. Assumptions Challenged Before Production
* **Upstream Data Contracts:** Eventhough our raw/bronze data is stored as Json to avoid strict schema validations, it is good to maintain sctrict contracts with the upstream data API providers to keep the schema as it is.
* **State Management:** Relied on local JSON state files for watermarking; production requires distributed state stores (e.g., Delta table transaction logs or database metadata tables).

## 2. Production Monitoring and Alerting
* **Quarantine Rate Monitoring:** Trigger alerts if the ratio of quarantined records exceeds 5% of total ingestion volume or any other reasonable threshold value, indicating upstream data degradation.

## 3. Reusability for Future APIs
* The current ingestions logic works works strictly for the given file, this logic needs to be abstracted into a reusable module with parameterized schema and any new APIs needs to be authenticated with an authorization header.

## 4. Building Trust in `daily_account_summary`
* **Automated Data Assertions:** Embed pre- and post-computation checks verifying primary key uniqueness and financial balance reconciliation ($Total\ Credits - Total\ Debits = Net\ Amount$).


## 5. Trade-offs Made Due to Time Limits
* Since this is worked with a small sample file, the data is stored in local environmnet. In production, the volume of data will be huge, we may need distributed processing frameworks like spark(For eg: Databricks can be leveraged)