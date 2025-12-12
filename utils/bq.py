# utils/bq.py
from google.cloud import bigquery
import os, logging

PROJECT = os.environ.get("PROJECT")
client = bigquery.Client(project=PROJECT)

def run_query(sql, job_config=None):
    logging.info("Running BQ SQL (truncated): %s", sql[:300].replace("\n"," "))
    job = client.query(sql, job_config=job_config)
    return job.result()

def insert_rows(table_id, rows):
    """
    table_id: 'project.dataset.table'
    rows: list of dict
    """
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        raise RuntimeError(f"BigQuery insert errors: {errors}")
    return len(rows)
