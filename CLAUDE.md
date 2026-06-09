# CLAUDE.md

This file provides guidance to Claude Code when working with the `ib-ai-sentiment-analysis-newchanges` project.

## Project Overview

**India Bonds AI Call Analytics** — an end-to-end pipeline that ingests call-center audio from S3, transcribes and diarizes it with WhisperX, performs LLM-based sentiment/emotion analysis via Ollama, and exposes results through a Streamlit dashboard.

---

## Module Map

| Directory | Purpose |
|-----------|---------|
| `api/` | FastAPI service: downloads audio from S3, runs WhisperX transcription + speaker diarization, writes to `call_audio` table |
| `analysis/` | FastAPI service: polls DB for unanalyzed transcripts, sends to Ollama LLM (`gemma4:e4b`), writes structured JSON to `call_analysis` table |
| `dashboard/` | Streamlit dashboard: 3-screen UI — agent overview, call list, call detail (transcription only) |
| `alembic/` | DB migration history — initial schema in `versions/001_initial_schema.py` |
| `DBtoDB.py` | Daily sync script: copies yesterday's calls (`conversation_duration >= 60s`) from source PBX DB to local `call_records_test` |

---

## Running

```bash
# Start all services (GPU required)
docker-compose up --build

# Individual service
docker-compose up api
docker-compose up analysis
docker-compose up dashboard
docker-compose up ollama
```

**Ports:**
- `8000` — API (transcription)
- `8001` — Analysis service
- `8501` — Streamlit dashboard
- `11434` — Ollama

---

## Data Pipeline

```
DBtoDB.py (daily)
  → call_records_test (source PBX call metadata + S3 paths)
        ↓
  api background worker (polls every 10s)
  → download audio from S3 → WhisperX transcribe + diarize
  → INSERT into call_audio (transcribed_text, status="processed")
        ↓
  analysis background worker (polls every 10s)
  → fetch unanalyzed rows (analysis_done=FALSE) from call_audio
  → send transcript to Ollama gemma4:e4b (50k ctx)
  → INSERT into call_analysis (call_json JSONB)
  → UPDATE call_audio SET analysis_done=TRUE
        ↓
  Streamlit dashboard reads call_analysis + call_audio + call_records_test
```

---

## Database Schema

Four tables (managed by Alembic):

| Table | Key Columns |
|-------|------------|
| `agents_numbers` | `phone_number` (unique), `agent_name` |
| `call_records_test` | `source_pbx_call_id` (unique PK), `agent_id`, `s3_file_path`, `conversation_duration` |
| `call_audio` | `call_audio_id` (= source_pbx_call_id), `transcribed_text`, `analysis_done` (bool), `user_name` |
| `call_analysis` | `id` (= call_audio_id), `agent_name`, `call_json` (JSONB), `created_at` |

**Run migrations:**
```bash
alembic upgrade head
```

---

## Environment Variables

All services load from `.env` in the project root.

| Variable | Used by | Notes |
|----------|---------|-------|
| `DB_NAME`, `USER`, `PASSWORD`, `HOST`, `PORT` | api, analysis, dashboard | Destination PostgreSQL |
| `SOURCE_DB_NAME`, `SOURCE_USER`, `SOURCE_PASSWORD`, `SOURCE_HOST`, `SOURCE_PORT` | DBtoDB.py | Source PBX database |
| `REGION_NAME` | api | AWS region for S3 |
| `hf_token` | api | HuggingFace token for diarization model |
| `OLLAMA_HOST` | analysis | Default: `http://ollama:11434` |

---

## Key Files

- `api/app.py` — FastAPI app; loads WhisperX models at startup; `background_worker()` polls for unprocessed calls
- `analysis/analysispipeline.py` — LLM prompt + `run_analysis()` pipeline; `llm_analyze()` returns full JSON
- `analysis/AnalysisAPI.py` — FastAPI wrapper that starts `analysis_worker()` on startup
- `dashboard/Dashboard.py` — 3-screen Streamlit UI (agent overview → call list → call detail)
- `DBtoDB.py` — Copy yesterday's calls from source PBX DB to local DB (run via cron)
- `alembic/versions/001_initial_schema.py` — Full DB schema

---

## LLM Analysis Output Schema

`call_analysis.call_json` is a JSONB column with this structure:

```json
{
  "emotion": {
    "agent":    {"dominant_emotion": "neutral", "confidence": 0.0},
    "customer": {"dominant_emotion": "neutral", "confidence": 0.0}
  },
  "sentiment": {
    "agent": {
      "label": "NEUTRAL|POSITIVE|NEGATIVE",
      "confidence": 0.0,
      "normalized_score": 0,        // INTEGER -100 to +100
      "drift": [0, 25, -25],        // Array of INTEGER scores per chunk
      "num_chunks": 0,
      "volatility": 0.0,
      "distribution": {"positive": 0, "neutral": 0, "negative": 0},
      "chunk_duration_sec": 35
    },
    "customer": { /* same shape */ }
  },
  "entities": {"persons": [], "orgs": [], "locations": []},
  "metadata": {
    "agent_name": null,
    "utterances": {"agent": 0, "customer": 0},
    "analysis_time": "ISO8601",
    "call_duration_sec": null
  },
  "advanced_insights": {
    "issue_detected": false,
    "primary_intent": "General inquiry",
    "compliance_risk": "Low|Medium|High",
    "repeat_call_risk": "Low|Medium|High",
    "resolution_status": "Resolved|Unresolved|Partial|Follow-up required|Escalated",
    "sentiment_explanation": "",
    "customer_intent_strength": "High|Medium|Low",
    "dominant_customer_emotion": ""
  },
  "executive_summary": "4-6 factual sentences."
}
```

**Critical:** `normalized_score` and `drift` values must be whole integers (-100, -75, -50, -25, 0, 25, 50, 75, 100). Never decimals.

---

## Speaker Labels

WhisperX diarization assigns `[SPEAKER_00]` and `[SPEAKER_01]` labels:
- `SPEAKER_00` → agent (call-center representative)
- `SPEAKER_01` → customer/caller

The LLM uses these labels for per-speaker analysis but excludes them from the executive summary.

---

## Models

| Model | Service | Purpose |
|-------|---------|---------|
| WhisperX `medium` | api | Speech-to-text, English |
| HuggingFace DiarizationPipeline | api | Speaker diarization (requires `hf_token`) |
| `gemma4:e4b` via Ollama | analysis | Sentiment, emotion, NER, insights |

WhisperX loads three models at startup (ASR + alignment + diarization) — startup is slow.

---

## Dashboard UI — Current Visible State

`dashboard/Dashboard.py` has been intentionally trimmed. The sections below are **commented out** (not deleted) and can be re-enabled:

| Screen | Currently Shown | Commented Out |
|--------|----------------|---------------|
| **Agent Performance Overview** | Total Agents KPI, Total Calls KPI, table with Agent Name / Total Calls / Avg Duration | Agent Sentiment KPI, Customer Sentiment KPI, Agent Talk % column, Customer Talk % column, Agent Sentiment column, Customer Sentiment column |
| **Call Analysis Dashboard** | Call ID, Duration, Date columns + View button | Agent Talk %, Customer Talk %, Sentiment columns |
| **Call Analysis Details** | Full Call Transcription (in expander), back button | All KPI cards, sentiment trend chart, donut chart, emotion bar chart, executive summary, risk panel, entities section, audio player, Ask AI section |

When re-enabling any commented-out section, also restore the corresponding variable assignments above the UI code (data loading, duration calculation, utterances, emotion/sentiment/advanced/entities/exec_summary blocks — all currently commented out in the details screen).

---

## Stack

- **Web:** FastAPI, Uvicorn
- **Transcription:** WhisperX, PyTorch (CUDA preferred), HuggingFace
- **LLM:** Ollama client (`ollama==0.6.1`), `gemma4:e4b`
- **Database:** PostgreSQL + psycopg2 (connection pool in api), Alembic migrations
- **Dashboard:** Streamlit, Plotly, pandas, boto3
- **Cloud:** AWS S3 (audio storage, IAM role auth)
- **Containers:** Docker Compose (all services + volumes for model caches)
