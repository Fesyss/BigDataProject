import requests
import json
from datetime import datetime
from google.cloud import storage, bigquery


def fetch_gold_history():
    bucket_name = "nbp-upload-temp"
    table_id = "nbpcurrencyratesbdfinalproject.nbp_data_raw.gold_history_raw"

    url = "https://api.nbp.pl/api/cenyzlota/2013-01-01/2025-05-26?format=json"
    response = requests.get(url)

    if response.status_code != 200:
        return f"❌ API error: {response.status_code}"

    try:
        data = response.json()
    except Exception as e:
        return f"❌ Failed to parse JSON: {e}"

    content = "\n".join(
        [
            json.dumps({"effective_date": d["data"], "price": d["cena"]})
            for d in data
            if "data" in d and "cena" in d
        ]
    )
    filename = f"gold_history_{datetime.now().date()}.ndjson"

    # Save to bucket
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(content, content_type="application/x-ndjson")

    # Load to BigQuery
    bq_client = bigquery.Client()
    uri = f"gs://{bucket_name}/{filename}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        schema=[
            bigquery.SchemaField("effective_date", "DATE"),
            bigquery.SchemaField("price", "NUMERIC"),
        ],
        write_disposition="WRITE_TRUNCATE",
        time_partitioning=bigquery.TimePartitioning(field="effective_date"),
    )

    load_job = bq_client.load_table_from_uri(uri, table_id, job_config=job_config)
    load_job.result()

    return f"✅ Loaded gold history to {table_id}"


if __name__ == "__main__":
    fetch_gold_history()
