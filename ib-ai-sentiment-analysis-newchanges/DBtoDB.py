import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv(override=True)
import os
print("DEBUG DEST_USER:", repr(os.getenv("USER")))
print("DEBUG DEST_PASSWORD:", repr(os.getenv("PASSWORD")))
print("DEBUG DEST_HOST:", repr(os.getenv("HOST")))
print("DEBUG DEST_DB_NAME:", repr(os.getenv("DB_NAME")))
print("DEBUG DEST_DB_NAME:", repr(os.getenv("PORT")))
# ==============================
# SOURCE DATABASE (Prodtest)
# ==============================
SRC_DB =  {
    "dbname": os.getenv("SOURCE_DB_NAME"),
    "user": os.getenv("SOURCE_USER"),
    "password": os.getenv("SOURCE_PASSWORD"),
    "host": os.getenv("SOURCE_HOST"),
    "port": os.getenv("SOURCE_PORT")
}

# ==============================
# DESTINATION DATABASE (CallAudioDB)
# ==============================
DEST_DB = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("USER"),
    "password": os.getenv("PASSWORD"),
    "host": os.getenv("HOST"),
    "port": 5432
}

# ==============================
# STEP 1 - GET YESTERDAY DATE
# ==============================
#yesterday = (datetime.now() - timedelta(days=1)).date()
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

print(f"Fetching data where processed_date = {yesterday}")

# ==============================
# STEP 2 - CONNECT TO SOURCE DB
# ==============================
src_conn = psycopg2.connect(**SRC_DB)

query = """
SELECT *
FROM call_details
WHERE processed_date = %s
AND conversation_duration >= 60
"""

df = pd.read_sql(query, src_conn, params=[yesterday])

src_conn.close()

print(f"Rows fetched: {len(df)}")

if df.empty:
    print("No data found for yesterday.")
    exit()

# ==============================
# STEP 3 - CONNECT TO DEST DB
# ==============================
dest_conn = psycopg2.connect(**DEST_DB)
cursor = dest_conn.cursor()

insert_query = """
INSERT INTO call_records_test (
    source_pbx_call_id,
    agent_id,
    calling_number,
    called_number,
    call_type,
    call_connected,
    conversation_duration,
    call_start_time,
    call_end_time,
    call_status,
    voice_file_path_local,
    station_id,
    s3_file_path,
    processed_date,
    created_at
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s
)   
ON CONFLICT (source_pbx_call_id) DO NOTHING;
"""

# ==============================
# STEP 4 - INSERT ROWS
# ==============================
for _, row in df.iterrows():
    cursor.execute(insert_query, (
        row["source_pbx_call_id"],
        row["agent_id"],
        row["calling_number"],
        row["called_number"],
        row["call_type"],
        row["call_connected"],
        row["conversation_duration"],
        row["call_start_time"],
        row["call_end_time"],
        row["call_status"],
        row["voice_file_path_local"],
        row["station_id"],
        row["s3_file_path"],
        row["processed_date"],
        row["created_at"]
    ))

dest_conn.commit()
cursor.close()
dest_conn.close()

print("Data copied successfully to CallAudioDB.call_records_test")
