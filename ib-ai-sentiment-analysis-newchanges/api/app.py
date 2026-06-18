import whisperx
import gc
import torch
import psycopg2
from psycopg2 import pool
import boto3
import json
import os
import tempfile
import time
import threading
import subprocess
from urllib.parse import urlparse
from whisperx.diarize import DiarizationPipeline
import uvicorn
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import os
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(override=True)
app = FastAPI()

# ============================================================
# POSTGRES CONFIG
# ============================================================

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}


# ============================================================
# POSTGRES CONNECTION POOL (FASTER)
# ============================================================

connection_pool = psycopg2.pool.SimpleConnectionPool(
    1,
    10,
    **DB_CONFIG
)

# ============================================================
# S3 CLIENT
# ============================================================

s3 = boto3.client(
    "s3",
    region_name=os.getenv("REGION_NAME")
)

# ============================================================
# LOAD MODELS ONCE
# ============================================================
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)
hf_token = os.getenv("hf_token")

asr_options = {
    "repetition_penalty": 1.2,
    "condition_on_previous_text": False,
    "no_speech_threshold": 0.6,
    "compression_ratio_threshold": 2.4
}

vad_options = {
    "vad_onset": 0.500,
    "vad_offset": 0.363
}

print("Loading WhisperX model...")

model = whisperx.load_model(
    "medium",
    device,
    compute_type="float16",
    language="en",
    asr_options=asr_options,
    vad_options=vad_options
)

print("Loading alignment model...")

model_a, metadata = whisperx.load_align_model(
    language_code="en",
    device=device
)

print("Loading diarization model...")

diarize_model = DiarizationPipeline(
    use_auth_token=hf_token,
    device=device
)

# ============================================================
# DOWNLOAD SINGLE AUDIO
# ============================================================

def download_audio(call_id, s3_link):

    parsed_url = urlparse(s3_link)

    if s3_link.startswith("s3://"):
        bucket_name = parsed_url.netloc
        s3_key = parsed_url.path.lstrip("/")
    else:
        bucket_name = parsed_url.netloc.split(".")[0]
        s3_key = parsed_url.path.lstrip("/")

    # Preserve the original file extension from S3 so ffmpeg can parse it correctly.
    # Hardcoding .wav breaks calls when the actual file is .mp3, .amr, etc.
    original_ext = os.path.splitext(s3_key)[1] or ".wav"
    temp_audio_path = os.path.join(
        tempfile.gettempdir(),
        f"{call_id}{original_ext}"
    )

    s3.download_file(bucket_name, s3_key, temp_audio_path)

    file_size = os.path.getsize(temp_audio_path)
    if file_size == 0:
        raise RuntimeError(f"Downloaded audio file is empty (0 bytes) for call {call_id}: {s3_link}")

    print(f"Downloaded {file_size} bytes from {s3_key} -> {temp_audio_path}")
    return temp_audio_path

# ============================================================
# AUDIO PRE-CONVERSION
# ============================================================

def convert_audio_for_whisperx(audio_path):
    """
    PBX systems often store audio as .wav but with non-standard codecs
    (GSM 6.10, G.711 μ-law/A-law) that ffmpeg can't auto-detect.
    This converts the file to plain 16kHz mono PCM WAV before WhisperX.
    """
    out_path = audio_path + "_pcm.wav"

    attempts = [
        # (description, extra_input_flags)
        ("auto-detect",    []),
        ("force WAV",      ["-f", "wav"]),
        ("G.711 mulaw",    ["-f", "mulaw", "-ar", "8000", "-ac", "1"]),
        ("G.711 alaw",     ["-f", "alaw",  "-ar", "8000", "-ac", "1"]),
        ("GSM 6.10",       ["-f", "gsm",   "-ar", "8000"]),
    ]

    last_err = ""
    for desc, input_flags in attempts:
        cmd = ["ffmpeg", "-y"] + input_flags + [
            "-i", audio_path,
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            out_path
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            print(f"Audio converted using: {desc}")
            return out_path
        last_err = result.stderr.decode()[-300:]

    raise RuntimeError(
        f"Cannot decode audio file {audio_path} in any known format.\n"
        f"Last ffmpeg error: {last_err}"
    )

# ============================================================
# TRANSCRIPTION FUNCTION
# ============================================================

def process_call(call_id, call_created_at=None):

    conn = connection_pool.getconn()
    cur = conn.cursor()
    audio_path = None
    converted_path = None

    try:

        # ===============================
        # FETCH CALL DATA
        # ===============================
        cur.execute("""
            SELECT agent_id, s3_file_path,conversation_duration
            FROM call_records_test
            WHERE source_pbx_call_id = %s
        """, (call_id,))

        row = cur.fetchone()
        if not row:
            print(f"Call {call_id} not found in call_records_test")
            return

        agent_id, s3_link, conversation_duration = row
        if conversation_duration is None or conversation_duration == '':
            conversation_duration = 0
        else:
            conversation_duration = int(float(conversation_duration))

        # ===============================
        # GET AGENT NAME
        # ===============================
        cur.execute("""
            SELECT agent_name
            FROM agents_numbers
            WHERE phone_number = %s
        """, (agent_id,))

        agent_row = cur.fetchone()
        if not agent_row:
            cur.execute("""
                SELECT source_pbx_call_id
                FROM call_records_test
                WHERE source_pbx_call_id = %s
            """, (call_id,))

            source_pbx_row = cur.fetchone()
            source_pbx_call_id = source_pbx_row[0] if source_pbx_row else call_id

            cur.execute("""
                INSERT INTO call_audio (
                    call_audio_id,
                    call_recording_link,
                    status,
                    created_at,
                    call_duration_sec
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                source_pbx_call_id,
                s3_link,
                "Not processed",
                call_created_at,
                conversation_duration
            ))
            conn.commit()
            print(f"Call {call_id} skipped - Agent ID {agent_id} not found in agents_numbers")
            return

        user_name = agent_row[0]

        # ===============================
        # DOWNLOAD + LOAD AUDIO
        # ===============================
        audio_path = download_audio(call_id, s3_link)
        print(f"STEP 2 - Audio downloaded: {audio_path}")

        converted_path = convert_audio_for_whisperx(audio_path)
        audio = whisperx.load_audio(converted_path)
        print("STEP 3 - Audio loaded")

        # ===============================
        # TRANSCRIBE AUDIO
        # ===============================
        result = model.transcribe(audio, batch_size=32, language="en")
        print("STEP 4 - Transcription finished")

        # ===============================
        # ALIGN WORDS
        # ===============================
        result = whisperx.align(
            result["segments"],
            model_a,
            metadata,
            audio,
            device
        )
        print("STEP 5 - Alignment finished")

        # ===============================
        # DIARIZATION
        # ===============================
        diarize_segments = diarize_model(
            audio,
            min_speakers=2,
            max_speakers=2
        )
        print("STEP 6 - Diarization finished")

        result = whisperx.assign_word_speakers(
            diarize_segments,
            result
        )

        # ===============================
        # BUILD FINAL TRANSCRIPT (Speaker labels from diarization)
        # ===============================
        final_transcript = []

        for segment in result["segments"]:
            speaker = segment.get("speaker", "UNKNOWN")
            text = segment["text"].strip()
            final_transcript.append(f"[{speaker}]: {text}")

        # ===============================
        # STORE IN DATABASE
        # ===============================
        cur.execute("""
            INSERT INTO call_audio (
                call_audio_id,
                user_name,
                audio_path,
                call_recording_link,
                transcribed_text,
                status,
                confidence_score,
                created_at,
                call_duration_sec
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            call_id,
            user_name,
            audio_path,
            s3_link,
            "\n".join(final_transcript),
            "processed",
            0.0,
            call_created_at,
            conversation_duration
        ))

        conn.commit()

        print(f"✅ Finished call {call_id}")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error processing call {call_id}: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        for path in [audio_path, converted_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"Cleaned up: {path}")
                except Exception as cleanup_error:
                    print(f"Failed to cleanup {path}: {cleanup_error}")

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()

        cur.close()
        connection_pool.putconn(conn)

# ============================================================
# BACKGROUND WORKER
# ============================================================

def background_worker():
    while True:
        conn = None
        try:
            conn = connection_pool.getconn()
            cur = conn.cursor()

            cur.execute("""
                SELECT w.source_pbx_call_id, w.created_at
                FROM call_records_test w
                LEFT JOIN call_audio c
                ON w.source_pbx_call_id = c.call_audio_id
                WHERE c.call_audio_id IS NULL
                ORDER BY w.source_pbx_call_id
                LIMIT 1
            """)

            rows = cur.fetchall()

            if rows:
                print(f"Found {len(rows)} new calls")

            for row in rows:
                call_id, call_created_at = row[0], row[1]
                print("Processing call:", call_id)
                process_call(call_id, call_created_at)

            cur.close()
        except Exception as e:
            print(f"Worker error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                connection_pool.putconn(conn)

        time.sleep(10)

# ============================================================
# START WORKER WHEN API STARTS
# ============================================================

@app.on_event("startup")
def start_worker():

    thread = threading.Thread(target=background_worker)
    thread.daemon = True
    thread.start()

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
