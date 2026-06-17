import json
import re
from datetime import datetime

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

print("🔍 Call Analysis Started (DB Driven — No LLM Pipeline)")

# ============================================================
# DB CONFIG
# ============================================================
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

# ============================================================
# UTILITIES
# ============================================================
def extract_json_from_llm(text):
    """Robustly extract JSON from an LLM response that may be wrapped in markdown."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())

# ============================================================
# BUILD JSON OUTPUT WITHOUT LLM (DB-ONLY)
# ============================================================
def build_db_only_json(transcript, agent_name, call_duration, audio_id, created_at=None):
    """
    Build the full JSON structure using ONLY database fields.
    LLM-derived fields are set to null/empty defaults.
    """
    
    # Count speaker turns from raw transcript
    speaker_00_count = transcript.count("[SPEAKER_00]") if transcript else 0
    speaker_01_count = transcript.count("[SPEAKER_01]") if transcript else 0
    
    # Build the complete JSON structure
    output = {
        # === NEW: Raw transcription field ===
        "transcription": transcript if transcript else None,
        
        # === DB-LEVEL METADATA (Real Data) ===
        "call_id": audio_id,
        "duration_sec": call_duration,
        "date": created_at.isoformat() if created_at else datetime.now().isoformat(),
        "agent_name": agent_name,
        
        # === LLM-DERIVED FIELDS (All Null/Empty — Model Not Called) ===
        "emotion": {
            "agent": {"dominant_emotion": None, "confidence": None},
            "customer": {"dominant_emotion": None, "confidence": None}
        },
        "sentiment": {
            "agent": {
                "label": None,
                "confidence": None,
                "normalized_score": None,
                "drift": [],
                "num_chunks": 0,
                "volatility": None,
                "distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "chunk_duration_sec": 35
            },
            "customer": {
                "label": None,
                "confidence": None,
                "normalized_score": None,
                "drift": [],
                "num_chunks": 0,
                "volatility": None,
                "distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "chunk_duration_sec": 35
            }
        },
        "entities": {
            "persons": [],
            "orgs": [],
            "locations": []
        },
        "metadata": {
            "agent_name": agent_name,
            "utterances": {
                "agent": speaker_00_count,
                "customer": speaker_01_count
            },
            "analysis_time": datetime.now().isoformat(),
            "call_duration_sec": call_duration
        },
        "advanced_insights": {
            "issue_detected": None,
            "primary_intent": None,
            "compliance_risk": None,
            "repeat_call_risk": None,
            "resolution_status": None,
            "sentiment_explanation": None,
            "customer_intent_strength": None,
            "dominant_customer_emotion": None
        },
        "executive_summary": None
    }
    
    return output

# ============================================================
# MAIN PIPELINE (DB DRIVEN — NO LLM)
# ============================================================
def run_analysis():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Fetch ALL relevant columns from call_audio table
    cur.execute("""
        SELECT 
            call_audio_id, 
            user_name, 
            transcribed_text, 
            call_duration_sec,
            created_at
        FROM call_audio
        WHERE analysis_done = FALSE
        AND transcribed_text IS NOT NULL
        AND transcribed_text <> ''
        LIMIT 1
    """)
    row = cur.fetchone()

    if not row:
        print("✅ No pending transcripts to analyze")
        cur.close()
        conn.close()
        return

    audio_id, agent_name, transcript, call_duration, created_at = row
    print(f"🎧 Processing Agent: {agent_name} (ID {audio_id})")

    # DEBUG preview
    print(f"   Raw transcript length: {len(transcript) if transcript else 0} chars")
    print(f"   Raw transcript preview: {transcript[:100]}...")

    # SAFETY CHECK: Skip if transcript is empty
    if not transcript or not transcript.strip():
        print(f"⚠️ Empty transcript for {audio_id}, marking as done")
        cur.execute("""
            UPDATE call_audio
            SET analysis_done = TRUE
            WHERE call_audio_id = %s
        """, (audio_id,))
        conn.commit()
        cur.close()
        conn.close()
        return

    # Build JSON output WITHOUT calling LLM
    print("   📦 Building DB-only JSON (NO LLM call)...")
    output = build_db_only_json(
        transcript=transcript,
        agent_name=agent_name,
        call_duration=call_duration,
        audio_id=audio_id,
        created_at=created_at
    )
    print("   ✅ JSON built successfully")

    # 1. Upsert analysis into call_analysis table
    # Use created_at from call_audio (sourced from call_records_test), not system time
    cur.execute("""
        INSERT INTO call_analysis (id, agent_name, call_json, created_at)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            agent_name = EXCLUDED.agent_name,
            call_json = EXCLUDED.call_json,
            created_at = EXCLUDED.created_at
    """, (audio_id, agent_name, json.dumps(output, indent=2, default=str), created_at))

    # 2. Mark as done in call_audio
    cur.execute("""
        UPDATE call_audio
        SET analysis_done = TRUE
        WHERE call_audio_id = %s
    """, (audio_id,))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Analysis stored successfully into table call_analysis")
    print(f"\n📄 SAMPLE OUTPUT (Call ID: {audio_id}):")
    print(json.dumps(output, indent=2, default=str))

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    run_analysis()