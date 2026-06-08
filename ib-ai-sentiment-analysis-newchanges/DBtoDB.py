import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import time

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

load_dotenv(override=True)

IST = pytz.timezone("Asia/Kolkata")

# ==============================
# SOURCE DATABASE (Prodtest)
# ==============================
SRC_DB = {
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


def sync_dbtodb():
    now_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    print(f"[{now_ist}] Starting DBtoDB sync...")

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
        return

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

    print(f"[{now_ist}] Data copied successfully to CallAudioDB.call_records_test")


# ==============================
# SCHEDULER (IST timezone)
# Set DBTODB_SCHEDULE_TIME=HH:MM in .env
# ==============================
run_time = os.getenv("DBTODB_SCHEDULE_TIME", "09:00")

try:
    hour, minute = run_time.strip().split(":")
    hour, minute = int(hour), int(minute)
except ValueError:
    print(f"Invalid DBTODB_SCHEDULE_TIME='{run_time}'. Expected HH:MM. Defaulting to 09:00 IST.")
    hour, minute = 9, 0

scheduler = BlockingScheduler(timezone=IST)
scheduler.add_job(
    sync_dbtodb,
    CronTrigger(hour=hour, minute=minute, timezone=IST),
    id="dbtodb_daily",
    name="DBtoDB daily sync",
)

next_run = scheduler.get_job("dbtodb_daily").next_run_time
print(f"Scheduler running. DBtoDB will sync daily at {hour:02d}:{minute:02d} IST.")
print(f"Next run: {next_run.astimezone(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")

scheduler.start()
