#### this is prod sentiment takes transcription and gives analysis using gemma date:- 30-04-26
'''import json
import re
from datetime import datetime

import psycopg2
from ollama import Client
from dotenv import load_dotenv
import os

load_dotenv()

print("🔍 Call Analysis Started (DB Driven — LLM Pipeline)")

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
# OLLAMA CLIENT
# ============================================================
client = Client(host=os.getenv("OLLAMA_HOST", "http://ollama:11434"))
LLM_MODEL = "gemma4:e4b"

# ============================================================
# UTILITIES
# ============================================================
def clean_line(line):
    return re.sub(r"^\[(agent|customer)\]\s*:\s*", "", line, flags=re.I).strip()

def parse_lines(text):
    agent, customer = [], []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\[agent\]", line, flags=re.I):
            agent.append(clean_line(line))
        elif re.match(r"^\[customer\]", line, flags=re.I):
            customer.append(clean_line(line))
    return agent, customer

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
# LLM COMPREHENSIVE ANALYSIS
# ============================================================
def llm_analyze(transcript, agent_name, call_duration):
    """Send transcript to LLM and return the full structured analysis JSON."""
    agent_lines, customer_lines = parse_lines(transcript)

    # Truncate safely to stay well within the 50k context window
    safe_transcript = transcript[:45000]

    prompt = f"""You are an expert conversation analyst. Analyze the following transcript and provide a detailed structured report.

CRITICAL: The transcript uses [agent] and [customer] labels to identify speakers. Use these labels internally for analysis, but DO NOT include speaker tags in the executive summary output.

TRANSCRIPT:
{safe_transcript}

ANALYSIS REQUIREMENTS:

1. **Emotion Analysis**
   - Analyze dominant emotion separately for AGENT and CUSTOMER
   - For each, provide:
     * dominant_emotion: The primary emotion detected (e.g., neutral, surprise, frustration, satisfaction, confusion, anger, happiness)
     * confidence: Score from 0.0 to 1.0

2. **Sentiment Analysis**
   - Analyze sentiment separately for AGENT and CUSTOMER
   - For each party, provide:
     * label: NEUTRAL, POSITIVE, or NEGATIVE
     * confidence: Score from 0.0 to 1.0
     * normalized_score: Overall sentiment score from -100 (extremely negative) to +100 (extremely positive), 0 = neutral
     * drift: Array of sentiment scores (-100 to +100) for each chronological chunk of the conversation. Use chunk_duration_sec of approximately 35 seconds per chunk, or adjust based on conversation length.
     * num_chunks: Number of chunks analyzed
     * volatility: Measure of sentiment fluctuation (0.0 = perfectly stable, higher = more volatile)
     * distribution: Object mapping sentiment labels to count of chunks (e.g., {{"neutral": 2, "positive": 1}})
     * chunk_duration_sec: Approximate duration of each chunk in seconds

3. **Named Entity Recognition (NER)**
   Extract and categorize all explicit mentions from the entire transcript (do NOT attribute to speaker):
   - **persons**: Any individuals mentioned by name
   - **orgs**: Organizations, companies, institutions, firms
   - **locations**: Places, cities, countries, addresses mentioned

4. **Metadata Extraction**
   - **agent_name**: Name of the agent if explicitly stated in the transcript, otherwise null
   - **utterances**: Object with count of turns for agent and customer
   - **analysis_time**: Current timestamp in ISO 8601 format (e.g., 2026-04-22T11:41:54.066931)
   - **call_duration_sec**: Total call duration in seconds if mentioned or inferable, otherwise null

5. **Advanced Insights**
   - **issue_detected**: Boolean indicating if a clear problem or complaint was raised
   - **primary_intent**: Single phrase describing the main purpose (e.g., "General inquiry", "Bond Enquiry", "Complaint", "Investment Enquiry")
   - **compliance_risk**: Risk level - "Low", "Medium", or "High"
   - **repeat_call_risk**: Likelihood of callback - "Low", "Medium", or "High"
   - **resolution_status**: Current state - "Resolved", "Unresolved", "Partial", "Follow-up required", or "Escalated"
   - **sentiment_explanation**: 1-2 sentence explanation of why the sentiment/emotion scores were assigned
   - **customer_intent_strength**: "High", "Medium", or "Low" - how committed/determined the customer was
   - **dominant_customer_emotion**: The single most prevalent customer emotion across the call

6. **Executive Summary**
   - Provide 4-6 factual, objective sentences summarizing what occurred in the conversation
   - Focus on key facts, requests, responses, and outcomes
   - Do NOT include speaker labels or sentiment tags in this text

OUTPUT FORMAT (JSON):
{{
    "emotion": {{
        "agent": {{"dominant_emotion": "", "confidence": 0.0}},
        "customer": {{"dominant_emotion": "", "confidence": 0.0}}
    }},
    "sentiment": {{
        "agent": {{
            "label": "NEUTRAL/POSITIVE/NEGATIVE",
            "confidence": 0.0,
            "normalized_score": 0,
            "drift": [0],
            "num_chunks": 0,
            "volatility": 0.0,
            "distribution": {{"neutral": 0}},
            "chunk_duration_sec": 35
        }},
        "customer": {{
            "label": "NEUTRAL/POSITIVE/NEGATIVE",
            "confidence": 0.0,
            "normalized_score": 0,
            "drift": [0],
            "num_chunks": 0,
            "volatility": 0.0,
            "distribution": {{"neutral": 0}},
            "chunk_duration_sec": 35
        }}
    }},
    "entities": {{"persons": [], "orgs": [], "locations": []}},
    "metadata": {{
        "agent_name": null,
        "utterances": {{"agent": 0, "customer": 0}},
        "analysis_time": "",
        "call_duration_sec": null
    }},
    "advanced_insights": {{
        "issue_detected": false,
        "primary_intent": "",
        "compliance_risk": "Low",
        "repeat_call_risk": "Low",
        "resolution_status": "",
        "sentiment_explanation": "",
        "customer_intent_strength": "High",
        "dominant_customer_emotion": ""
    }},
    "executive_summary": "4-6 factual sentences summarizing the conversation."
}}

RULES:
- Use ONLY information explicitly stated in the transcript
- Do NOT output a tagged transcript reconstruction or per-line speaker labels
- If a field cannot be determined from the transcript, use null or empty arrays rather than guessing
- For drift arrays, divide the conversation into roughly equal time-based chunks (default ~35 sec each) and score each chunk
- Confidence scores must be between 0.0 and 1.0
- Sentiment normalized_score must be between -100 and +100
- analysis_time should reflect the current analysis timestamp
- utterance counts should reflect actual speaker turns in the transcript
- Keep executive_summary factual and objective; avoid interpretive language
- normalized_score and drift values MUST be whole INTEGERS between -100 and +100. 
- NEVER output decimals like 0.5 or 0.1. Use values like: -100, -75, -50, -25, 0, 25, 50, 75, 100.
"""

    response = client.chat(
        model=LLM_MODEL,
        options={"num_ctx": 50000},
        messages=[{"role": "user", "content": prompt}]
    )

    raw_content = response["message"]["content"].strip()

    # Parse JSON with fallback safety net
    try:
        result = extract_json_from_llm(raw_content)
    except Exception as e:
        print(f"⚠️ Failed to parse LLM JSON: {e}")
        print(f"   Raw preview: {raw_content[:500]}")
        result = {
            "emotion": {
                "agent": {"dominant_emotion": "neutral", "confidence": 0.0},
                "customer": {"dominant_emotion": "neutral", "confidence": 0.0}
            },
            "sentiment": {
                "agent": {
                    "label": "NEUTRAL", "confidence": 0.0, "normalized_score": 0,
                    "drift": [], "num_chunks": 0, "volatility": 0.0,
                    "distribution": {}, "chunk_duration_sec": 35
                },
                "customer": {
                    "label": "NEUTRAL", "confidence": 0.0, "normalized_score": 0,
                    "drift": [], "num_chunks": 0, "volatility": 0.0,
                    "distribution": {}, "chunk_duration_sec": 35
                }
            },
            "entities": {"persons": [], "orgs": [], "locations": []},
            "metadata": {},
            "advanced_insights": {
                "issue_detected": False,
                "primary_intent": "General inquiry",
                "compliance_risk": "Low",
                "repeat_call_risk": "Low",
                "resolution_status": "Follow-up required",
                "sentiment_explanation": "Unable to analyze due to response parsing error.",
                "customer_intent_strength": "Medium",
                "dominant_customer_emotion": "neutral"
            },
            "executive_summary": "Analysis could not be completed due to response parsing failure."
        }

    # Override metadata with ground-truth from DB / code
    result["metadata"] = {
        "agent_name": agent_name,
        "analysis_time": datetime.now().isoformat(),
        "call_duration_sec": call_duration,
        "utterances": {
            "agent": len(agent_lines),
            "customer": len(customer_lines)
        }
    }

    return result

# ============================================================
# MAIN PIPELINE (DB DRIVEN)
# ============================================================
def run_analysis():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT call_audio_id, user_name, transcribed_text, call_duration_sec
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

    audio_id, agent_name, transcript, call_duration = row
    print(f"🎧 Processing Agent: {agent_name} (ID {audio_id})")

    # DEBUG preview
    print(f"   Raw transcript length: {len(transcript)} chars")
    print(f"   Raw transcript preview: {transcript[:100]}...")

    agent_lines, customer_lines = parse_lines(transcript)
    agent_text = " ".join(agent_lines)
    customer_text = " ".join(customer_lines)

    print(f"   Parsed: {len(agent_lines)} agent lines, {len(customer_lines)} customer lines")
    print(f"   Agent text: {len(agent_text)} chars, Customer text: {len(customer_text)} chars")

    # SAFETY CHECK: Skip if both are empty
    if not agent_text.strip() and not customer_text.strip():
        print(f"⚠️ No agent/customer text parsed for {audio_id}, marking as done")
        cur.execute("""
            UPDATE call_audio
            SET analysis_done = TRUE
            WHERE call_audio_id = %s
        """, (audio_id,))
        conn.commit()
        cur.close()
        conn.close()
        return

    # Run comprehensive LLM analysis
    print("   🤖 Sending to LLM for comprehensive analysis...")
    output = llm_analyze(transcript, agent_name, call_duration)
    print("   ✅ LLM analysis complete")

    # 1. Upsert analysis (won't crash even if already exists)
    cur.execute("""
        INSERT INTO call_analysis (id, agent_name, call_json, created_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (id) DO UPDATE SET
            agent_name = EXCLUDED.agent_name,
            call_json = EXCLUDED.call_json,
            created_at = NOW()
    """, (audio_id, agent_name, json.dumps(output)))

    # 2. Mark as done
    cur.execute("""
        UPDATE call_audio
        SET analysis_done = TRUE
        WHERE call_audio_id = %s
    """, (audio_id,))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Analysis stored successfully into table call_analysis")

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":

'''
import json
import re
from datetime import datetime

import psycopg2
from ollama import Client
from dotenv import load_dotenv
import os

load_dotenv()

print("🔍 Call Analysis Started (DB Driven — LLM Pipeline)")

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
# OLLAMA CLIENT
# ============================================================
client = Client(host=os.getenv("OLLAMA_HOST", "http://ollama:11434"))
LLM_MODEL = "gemma4:e4b"

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
# LLM COMPREHENSIVE ANALYSIS
# ============================================================
def llm_analyze(transcript, agent_name, call_duration):
    """Send transcript to LLM and return the full structured analysis JSON."""
    
    # Truncate safely to stay well within the 50k context window
    safe_transcript = transcript[:45000]

    prompt = f"""You are an expert conversation analyst. Analyze the following transcript and provide a detailed structured report.

CRITICAL: The transcript uses [SPEAKER_00] and [SPEAKER_01] labels to identify speakers.
- [SPEAKER_00] is typically the agent/call center representative
- [SPEAKER_01] is typically the customer/caller
Use these labels internally for analysis, but DO NOT include speaker tags in the executive summary output.

TRANSCRIPT:
{safe_transcript}

ANALYSIS REQUIREMENTS:

1. **Emotion Analysis**
   - Analyze dominant emotion separately for SPEAKER_00 (agent) and SPEAKER_01 (customer)
   - For each, provide:
     * dominant_emotion: The primary emotion detected (e.g., neutral, surprise, frustration, satisfaction, confusion, anger, happiness)
     * confidence: Score from 0.0 to 1.0

2. **Sentiment Analysis**
   - Analyze sentiment separately for SPEAKER_00 (agent) and SPEAKER_01 (customer) it should be intent based you figure which could be agent and customer.
   - For each party, provide:
     * label: NEUTRAL, POSITIVE, or NEGATIVE
     * confidence: Score from 0.0 to 1.0
     * normalized_score: Overall sentiment score as an INTEGER from -100 (extremely negative) to +100 (extremely positive), 0 = neutral. Use whole numbers only: -100, -75, -50, -25, 0, 25, 50, 75, 100. NEVER use decimals like 0.5 or 0.1.
     * drift: Array of sentiment scores as INTEGERS (-100 to +100) for each chronological chunk of the conversation. Use whole numbers only. Use chunk_duration_sec of approximately 35 seconds per chunk, or adjust based on conversation length.
     * num_chunks: Number of chunks analyzed
     * volatility: Measure of sentiment fluctuation (0.0 = perfectly stable, higher = more volatile)
     * distribution: Object with EXACT keys "positive", "neutral", "negative" mapping to count of chunks (e.g., {{"positive": 2, "neutral": 1, "negative": 0}})
     * chunk_duration_sec: Approximate duration of each chunk in seconds

3. **Named Entity Recognition (NER)**
   Extract and categorize all explicit mentions from the entire transcript (do NOT attribute to speaker):
   - **persons**: Any individuals mentioned by name
   - **orgs**: Organizations, companies, institutions, firms
   - **locations**: Places, cities, countries, addresses mentioned

4. **Metadata Extraction**
   - **agent_name**: Name of the agent if explicitly stated in the transcript, otherwise null
   - **utterances**: Object with count of turns for agent (SPEAKER_00) and customer (SPEAKER_01)
   - **analysis_time**: Current timestamp in ISO 8601 format (e.g., 2026-04-22T11:41:54.066931)
   - **call_duration_sec**: Total call duration in seconds if mentioned or inferable, otherwise null

5. **Advanced Insights**
   - **issue_detected**: Boolean indicating if a clear problem or complaint was raised
   - **primary_intent**: Single phrase describing the main purpose (e.g., "General inquiry", "Bond Enquiry", "Complaint", "Investment Enquiry")
   - **compliance_risk**: Risk level - "Low", "Medium", or "High"
   - **repeat_call_risk**: Likelihood of callback - "Low", "Medium", or "High"
   - **resolution_status**: Current state - "Resolved", "Unresolved", "Partial", "Follow-up required", or "Escalated"
   - **sentiment_explanation**: 1-2 sentence explanation of why the sentiment/emotion scores were assigned
   - **customer_intent_strength**: "High", "Medium", or "Low" - how committed/determined the customer was
   - **dominant_customer_emotion**: The single most prevalent customer emotion across the call

6. **Executive Summary**
   - Provide 4-6 factual, objective sentences summarizing what occurred in the conversation
   - Focus on key facts, requests, responses, and outcomes
   - Do NOT include speaker labels or sentiment tags in this text

OUTPUT FORMAT (JSON):
{{
    "emotion": {{
        "agent": {{"dominant_emotion": "", "confidence": 0.0}},
        "customer": {{"dominant_emotion": "", "confidence": 0.0}}
    }},
    "sentiment": {{
        "agent": {{
            "label": "NEUTRAL",
            "confidence": 0.0,
            "normalized_score": 0,
            "drift": [0],
            "num_chunks": 0,
            "volatility": 0.0,
            "distribution": {{"positive": 0, "neutral": 0, "negative": 0}},
            "chunk_duration_sec": 35
        }},
        "customer": {{
            "label": "NEUTRAL",
            "confidence": 0.0,
            "normalized_score": 0,
            "drift": [0],
            "num_chunks": 0,
            "volatility": 0.0,
            "distribution": {{"positive": 0, "neutral": 0, "negative": 0}},
            "chunk_duration_sec": 35
        }}
    }},
    "entities": {{"persons": [], "orgs": [], "locations": []}},
    "metadata": {{
        "agent_name": null,
        "utterances": {{"agent": 0, "customer": 0}},
        "analysis_time": "",
        "call_duration_sec": null
    }},
    "advanced_insights": {{
        "issue_detected": false,
        "primary_intent": "",
        "compliance_risk": "Low",
        "repeat_call_risk": "Low",
        "resolution_status": "",
        "sentiment_explanation": "",
        "customer_intent_strength": "High",
        "dominant_customer_emotion": ""
    }},
    "executive_summary": "4-6 factual sentences summarizing the conversation."
}}

RULES:
- Use ONLY information explicitly stated in the transcript
- Do NOT output a tagged transcript reconstruction or per-line speaker labels
- If a field cannot be determined from the transcript, use null or empty arrays rather than guessing
- For drift arrays, divide the conversation into roughly equal time-based chunks (default ~35 sec each) and score each chunk
- Confidence scores must be between 0.0 and 1.0
- Sentiment normalized_score must be between -100 and +100
- analysis_time should reflect the current analysis timestamp
- utterance counts should reflect actual speaker turns in the transcript
- Keep executive_summary factual and objective; avoid interpretive language
- normalized_score and drift values MUST be whole INTEGERS between -100 and +100.
- NEVER output decimals like 0.5 or 0.1. Use values like: -100, -75, -50, -25, 0, 25, 50, 75, 100.
"""

    response = client.chat(
        model=LLM_MODEL,
        options={"num_ctx": 50000},
        messages=[{"role": "user", "content": prompt}]
    )

    raw_content = response["message"]["content"].strip()
    result = extract_json_from_llm(raw_content)

    # Parse JSON with fallback safety net
    '''try:
        result = extract_json_from_llm(raw_content)
    except Exception as e:
        print(f"⚠️ Failed to parse LLM JSON: {e}")
        print(f"   Raw preview: {raw_content[:500]}")
        result = {
            "emotion": {
                "agent": {"dominant_emotion": "neutral", "confidence": 0.0},
                "customer": {"dominant_emotion": "neutral", "confidence": 0.0}
            },
            "sentiment": {
                "agent": {
                    "label": "NEUTRAL", "confidence": 0.0, "normalized_score": 0,
                    "drift": [], "num_chunks": 0, "volatility": 0.0,
                    "distribution": {}, "chunk_duration_sec": 35
                },
                "customer": {
                    "label": "NEUTRAL", "confidence": 0.0, "normalized_score": 0,
                    "drift": [], "num_chunks": 0, "volatility": 0.0,
                    "distribution": {}, "chunk_duration_sec": 35
                }
            },
            "entities": {"persons": [], "orgs": [], "locations": []},
            "metadata": {},
            "advanced_insights": {
                "issue_detected": False,
                "primary_intent": "General inquiry",
                "compliance_risk": "Low",
                "repeat_call_risk": "Low",
                "resolution_status": "Follow-up required",
                "sentiment_explanation": "Unable to analyze due to response parsing error.",
                "customer_intent_strength": "Medium",
                "dominant_customer_emotion": "neutral"
            },
            "executive_summary": "Analysis could not be completed due to response parsing failure."
        }'''

    # Count speaker turns from raw transcript for metadata
    speaker_00_count = transcript.count("[SPEAKER_00]")
    speaker_01_count = transcript.count("[SPEAKER_01]")

    # Override metadata with ground-truth from DB / code
    result["metadata"] = {
        "agent_name": agent_name,
        "analysis_time": datetime.now().isoformat(),
        "call_duration_sec": call_duration,
        "utterances": {
            "agent": speaker_00_count,
            "customer": speaker_01_count
        }
    }

    return result

# ============================================================
# MAIN PIPELINE (DB DRIVEN)
# ============================================================
def run_analysis():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT call_audio_id, user_name, transcribed_text, call_duration_sec
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

    audio_id, agent_name, transcript, call_duration = row
    print(f"🎧 Processing Agent: {agent_name} (ID {audio_id})")

    # DEBUG preview
    print(f"   Raw transcript length: {len(transcript)} chars")
    print(f"   Raw transcript preview: {transcript[:100]}...")

    # SAFETY CHECK: Skip if transcript is empty
    if not transcript.strip():
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

    # Run comprehensive LLM analysis
    print("   🤖 Sending to LLM for comprehensive analysis...")
    output = llm_analyze(transcript, agent_name, call_duration)
    print("   ✅ LLM analysis complete")

    # 1. Upsert analysis (won't crash even if already exists)
    cur.execute("""
        INSERT INTO call_analysis (id, agent_name, call_json, created_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (id) DO UPDATE SET
            agent_name = EXCLUDED.agent_name,
            call_json = EXCLUDED.call_json,
            created_at = NOW()
    """, (audio_id, agent_name, json.dumps(output)))

    # 2. Mark as done
    cur.execute("""
        UPDATE call_audio
        SET analysis_done = TRUE
        WHERE call_audio_id = %s
    """, (audio_id,))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Analysis stored successfully into table call_analysis")

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    run_analysis()
