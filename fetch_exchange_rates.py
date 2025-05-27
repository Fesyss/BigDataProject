import requests
import json
from datetime import datetime
from google.cloud import storage, bigquery


def fetch_todays_exchange_rates():
    # ---------- 1. FETCH from API ----------
    table_type = "A"
    url = f"https://api.nbp.pl/api/exchangerates/tables/{table_type}/?format=json"
    response = requests.get(url)
    if response.status_code != 200:
        return f"❌ Failed to fetch data: status {response.status_code}"

    try:
        data = response.json()
    except Exception as e:
        return f"❌ Failed to parse JSON: {e}"

    # ---------- 2. CONVERT to NDJSON ----------
    all_lines = []
    for day in data:
        for rate in day.get("rates", []):
            line = {
                "table_type": day.get("table"),
                "effective_date": day.get("effectiveDate"),
                "currency": rate.get("currency"),
                "code": rate.get("code"),
                "mid": rate.get("mid"),
            }
            all_lines.append(json.dumps(line))

    ndjson_content = "\n".join(all_lines)
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"fx_today_{today}.ndjson"
    bucket_name = "nbp-upload-temp"

    # ---------- 3. UPLOAD to Cloud Storage ----------
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(ndjson_content, content_type="application/x-ndjson")

    # ---------- 4. LOAD to BigQuery ----------
    bq_client = bigquery.Client()
    table_id = "nbpcurrencyratesbdfinalproject.nbp_data_raw.fx_today_raw"
    uri = f"gs://{bucket_name}/{filename}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        schema=[
            bigquery.SchemaField("table_type", "STRING"),
            bigquery.SchemaField("effective_date", "DATE"),
            bigquery.SchemaField("currency", "STRING"),
            bigquery.SchemaField("code", "STRING"),
            bigquery.SchemaField("mid", "NUMERIC"),
        ],
        write_disposition="WRITE_TRUNCATE",
        time_partitioning=bigquery.TimePartitioning(field="effective_date"),
        clustering_fields=["code"],
    )

    load_job = bq_client.load_table_from_uri(uri, table_id, job_config=job_config)
    load_job.result()  # Wait for completion

    return f"✅ Downloaded NBP table A, saved as {filename}, and loaded to {table_id}"


if __name__ == "__main__":
    fetch_todays_exchange_rates()
