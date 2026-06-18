import json
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import boto3

#load_dotenv(dotenv_path="/app/.env")
load_dotenv(override=True)
# ============================================================
# PAGE CONFIG - PROFESSIONAL DARK THEME
# ============================================================
st.set_page_config(
    page_title="IndiaBondsAI Call Analytics",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PROFESSIONAL DASHBOARD CSS - MODERN SAAS STYLE
# ============================================================
st.markdown("""
<style>
    /* Main Background - Clean Dark */
    .stApp {
        background: #0f172a;
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #f8fafc !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 600;
        letter-spacing: -0.025em;
    }

    p, span, div {
        color: #cbd5e1;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: #1e293b;
        border-right: 1px solid #334155;
    }

    [data-testid="stSidebar"] .css-1d391kg {
        background: #1e293b;
    }

    /* Navigation Items */
    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        margin: 4px 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        color: #94a3b8;
        font-size: 14px;
        font-weight: 500;
    }

    .nav-item:hover {
        background: #334155;
        color: #f8fafc;
    }

    .nav-item.active {
        background: rgba(99, 102, 241, 0.1);
        color: #818cf8;
        border-right: 3px solid #6366f1;
    }

    /* Metric Cards - Clean Solid Design */
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        transition: all 0.2s ease;
    }

    .metric-card:hover {
        border-color: #6366f1;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.08);
    }

    .metric-icon {
        width: 44px;
        height: 44px;
        background: #334155;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16px;
        font-size: 20px;
    }

    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 4px;
        line-height: 1;
    }

    .metric-label {
        font-size: 14px;
        color: #94a3b8;
        margin-bottom: 12px;
    }

    .metric-trend {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    .trend-up {
        background: rgba(16, 185, 129, 0.1);
        color: #10b981;
    }

    .trend-down {
        background: rgba(244, 63, 94, 0.1);
        color: #f43f5e;
    }

    .trend-neutral {
        background: rgba(148, 163, 184, 0.1);
        color: #94a3b8;
    }

    /* Status Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
    }

    .badge-positive {
        background: rgba(16, 185, 129, 0.1);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }

    .badge-negative {
        background: rgba(244, 63, 94, 0.1);
        color: #f43f5e;
        border: 1px solid rgba(244, 63, 94, 0.2);
    }

    .badge-neutral {
        background: rgba(99, 102, 241, 0.1);
        color: #6366f1;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }

    .badge-warning {
        background: rgba(245, 158, 11, 0.1);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }

    /* Chart Containers */
    .chart-container {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
    }

    /* Section Headers */
    .section-header {
        font-size: 18px;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 1px solid #334155;
    }

    /* Data Cards */
    .data-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .data-label {
        font-size: 12px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }

    .data-value {
        font-size: 16px;
        font-weight: 600;
        color: #f8fafc;
    }

    /* Table Styling */
    .custom-table {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        overflow: hidden;
    }

    .table-header {
        background: #0f172a;
        padding: 16px 24px;
        border-bottom: 1px solid #334155;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .table-row {
        display: flex;
        align-items: center;
        padding: 16px 24px;
        border-bottom: 1px solid #334155;
        transition: background 0.2s;
    }

    .table-row:hover {
        background: rgba(51, 65, 85, 0.5);
    }

    .table-row:last-child {
        border-bottom: none;
    }

    /* Sentiment Row Colors - Subtle */
    .sentiment-positive {
        background: rgba(16, 185, 129, 0.05);
        border-left: 3px solid #10b981;
    }

    .sentiment-negative {
        background: rgba(244, 63, 94, 0.05);
        border-left: 3px solid #f43f5e;
    }

    .sentiment-neutral {
        background: rgba(99, 102, 241, 0.05);
        border-left: 3px solid #6366f1;
    }

    /* Executive Summary */
    .summary-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        line-height: 1.7;
    }

    /* Entity Tags */
    .entity-tag {
        display: inline-flex;
        align-items: center;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        margin: 4px;
    }

    .entity-org {
        background: rgba(16, 185, 129, 0.1);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }

    .entity-person {
        background: rgba(59, 130, 246, 0.1);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }

    .entity-location {
        background: rgba(245, 158, 11, 0.1);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }

    /* Transcription */
    .transcription-box {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        max-height: 400px;
        overflow-y: auto;
        font-size: 14px;
        line-height: 1.8;
    }

    .speaker-agent {
        color: #6366f1;
        font-weight: 600;
    }

    .speaker-customer {
        color: #f59e0b;
        font-weight: 600;
    }

    /* Search Bar */
    .search-bar {
        display: flex;
        align-items: center;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 10px 16px;
    }

    /* Top Navigation Elements */
    .top-nav-icon {
        padding: 10px;
        background: #1e293b;
        border-radius: 10px;
        color: #94a3b8;
        cursor: pointer;
        position: relative;
    }

    .notification-dot {
        position: absolute;
        top: 8px;
        right: 8px;
        width: 8px;
        height: 8px;
        background: #f43f5e;
        border-radius: 50%;
    }

    /* Buttons */
    .stButton > button {
        background: #6366f1;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background: #4f46e5;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
    }

    /* ============================================
       SELECTBOX STYLING - FIXED DROPDOWN
       ============================================ */

    /* Select Box - Main container */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
    }

    /* Select Box - Input text color */
    div[data-baseweb="select"] input {
        color: #f8fafc !important;
    }

    /* Select Box - Placeholder text */
    div[data-baseweb="select"] div[aria-selected="true"] {
        color: #f8fafc !important;
    }

    /* Select Box - Dropdown menu (the ul element) */
    ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }

    /* Select Box - Individual option items (li elements) */
    ul[data-testid="stSelectboxVirtualDropdown"] li[role="option"] {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        font-size: 14px !important;
    }

    /* Select Box - Hover state for options */
    ul[data-testid="stSelectboxVirtualDropdown"] li[role="option"]:hover {
        background-color: #334155 !important;
        color: #f8fafc !important;
    }

    /* Select Box - Selected/highlighted option */
    ul[data-testid="stSelectboxVirtualDropdown"] li[aria-selected="true"] {
        background-color: #6366f1 !important;
        color: #f8fafc !important;
    }

    /* Select Box - Focused option */
    ul[data-testid="stSelectboxVirtualDropdown"] li[role="option"]:focus {
        background-color: #334155 !important;
        color: #f8fafc !important;
    }

    /* Select Box - Active/pressed state */
    ul[data-testid="stSelectboxVirtualDropdown"] li[role="option"]:active {
        background-color: #475569 !important;
        color: #f8fafc !important;
    }

    /* Select Box - Label styling */
    .stSelectbox label {
        color: #94a3b8 !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }

    /* Text Input */
    .stTextInput > div > div > input {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        color: #f8fafc;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        color: #f8fafc;
    }

    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Keep sidebar collapse/expand toggle visible even when header is hidden */
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        display: flex !important;
    }
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #0f172a;
    }

    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #475569;
    }

    /* Layout utilities */
    .flex { display: flex; }
    .items-center { align-items: center; }
    .justify-between { justify-content: space-between; }
    .gap-2 { gap: 8px; }
    .gap-3 { gap: 12px; }
    .gap-4 { gap: 16px; }
    .mb-4 { margin-bottom: 16px; }
    .mb-6 { margin-bottom: 24px; }
    .mt-4 { margin-top: 16px; }
    .text-sm { font-size: 14px; }
    .text-xs { font-size: 12px; }
    .font-medium { font-weight: 500; }
    .text-slate-400 { color: #94a3b8; }
    .text-slate-500 { color: #64748b; }
</style>
""", unsafe_allow_html=True)

def plot_sentiment_trend(segments, call_duration):
    agent_drift = []
    cust_drift = []

    for seg in segments:
        sentiment = seg.get("sentiment", {}).get("normalized_score", 0)
        if seg.get("speaker") == "Agent":
            agent_drift.append(sentiment)
        elif seg.get("speaker") == "Customer":
            cust_drift.append(sentiment)

    if len(agent_drift) == 0:
        agent_drift = [0]
    if len(cust_drift) == 0:
        cust_drift = [0]

    max_len = max(len(agent_drift), len(cust_drift))

    if len(agent_drift) < max_len:
        agent_drift += [agent_drift[-1]] * (max_len - len(agent_drift))
    if len(cust_drift) < max_len:
        cust_drift += [cust_drift[-1]] * (max_len - len(cust_drift))

    segment_duration = call_duration / max_len
    time_points = [round(i * segment_duration, 1) for i in range(max_len)]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=time_points,
        y=agent_drift,
        mode="lines+markers",
        name="Agent",
        line=dict(color='#6366f1', width=3),
        marker=dict(size=6, color='#6366f1')
    ))

    fig.add_trace(go.Scatter(
        x=time_points,
        y=cust_drift,
        mode="lines+markers",
        name="Customer",
        line=dict(color='#f59e0b', width=3),
        marker=dict(size=6, color='#f59e0b')
    ))

    fig.add_hline(y=0, line_dash="dash", line_color="#475569")

    fig.update_layout(
        title=dict(text='Sentiment Flow During Call', font=dict(color='#f8fafc', size=16)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        xaxis=dict(
            title='Call Time (seconds)',
            showgrid=False,
            color='#64748b',
            linecolor='#334155'
        ),
        yaxis=dict(
        title='Sentiment Score',
        range=[-100, 100],
        showgrid=True,
        gridcolor='#334155',
        color='#64748b',
        linecolor='#334155',
        tickmode='array',
        tickvals=[-100, -50, 0, 50, 100],
        ticktext=['Very Negative<br>(-100)', 'Negative<br>(-50)', 'Neutral<br>(0)', 'Positive<br>(50)', 'Very Positive<br>(100)']
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(color='#94a3b8')
        ),
        hovermode="x unified",
        margin=dict(l=60, r=20, t=80, b=60)
    )

    return fig

# ============================================================
# SESSION STATE INIT
# ============================================================
if "data" not in st.session_state:
    st.session_state.data = None

if "agent_summary_df" not in st.session_state:
    st.session_state.agent_summary_df = None

if "selected_call" not in st.session_state:
    st.session_state.selected_call = None

if "show_main_dashboard" not in st.session_state:
    st.session_state.show_main_dashboard = False

# Cache invalidation tracking
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

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
# DATA LOADING FUNCTIONS (UNCHANGED)
# ============================================================
@st.cache_data(ttl=300)
def load_agent_summary():
    conn = psycopg2.connect(**DB_CONFIG)

    query = """
    SELECT
        TRIM(ca.agent_name) AS agent_name,
        ROUND(
            AVG(
                (ca.call_json->'metadata'->'utterances'->>'agent')::INT * 100.0 /
                NULLIF(
                    (ca.call_json->'metadata'->'utterances'->>'agent')::INT +
                    (ca.call_json->'metadata'->'utterances'->>'customer')::INT,
                    0
                )
            )::NUMERIC,
            2
        ) AS avg_agent_talk_pct,
        ROUND(
            AVG(
                COALESCE(
                    (ca.call_json->'sentiment'->'agent'->>'normalized_score')::FLOAT,
                    NULL
                )
            )::NUMERIC,
            2
        ) AS agent_avg_sentiment,
        ROUND(
            AVG(
                COALESCE(
                    (ca.call_json->'sentiment'->'customer'->>'normalized_score')::FLOAT,
                    NULL
                )
            )::NUMERIC,  -- ← Fixed here
            2
        ) AS customer_avg_sentiment,
        ROUND(
            AVG(
                (ca.call_json->'metadata'->'utterances'->>'customer')::INT * 100.0 /
                NULLIF(
                    (ca.call_json->'metadata'->'utterances'->>'agent')::INT +
                    (ca.call_json->'metadata'->'utterances'->>'customer')::INT,
                    0
                )
            )::NUMERIC,
            2
        ) AS avg_customer_talk_pct,
        COUNT(*) AS total_calls,
        ROUND(AVG(crt.conversation_duration)::NUMERIC, 0) AS avg_duration_sec,
        crt.created_at
    FROM call_analysis ca
    LEFT JOIN call_records_test crt ON crt.source_pbx_call_id = ca.id
    GROUP BY TRIM(ca.agent_name), crt.created_at
    ORDER BY TRIM(ca.agent_name);
    """

    df = pd.read_sql(query, conn)
    conn.close()

    df = df.rename(columns={
        "agent_name": "Agent Name",
        "avg_agent_talk_pct": "Average Agent Talk Percent",
        "avg_customer_talk_pct": "Average Customer Talk Percent",
        "agent_avg_sentiment": "Agent Avg Sentiment",
        "customer_avg_sentiment": "Customer Avg Sentiment",
        "total_calls": "Total Calls",
        "avg_duration_sec": "Avg Duration (sec)"
    })
    return df

#Load audio from S3
@st.cache_data
def load_audio_from_s3(call_id):
    """Fetch audio bytes from S3 using call_recording_link"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT call_recording_link
            FROM call_audio
            WHERE call_audio_id = %s
        """, (call_id,))
        row = cur.fetchone()

        if not row or not row[0]:
            return None

        s3_path = row[0]

        # Parse s3://bucket/key format
        parts = s3_path.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        # No credentials needed — IAM role handles it
        s3 = boto3.client('s3')

        return s3.get_object(Bucket=bucket, Key=key)['Body'].read()

    except Exception:
        return None
    finally:
        cur.close()
        conn.close()



def get_call_details(call_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT
            ca.id,
            ca.agent_name,
            ca.call_json,
            ca.created_at,
            audio.transcribed_text,
            crt.conversation_duration
        FROM call_analysis ca
        JOIN call_audio audio
            ON audio.call_audio_id = ca.id
        JOIN call_records_test crt
            ON crt.source_pbx_call_id = ca.id
        WHERE ca.id = %s;
    """, (call_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "agent_name": row[1],
        "analysis": row[2],
        "created_at": row[3],
        "transcript": row[4],
        "duration": row[5]
    }

def executive_sentiment_label(score):
    if score >= 50:
        return "Very Positive"
    elif score >= 20:
        return "Generally Positive"
    elif score > -20:
        return "Neutral"
    elif score > -50:
        return "Generally Negative"
    else:
        return "Highly Negative"

@st.cache_data
def load_all_calls():
    calls = []
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT ca.id, ca.agent_name, ca.call_json, ca.created_at,
               crt.conversation_duration, crt.created_at AS source_date
        FROM call_analysis ca
        LEFT JOIN call_records_test crt ON crt.source_pbx_call_id = ca.id
        ORDER BY ca.created_at DESC
    """)
    for row in cur.fetchall():
        calls.append((row["id"], row["agent_name"], row["call_json"], row["created_at"], row["conversation_duration"], row["source_date"]))
    cur.close()
    conn.close()
    return calls

@st.cache_data
def load_transcription(call_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    query = "SELECT transcribed_text, call_audio_id FROM call_audio WHERE call_audio_id = %s"
    cur.execute(query, (call_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        return result[0]
    return None

# ============================================================
# NEW FUNCTION: Get conversation duration from call_records_test table
# ============================================================
@st.cache_data
def get_conversation_duration(call_id):
    """
    Fetch conversation_duration from call_records_test table
    Returns duration in seconds (as float)
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        # FIXED: Use correct relationship - crt.source_pbx_call_id = ca.id
        cur.execute("""
            SELECT crt.conversation_duration
            FROM call_records_test crt
            WHERE crt.source_pbx_call_id = %s
            LIMIT 1
        """, (call_id,))

        result = cur.fetchone()
        if result and result[0] is not None:
            duration = result[0]
            # Handle different data types
            if isinstance(duration, (int, float)):
                return float(duration)
            elif isinstance(duration, str):
                try:
                    return float(duration)
                except ValueError:
                    # If format is MM:SS or HH:MM:SS, convert to seconds
                    parts = duration.strip().split(':')
                    if len(parts) == 2:  # MM:SS
                        return int(parts[0]) * 60 + int(parts[1])
                    elif len(parts) == 3:  # HH:MM:SS
                        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0.0
    except Exception as e:
        # Silently return 0 on error to not break the UI
        return 0.0
    finally:
        cur.close()
        conn.close()



# ============================================================
# CHANGED: Scale down from -100/+100 to -1/+1 for display
# ============================================================
def get_normalized(sent):
    if "normalized_score" in sent:
        return float(sent["normalized_score"])  # Already -100 to +100, no division
    # Fallback
    label_map = {"POSITIVE": 100, "NEGATIVE": -100, "NEUTRAL": 0}
    confidence = sent.get("confidence", 0)
    if isinstance(confidence, (int, float)) and confidence > 1:
        confidence = confidence / 100  # Handle if confidence is 0-100
    return label_map.get(sent.get("label", "NEUTRAL"), 0) * confidence
# ============================================================
# CHANGED: Scale down drift values from -100/+100 to -1/+1
# ============================================================
def get_drift(sent):
    if "drift" in sent and isinstance(sent["drift"], list):
        # Already -100 to +100 from pipeline, return as-is
        return sent["drift"]
    # Fallback calculation
    confidence = sent.get("confidence", 0)
    label = sent.get("label", "NEUTRAL")
    sign = 100 if label == "POSITIVE" else -100 if label == "NEGATIVE" else 0
    return [sign * confidence]

def format_duration(seconds):
    """Convert seconds to hh:mm:ss format"""
    if not seconds or seconds <= 0:
        return "00:00:00"

    # Ensure seconds is a number
    try:
        total_seconds = int(float(seconds))
    except (ValueError, TypeError):
        return "00:00:00"

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# ============================================================
# SIDEBAR NAVIGATION (PROFESSIONAL LAYOUT) - USER PROFILE REMOVED
# ============================================================
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="padding: 20px 0 24px 0; border-bottom: 1px solid #334155; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 40px; height: 40px; background: #6366F1; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px;">
                📞
            </div>
            <div>
                <div style="font-size: 18px; font-weight: 700; color: #F8FAFC;">IndiaBonds<span style="color: #6366F1;">AI</span></div>
                <div style="font-size: 11px; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Call Analytics</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # REFRESH BUTTON - ADDED HERE
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.session_state.agent_summary_df = None
        st.session_state.data = None
        st.session_state.last_refresh = datetime.now()
        st.rerun()

    # Last updated timestamp
    if 'last_refresh' in st.session_state:
        st.markdown(f"""
        <div style="text-align: center; padding: 8px; color: #64748B; font-size: 11px; margin-bottom: 16px;">
            Last updated: {st.session_state.last_refresh.strftime("%H:%M:%S")}
        </div>
        """, unsafe_allow_html=True)

    # Navigation
    st.markdown("""
    <style>
    div[data-testid="stSidebar"] .stButton > button {
        background: rgba(99, 102, 241, 0.1) !important;
        color: #818cf8 !important;
        border: none !important;
        border-right: 3px solid #6366f1 !important;
        border-radius: 8px !important;
        text-align: left !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        padding: 12px 16px !important;
        width: 100% !important;
    }
    div[data-testid="stSidebar"] .stButton > button:hover {
        background: #334155 !important;
        color: #f8fafc !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("📊  Dashboard", key="nav_dashboard", use_container_width=True):
        st.session_state.show_main_dashboard = False
        st.session_state.selected_call = None
        st.rerun()

# ============================================================
# FIRST DASHBOARD - AGENT PERFORMANCE OVERVIEW
# ============================================================
if not st.session_state.show_main_dashboard:
    # LOAD DATA FIRST (before creating columns)
    if st.session_state.agent_summary_df is None:
        st.session_state.agent_summary_df = load_agent_summary()

    df = st.session_state.agent_summary_df
    df['Agent Name'] = df['Agent Name'].str.strip()

    # Ensure created_at is datetime
    if 'created_at' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['created_at']):
        df['created_at'] = pd.to_datetime(df['created_at'])
    df['Agent Name'] = df['Agent Name'].str.strip()

    # Get available dates for the picker
    available_dates = sorted(df['created_at'].dt.date.unique()) if 'created_at' in df.columns else []

    # Initialize selected_date in session state
    if available_dates:
        if 'selected_date' not in st.session_state or st.session_state.selected_date not in available_dates:
            st.session_state.selected_date = available_dates[-1]  # Default to most recent

    # Top Header - NOW create columns after data is loaded
    col1, col2, col3, col4 = st.columns([2, 1.5, 1, 0.8])

    with col1:
        st.markdown("""
        <div>
            <h1 style="font-size: 28px; margin-bottom: 4px;">Agent Performance Overview</h1>
            <p style="color: #64748b; font-size: 14px; margin: 0;">Monitor agent metrics and conversation analytics</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # WORKING SEARCH BAR - Filters agent table
        search_query = st.text_input(
            "Search",
            value=st.session_state.get("agent_search", ""),
            key="agent_search",
            placeholder="🔍 Search agents...",
            label_visibility="collapsed"
        )

        # Custom CSS to style the search input like your design
        st.markdown("""
        <style>
        div[data-testid="stTextInput"] input {
            background: #1e293b !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            color: #f8fafc !important;
            padding: 10px 16px !important;
            font-size: 14px !important;
        }
        div[data-testid="stTextInput"] input::placeholder {
            color: #64748b !important;
        }
        </style>
        """, unsafe_allow_html=True)

    with col3:
        # DATE PICKER with "All" option
        if available_dates:
            # Create list with "All" option prepended
            date_options = ["All"] + [d.strftime("%b %d, %Y") for d in available_dates]

            # Get current selection or default to "All"
            current_selection = st.session_state.get('selected_date', "All")
            if current_selection == "All":
                default_index = 0
            elif current_selection in available_dates:
                default_index = available_dates.index(current_selection) + 1
            else:
                default_index = 0

            selected_option = st.selectbox(
                "📅 Select Date",
                options=date_options,
                index=default_index,
                key="date_filter"
            )

            # Convert selection back to date object or "All"
            if selected_option == "All":
                st.session_state.selected_date = "All"
            else:
                # Parse the date string back to date object
                selected_date = datetime.strptime(selected_option, "%b %d, %Y").date()
                st.session_state.selected_date = selected_date
        else:
            st.session_state.selected_date = "All"

    with col4:
        st.markdown("<div style='padding-top: 22px;'>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", key="overview_refresh", use_container_width=True):
            st.cache_data.clear()
            st.session_state.agent_summary_df = None
            st.session_state.data = None
            st.session_state.last_refresh = datetime.now()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

        # FILTER agents based on search query
    if search_query:
        df_filtered = df[df['Agent Name'].str.contains(search_query, case=False, na=False)]
    else:
        df_filtered = df.copy()

    # FILTER by selected date (only if not "All")
    if st.session_state.get('selected_date') != "All" and st.session_state.get('selected_date') and 'created_at' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['created_at'].dt.date == st.session_state.selected_date]

    # FIXED: Always aggregate so each agent appears ONCE
    if not df_filtered.empty:
        # Helper for weighted duration
        df_filtered['__weighted_duration'] = df_filtered['Avg Duration (sec)'] * df_filtered['Total Calls']

        # Build aggregation
        agg_dict = {
            'Total Calls': 'sum',
            '__weighted_duration': 'sum',
            'Agent Avg Sentiment': 'mean',
            'Customer Avg Sentiment': 'mean',
            'Average Agent Talk Percent': 'mean',
            'Average Customer Talk Percent': 'mean',
        }
        if 'created_at' in df_filtered.columns:
            agg_dict['created_at'] = 'max'

        # Group by agent and aggregate
        df_filtered = df_filtered.groupby('Agent Name', as_index=False).agg(agg_dict)

        # Calculate weighted average duration
        df_filtered['Avg Duration (sec)'] = df_filtered.apply(
            lambda row: row['__weighted_duration'] / row['Total Calls'] if row['Total Calls'] > 0 else 0,
            axis=1
        )
        df_filtered = df_filtered.drop(columns=['__weighted_duration'])

    # KPI Cards for Overview
    total_agents = df_filtered['Agent Name'].nunique()
    total_calls = int(df_filtered['Total Calls'].sum()) if 'Total Calls' in df_filtered.columns else 0

    if not df_filtered.empty:
        avg_agent_sentiment = df_filtered['Agent Avg Sentiment'].mean()
        avg_customer_sentiment = df_filtered['Customer Avg Sentiment'].mean()
    else:
        avg_agent_sentiment = 0.0
        avg_customer_sentiment = 0.0

    # Helper for trend styling
    def get_trend_class(value):
        if value > 20:
            return "trend-up"
        elif value < -20:
            return "trend-down"
        else:
            return "trend-neutral"

    def get_trend_text(value):
        if value > 0.2:
            return "Positive"
        elif value < -0.2:
            return "Negative"
        else:
            return "Neutral"

    agent_trend_class = get_trend_class(avg_agent_sentiment)
    agent_trend_text = get_trend_text(avg_agent_sentiment)
    cust_trend_class = get_trend_class(avg_customer_sentiment)
    cust_trend_text = get_trend_text(avg_customer_sentiment)

    # Show 4 KPI cards instead of 3
    cols = st.columns(2)

    with cols[0]:
        st.markdown(f"""
        <div class="metric-card" style="min-height: 145px;">
            <div class="metric-icon">👥</div>
            <div class="metric-value">{total_agents}</div>
            <div class="metric-label">Total Agents</div>
            <div style="min-height: 24px;"></div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"""
        <div class="metric-card" style="min-height: 145px;">
            <div class="metric-icon">📞</div>
            <div class="metric-value">{total_calls}</div>
            <div class="metric-label">Total Calls</div>
            <div style="min-height: 24px;"></div>
        </div>
        """, unsafe_allow_html=True)

    # with cols[2]:
    #     st.markdown(f"""
    #     <div class="metric-card" style="min-height: 140px;">
    #         <div class="metric-icon">😊</div>
    #         <div class="metric-value">{avg_agent_sentiment:+.0f}</div>
    #         <div class="metric-label">Agent Sentiment</div>
    #         <span class="metric-trend {agent_trend_class}">{agent_trend_text}</span>
    #     </div>
    #     """, unsafe_allow_html=True)

    # with cols[3]:
    #     st.markdown(f"""
    #     <div class="metric-card" style="min-height: 140px;">
    #         <div class="metric-icon">🎯</div>
    #         <div class="metric-value">{avg_customer_sentiment:+.0f}</div>
    #         <div class="metric-label">Customer Sentiment</div>
    #         <span class="metric-trend {cust_trend_class}">{cust_trend_text}</span>
    #     </div>
    #     """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

        # Column Headers - Added Avg Duration column
        # Column Headers - Added Avg Duration column
    cols = st.columns([2, 1.2, 1.2, 1])
    headers = ["Agent Name", "Total Calls", "Avg Duration"]
    # headers = ["Agent Name", "Total Calls", "Agent Talk %", "Customer Talk %", "Agent Sentiment", "Customer Sentiment", "Avg Duration"]
    for i, header in enumerate(headers):
        cols[i].markdown(f"<div style='padding: 12px 0; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>{header}</div>", unsafe_allow_html=True)

    st.markdown("<div style='border-top: 1px solid #334155;'></div>", unsafe_allow_html=True)

    for idx, row in df_filtered.iterrows():
        agent_name = row['Agent Name']

        # Get individual agent's call count
        agent_total_calls = int(row['Total Calls']) if pd.notna(row['Total Calls']) else 0

        agent_sent = float(row['Agent Avg Sentiment']) if pd.notna(row['Agent Avg Sentiment']) else 0
        cust_sent = float(row['Customer Avg Sentiment']) if pd.notna(row['Customer Avg Sentiment']) else 0
        avg_duration_sec = float(row['Avg Duration (sec)']) if pd.notna(row['Avg Duration (sec)']) else 0
        duration_str = format_duration(avg_duration_sec)

        agent_badge = "badge-positive" if agent_sent > 20 else "badge-negative" if agent_sent < -20 else "badge-neutral"
        cust_badge = "badge-positive" if cust_sent > 20 else "badge-negative" if cust_sent < -20 else "badge-neutral"

        cols = st.columns([2, 1.2, 1.2, 1])

        cols[0].markdown(f"**{agent_name}**")
        cols[1].markdown(f"{agent_total_calls}")  # Individual agent's call count
        # cols[2].markdown(f"{row['Average Agent Talk Percent']}%")
        # cols[3].markdown(f"{row['Average Customer Talk Percent']}%")
        # cols[4].markdown(f"<span class='badge {agent_badge}'>{agent_sent:+.0f}</span>", unsafe_allow_html=True)
        # cols[5].markdown(f"<span class='badge {cust_badge}'>{cust_sent:+.0f}</span>", unsafe_allow_html=True)
        cols[2].markdown(duration_str)

        if cols[3].button("View", key=f"view_{idx}_{agent_name}"):
            st.session_state.selected_agent_filter = agent_name
            st.session_state.show_main_dashboard = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.stop()

# ============================================================
# CALL LIST VIEW - AGENT CALLS
# ============================================================
if st.session_state.selected_call is None:
    # Header
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button("⬅ Back to Overview"):
            st.session_state.selected_call = None
            st.session_state.show_main_dashboard = False
            st.rerun()

    with col2:
        st.markdown("<h1 style='margin: 0; font-size: 24px;'>Call Analysis Dashboard</h1>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div style='padding-top: 8px;'>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", key="calls_refresh", use_container_width=True):
            st.cache_data.clear()
            st.session_state.data = None
            st.session_state.last_refresh = datetime.now()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    calls = load_all_calls()
    rows = []

    for call_id, agent_name, call, created_at, conversation_duration, source_date in calls:
        meta = call.get("metadata", {})
        utt = meta.get("utterances", {})

        # Use database duration instead of metadata
        if conversation_duration and conversation_duration > 0:
            raw_duration = format_duration(float(conversation_duration))
        else:
            # Fallback to metadata if database value is None/0
            metadata_duration = meta.get("call_duration_sec", 0)
            if isinstance(metadata_duration, (int, float)) and metadata_duration > 0:
                raw_duration = format_duration(float(metadata_duration))
            else:
                raw_duration = "00:00:00"
        agent_utt = utt.get('agent', 0)
        cust_utt = utt.get('customer', 0)
        total = agent_utt + cust_utt

        rows.append({
            "Agent": agent_name,
            "Call ID": meta.get("file", f"call_{call_id}"),
            "Date": source_date.strftime("%Y-%m-%d") if source_date else created_at.strftime("%Y-%m-%d"),
            "Duration": raw_duration,
            "Agent Talk %": round((agent_utt / total) * 100, 1) if total else 0,
            "Customer Talk %": round((cust_utt / total) * 100, 1) if total else 0,
            "Sentiment": call.get("sentiment", {}).get("agent", {}).get("label") or "N/A",
            "path": call_id
        })

    df = pd.DataFrame(rows)

        # Agent Selector - Pre-select if coming from agent click
    all_agents = sorted(df["Agent"].unique())

    # Check if we have a pre-selected agent from the dashboard
    if "selected_agent_filter" in st.session_state and st.session_state.selected_agent_filter in all_agents:
        # Pre-select the agent that was clicked
        pre_selected = st.session_state.selected_agent_filter
        agent_index = all_agents.index(pre_selected)
        selected_agent = st.selectbox("Select Agent", all_agents, index=agent_index)
        # Optional: clear after use so dropdown works normally on refresh
        # del st.session_state.selected_agent_filter
    else:
        selected_agent = st.selectbox("Select Agent", all_agents)

    agent_df = df[df["Agent"] == selected_agent]

    # Section Header with Agent Info
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin: 24px 0;">
        <div class="section-header" style="margin: 0; border: none; padding: 0;">
            Calls for {selected_agent}
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="badge badge-neutral">{len(agent_df)} Calls</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Calls Table
    st.markdown('<div class="custom-table">', unsafe_allow_html=True)

    # Column Headers - Adjusted column ratios for better button display
    cols = st.columns([3, 2, 2, 1.5])
    headers = ["Call ID", "Duration", "Date", "Action"]
    # headers = ["Call ID", "Duration", "Agent Talk %", "Customer Talk %", "Sentiment", "Date", "Action"]
    for i, header in enumerate(headers):
        cols[i].markdown(f"<div style='padding: 12px 0; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>{header}</div>", unsafe_allow_html=True)

    st.markdown("<div style='border-top: 1px solid #334155;'></div>", unsafe_allow_html=True)

    # Table Rows with Sentiment Colors and Fixed View Button
    for i, row in agent_df.iterrows():
        sentiment = (row["Sentiment"] or "N/A").upper()
        sentiment_class = "sentiment-positive" if sentiment == "POSITIVE" else "sentiment-negative" if sentiment == "NEGATIVE" else "sentiment-neutral"

        # Apply sentiment styling
        st.markdown(f"""
        <style>
        div[data-testid="stHorizontalBlock"]:has(> div:nth-child(1) div#call_row_{i}) {{
            background: {'rgba(16, 185, 129, 0.05)' if sentiment == 'POSITIVE' else 'rgba(244, 63, 94, 0.05)' if sentiment == 'NEGATIVE' else 'rgba(99, 102, 241, 0.05)'};
            border-left: 3px solid {'#10b981' if sentiment == 'POSITIVE' else '#f43f5e' if sentiment == 'NEGATIVE' else '#6366f1'};
            border-radius: 0 8px 8px 0;
            margin-bottom: 8px;
        }}
        </style>
        """, unsafe_allow_html=True)

        # Adjusted column ratios - last column is wider (1.5 instead of 1)
        cols = st.columns([3, 2, 2, 1.5])

        cols[0].markdown(f"<div id='call_row_{i}' style='padding: 16px 0; font-weight: 500; color: #f8fafc;'>{row['Call ID']}</div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div style='padding: 16px 0; color: #cbd5e1;'>{row['Duration']}</div>", unsafe_allow_html=True)
        # cols[2].markdown(f"<div style='padding: 16px 0; color: #cbd5e1;'>{row['Agent Talk %']}%</div>", unsafe_allow_html=True)
        # cols[3].markdown(f"<div style='padding: 16px 0; color: #cbd5e1;'>{row['Customer Talk %']}%</div>", unsafe_allow_html=True)

        # badge_class = "badge-positive" if sentiment == "POSITIVE" else "badge-negative" if sentiment == "NEGATIVE" else "badge-neutral"
        # cols[4].markdown(f"<div style='padding: 16px 0;'><span class='badge {badge_class}'>{row['Sentiment']}</span></div>", unsafe_allow_html=True)

        cols[2].markdown(f"<div style='padding: 16px 0; color: #94a3b8; font-size: 13px;'>{row['Date']}</div>", unsafe_allow_html=True)

        # Fixed View Button - Using a container with custom styling
        with cols[3]:
            st.markdown('<div style="padding: 12px 0;">', unsafe_allow_html=True)
            if st.button("View", key=f"btn_{i}_{row['path']}", use_container_width=True):
                st.session_state["selected_call_id"] = row["path"]
                selected = next(c for c in calls if c[0] == row["path"])
                st.session_state.data = selected[2]
                st.session_state.selected_call = row["path"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ============================================================
# CALL DETAIL DASHBOARD - PROFESSIONAL LAYOUT
# ============================================================
# Back button and header
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    if st.button("⬅ Back to Calls"):
        st.session_state.selected_call = None
        st.rerun()

with col2:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 44px; height: 44px; background: #6366f1; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px;">
            📞
        </div>
        <div>
            <h1 style="margin: 0; font-size: 24px;">Call Analysis Details</h1>
            <p style="margin: 0; color: #64748b; font-size: 14px;">Deep dive into conversation metrics</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="display: flex; justify-content: flex-end; gap: 12px;">
    </div>
    """, unsafe_allow_html=True)

# data = st.session_state.data

# # ============================================================
# # FIXED: Get precise conversation duration from call_records_test
# # ============================================================
# # ============================================================
# # FIXED: Get precise conversation duration from call_records_test
# # ============================================================
call_id = st.session_state.selected_call

# # Get duration from call_records_test table (conversation_duration column) - PRIORITY 1
# conversation_duration_sec = get_conversation_duration(call_id)

# # Fallback to metadata duration from call_json - PRIORITY 2
# call_meta = data.get("metadata", {})
# metadata_duration = call_meta.get("call_duration_sec", 0)

# # PRIORITY ORDER: Database value > Metadata value > Default
# if conversation_duration_sec > 0:
#     call_duration_val = conversation_duration_sec
#     duration_source = "Database"
# elif isinstance(metadata_duration, (int, float)) and metadata_duration > 0:
#     call_duration_val = float(metadata_duration)
#     duration_source = "Metadata"
# elif isinstance(metadata_duration, str) and ':' in metadata_duration:
#     try:
#         parts = metadata_duration.split(':')
#         if len(parts) == 3:  # HH:MM:SS
#             call_duration_val = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
#         elif len(parts) == 2:  # MM:SS
#             call_duration_val = int(parts[0]) * 60 + int(parts[1])
#         else:
#             call_duration_val = float(metadata_duration) if metadata_duration else 0
#         duration_source = "Metadata (parsed)"
#     except:
#         call_duration_val = 0
#         duration_source = "Default"
# else:
#     try:
#         call_duration_val = float(metadata_duration) if metadata_duration else 0
#         duration_source = "Metadata" if call_duration_val > 0 else "Default"
#     except:
#         call_duration_val = 0
#         duration_source = "Default"

# # Ensure duration is never negative and is float
# call_duration_val = max(0.0, float(call_duration_val))

# utterances = data['metadata'].get('utterances', {})
# agent_utt = utterances.get('agent', 0)
# cust_utt = utterances.get('customer', 0)
# total_utt = agent_utt + cust_utt
# agent_pct = (agent_utt / total_utt * 100) if total_utt else 0

# # Emotion data
# agent_emotion = data.get("emotion", {}).get("agent", {})
# cust_emotion = data.get("emotion", {}).get("customer", {})
# agent_emotion_conf = agent_emotion.get("confidence", 0)
# cust_emotion_conf = cust_emotion.get("confidence", 0)
# agent_emotion_label = agent_emotion.get("dominant_emotion", "neutral")
# cust_emotion_label = cust_emotion.get("dominant_emotion", "neutral")

# # Sentiment data - NOW SCALED DOWN in get_normalized()
# agent_sent = data.get("sentiment", {}).get("agent", {})
# cust_sent = data.get("sentiment", {}).get("customer", {})
# agent_norm = get_normalized(agent_sent)
# cust_norm = get_normalized(cust_sent)

# # Advanced insights
# advanced = data.get("advanced_insights", {})
# primary_intent = advanced.get("primary_intent", "N/A")
# intent_strength = advanced.get("customer_intent_strength", "N/A")
# resolution_status = advanced.get("resolution_status", "N/A")
# repeat_risk = advanced.get("repeat_call_risk", "N/A")
# compliance_risk = advanced.get("compliance_risk", "N/A")
# issue_detected = advanced.get("issue_detected", False)
# dominant_emotion = advanced.get("dominant_customer_emotion", "N/A")
# sentiment_explanation = advanced.get("sentiment_explanation", "N/A")

# # Entities
# entities = data.get("entities", {})
# orgs = entities.get("orgs", [])
# persons = entities.get("persons", [])
# locations = entities.get("locations", [])

# # Executive summary
# exec_summary = data.get("executive_summary", "")

# # KPI Cards - Top Row
# st.markdown("<div style='margin: 24px 0;'>", unsafe_allow_html=True)
# cols = st.columns(4)

# metrics = [
#     {"icon": "🎙️", "label": "Agent Utterances", "value": str(agent_utt), "sub": f"{agent_pct:.1f}% of conversation"},
#     {"icon": "💬", "label": "Customer Utterances", "value": str(cust_utt), "sub": f"{100-agent_pct:.1f}% of conversation"},
#     {"icon": "😊", "label": "Agent Sentiment", "value": f"{agent_norm:+.0f}", "sub": agent_emotion_label},
#     {"icon": "⏱️", "label": "Call Duration", "value": format_duration(call_duration_val), "sub": f"{call_duration_val:.0f}s ({duration_source})" if call_duration_val > 0 else "N/A"}]

# for i, metric in enumerate(metrics):
#     with cols[i]:
#         st.markdown(f"""
#         <div class="metric-card">
#             <div class="metric-icon">{metric['icon']}</div>
#             <div class="metric-value">{metric['value']}</div>
#             <div class="metric-label">{metric['label']}</div>
#             <div style="font-size: 12px; color: #64748b;">{metric['sub']}</div>
#         </div>
#         """, unsafe_allow_html=True)
# st.markdown("</div>", unsafe_allow_html=True)

# # Second Row - Customer Metrics & Emotion
# cols = st.columns(4)

# with cols[0]:
#     cust_label = executive_sentiment_label(cust_norm)
#     trend_class = "trend-up" if cust_norm > 0.2 else "trend-down" if cust_norm < -0.2 else "trend-neutral"
#     st.markdown(f"""
#     <div class="metric-card">
#         <div class="metric-icon">🎯</div>
#         <div class="metric-value">{cust_norm:+.0f}</div>
#         <div class="metric-label">Customer Sentiment</div>
#         <span class="metric-trend {trend_class}">{cust_label}</span>
#     </div>
#     """, unsafe_allow_html=True)

# with cols[1]:
#     vol_status = "Stable" if cust_emotion_conf < 0.2 else "Volatile"
#     vol_class = "trend-up" if cust_emotion_conf < 0.2 else "trend-down"
#     st.markdown(f"""
#     <div class="metric-card">
#         <div class="metric-icon">⚡</div>
#         <div class="metric-value">{cust_emotion_conf:.0%}</div>
#         <div class="metric-label">Emotion Confidence</div>
#         <span class="metric-trend {vol_class}">{vol_status}</span>
#     </div>
#     """, unsafe_allow_html=True)

# with cols[2]:
#     intent_badge = "badge-positive" if intent_strength == "High" else "badge-warning" if intent_strength == "Medium" else "badge-neutral"
#     st.markdown(f"""
#     <div class="metric-card">
#         <div class="metric-icon">🎯</div>
#         <div class="metric-value" style="font-size: 18px;">{primary_intent}</div>
#         <div class="metric-label">Primary Intent</div>
#         <span class="badge {intent_badge}">{intent_strength}</span>
#     </div>
#     """, unsafe_allow_html=True)

# with cols[3]:
#     risk_badge = "badge-positive" if repeat_risk == "Low" else "badge-warning" if repeat_risk == "Medium" else "badge-negative"
#     st.markdown(f"""
#     <div class="metric-card">
#         <div class="metric-icon">🔄</div>
#         <div class="metric-value" style="font-size: 18px;">{repeat_risk}</div>
#         <div class="metric-label">Repeat Call Risk</div>
#         <span class="badge {risk_badge}">{resolution_status}</span>
#     </div>
#     """, unsafe_allow_html=True)

# # Charts Section - Two Columns
# st.markdown("<br>", unsafe_allow_html=True)
# col_left, col_right = st.columns([2, 1])

# with col_left:
#     # IMPROVED Sentiment Trend Chart - Management Friendly
#     st.markdown('<div style="font-size: 16px; font-weight: 600; color: #f8fafc; margin-bottom: 20px;">📈 Sentiment Flow During Call</div>', unsafe_allow_html=True)

#     # Add explanation for management
#     st.markdown("""
#     <div style="background: #0f172a; border-left: 3px solid #6366f1; padding: 12px 16px; margin-bottom: 16px; border-radius: 0 8px 8px 0;">
#         <div style="font-size: 12px; color: #94a3b8; line-height: 1.5;">
#             <strong style="color: #f8fafc;">How to read:</strong> This chart shows sentiment changes throughout the call.
#             <span style="color: #6366f1;">● Agent</span> (blue) and <span style="color: #f59e0b;">● Customer</span> (orange).
#             Values above 0 = Positive, Below 0 = Negative. The closer to +1 or -1, the stronger the sentiment.
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # CHANGED: Now uses get_drift() which scales down from -100/+100 to -1/+1
#     agent_drift = get_drift(agent_sent)
#     cust_drift = get_drift(cust_sent)

#     if len(agent_drift) == 0:
#         agent_drift = [0]
#     if len(cust_drift) == 0:
#         cust_drift = [0]

#     max_len = max(len(agent_drift), len(cust_drift))
#     if len(agent_drift) < max_len:
#         agent_drift += [agent_drift[-1]] * (max_len - len(agent_drift))
#     if len(cust_drift) < max_len:
#         cust_drift += [cust_drift[-1]] * (max_len - len(cust_drift))

#     # ============================================================
#     # FIXED: Proper time point calculation using actual conversation duration
#     # ============================================================
#         # ============================================================
#     # FIXED: Proper time point calculation using actual conversation duration
#     # ============================================================

#     # Get the chunk duration from sentiment data (default to 10 seconds if not found)
#     agent_chunk_duration = agent_sent.get('chunk_duration_sec', 10)
#     cust_chunk_duration = cust_sent.get('chunk_duration_sec', 10)
#     chunk_duration = max(agent_chunk_duration, cust_chunk_duration, 1)  # At least 1 second

#     # Use actual conversation duration from database, fallback to calculated duration
#     effective_duration = call_duration_val if call_duration_val > 0 else (max_len * chunk_duration)

#     # Calculate time points based on actual call duration
#     if max_len == 1:
#         time_points = [0]
#     else:
#         # Distribute chunks evenly across the actual call duration
#         time_points = [round(i * effective_duration / (max_len - 1), 1) for i in range(max_len)]

#     # Ensure no negative values
#     time_points = [max(0.0, float(t)) for t in time_points]

#     # Create improved trend chart with filled areas
#     fig = go.Figure()

#     # Add filled area under lines for better visualization
#     fig.add_trace(go.Scatter(
#         x=time_points,
#         y=agent_drift,
#         mode="lines+markers",
#         name="Agent",
#         line=dict(color='#6366f1', width=3),
#         marker=dict(size=8, color='#6366f1', line=dict(color='#1e293b', width=2)),
#         fill='tozeroy',
#         fillcolor='rgba(99, 102, 241, 0.1)'
#     ))

#     fig.add_trace(go.Scatter(
#         x=time_points,
#         y=cust_drift,
#         mode="lines+markers",
#         name="Customer",
#         line=dict(color='#f59e0b', width=3),
#         marker=dict(size=8, color='#f59e0b', line=dict(color='#1e293b', width=2)),
#         fill='tozeroy',
#         fillcolor='rgba(245, 158, 11, 0.1)'
#     ))

#     # Add reference lines
#     fig.add_hline(y=0, line_dash="solid", line_color="#475569", line_width=2,
#                   annotation_text="Neutral", annotation_position="right",
#                   annotation_font_color="#94a3b8")
#     fig.add_hline(y=50, line_dash="dash", line_color="#10b981", line_width=1,
#                   annotation_text="Positive Threshold", annotation_position="right",
#                   annotation_font_color="#10b981", annotation_font_size=10)
#     fig.add_hline(y=-50, line_dash="dash", line_color="#f43f5e", line_width=1,
#                   annotation_text="Negative Threshold", annotation_position="right",
#                   annotation_font_color="#f43f5e", annotation_font_size=10)

#     # Add shaded regions for positive/negative zones
#     fig.add_hrect(y0=0, y1=1, line_width=0, fillcolor="#10b981", opacity=0.05)
#     fig.add_hrect(y0=-1, y1=0, line_width=0, fillcolor="#f43f5e", opacity=0.05)

#     fig.update_layout(
#         paper_bgcolor='rgba(0,0,0,0)',
#         plot_bgcolor='rgba(0,0,0,0)',
#         font=dict(color='#94a3b8', family='Inter, sans-serif'),
#                 xaxis=dict(
#             title=dict(text=f'Call Timeline - Total Duration: {format_duration(call_duration_val)}', font=dict(color='#64748b')),
#             showgrid=True,
#             gridcolor='#334155',
#             color='#64748b',
#             linecolor='#334155',
#             zeroline=False,
#             range=[0, max(time_points) * 1.05] if time_points and max(time_points) > 0 else [0, 10],
#             # Format x-axis ticks as minutes
#             tickmode='array',
#             tickvals=[i * 60 for i in range(int(effective_duration // 60) + 1)] if effective_duration > 0 else None,
#             ticktext=[f"{i}:00" for i in range(int(effective_duration // 60) + 1)] if effective_duration > 0 else None,
#         ),
#         yaxis=dict(
#             title=dict(text='Sentiment Score', font=dict(color='#64748b')),
#             range=[-100, 100],
#             showgrid=True,
#             gridcolor='#334155',
#             color='#64748b',
#             linecolor='#334155',
#             tickmode='array',
#             tickvals=[-100, -50, 0, 50, 100],
#             ticktext=['Very Negative<br>(-100)', 'Negative<br>(-50)', 'Neutral<br>(0)', 'Positive<br>(50)', 'Very Positive<br>(100)']
#         ),
#         legend=dict(
#             orientation='h',
#             yanchor='bottom',
#             y=1.02,
#             xanchor='right',
#             x=1,
#             font=dict(color='#f8fafc', size=12),
#             bgcolor='rgba(30, 41, 59, 0.8)',
#             bordercolor='#334155',
#             borderwidth=1
#         ),
#         hovermode="x unified",
#         margin=dict(l=80, r=120, t=100, b=60),
#         height=450
#     )

#     st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
#     st.markdown('</div>', unsafe_allow_html=True)

# with col_right:

#     # Dropdown to select Agent or Customer
#     sentiment_view = st.selectbox("View Sentiment For", ["Agent", "Customer"], key="sentiment_dist_select")

#     # Get the appropriate sentiment data based on selection
#     if sentiment_view == "Agent":
#         sentiment_data = agent_sent.get('distribution', {})
#         center_text = "Agent"
#         primary_color = "#6366f1"
#     else:
#         sentiment_data = cust_sent.get('distribution', {})
#         center_text = "Customer"
#         primary_color = "#f59e0b"

#     st.markdown(f'<div style="font-size: 16px; font-weight: 600; color: #f8fafc; margin-bottom: 20px;">🎯 Sentiment Distribution - {sentiment_view}</div>', unsafe_allow_html=True)

#     if sentiment_data:
#         # Ensure all sentiment categories are present
#         full_sentiment_data = {"Positive": 0, "Neutral": 0, "Negative": 0}
#         for key, value in sentiment_data.items():
#             if key.lower() == "positive":
#                 full_sentiment_data["Positive"] = value
#             elif key.lower() == "negative":
#                 full_sentiment_data["Negative"] = value
#             else:
#                 full_sentiment_data["Neutral"] = value

#         color_map = {"Positive": "#10b981", "Neutral": "#6366f1", "Negative": "#f43f5e"}
#         labels = list(full_sentiment_data.keys())
#         values = list(full_sentiment_data.values())

#         # Create donut chart with improved styling - FIXED labels and legend position
#         fig_pie = go.Figure(data=[go.Pie(
#             values=values,
#             labels=labels,
#             hole=0.6,
#             marker=dict(
#                 colors=[color_map[label] for label in labels],
#                 line=dict(color='#1e293b', width=3)
#             ),
#             # FIXED: Move labels inside the pie slices to avoid cutoff
#             textinfo='label+percent',
#             textposition='inside',
#             textfont=dict(color='#f8fafc', size=11, family='Inter, sans-serif'),
#             insidetextorientation='horizontal',
#             hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
#         )])

#         # Update layout with legend at top right - ABOVE the chart
#         fig_pie.update_layout(
#             paper_bgcolor='rgba(0,0,0,0)',
#             plot_bgcolor='rgba(0,0,0,0)',
#             font=dict(color='#f8fafc', family='Inter, sans-serif'),
#             showlegend=True,
#             legend=dict(
#                 orientation='h',  # Horizontal layout
#                 yanchor='bottom',  # Anchor to bottom of legend
#                 y=1.15,  # Position ABOVE the chart (y > 1)
#                 xanchor='right',  # Anchor to right
#                 x=1,  # Right position
#                 font=dict(color='#f8fafc', size=12),
#                 bgcolor='rgba(30, 41, 59, 0.8)',
#                 bordercolor='#334155',
#                 borderwidth=1
#             ),
#             margin=dict(l=20, r=20, t=80, b=20),  # Increased top margin for legend
#             height=350,
#             annotations=[
#                 dict(
#                     text=f'<b>{center_text}</b><br>Sentiment',
#                     x=0.5, y=0.5,
#                     font_size=14,
#                     showarrow=False,
#                     font=dict(color='#f8fafc', family='Inter, sans-serif')
#                 )
#             ]
#         )

#         st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

#         # Add summary statistics below the chart
#         total_segments = sum(values)
#         if total_segments > 0:
#             pos_pct = (full_sentiment_data["Positive"] / total_segments) * 100
#             neg_pct = (full_sentiment_data["Negative"] / total_segments) * 100

#             st.markdown(f"""
#             <div style="display: flex; justify-content: space-between; margin-top: 16px; padding-top: 16px; border-top: 1px solid #334155;">
#                 <div style="text-align: center; flex: 1;">
#                     <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Positive</div>
#                     <div style="font-size: 18px; font-weight: 700; color: #10b981;">{pos_pct:.1f}%</div>
#                 </div>
#                 <div style="text-align: center; flex: 1; border-left: 1px solid #334155; border-right: 1px solid #334155;">
#                     <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Neutral</div>
#                     <div style="font-size: 18px; font-weight: 700; color: #6366f1;">{(full_sentiment_data["Neutral"] / total_segments) * 100:.1f}%</div>
#                 </div>
#                 <div style="text-align: center; flex: 1;">
#                     <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Negative</div>
#                     <div style="font-size: 18px; font-weight: 700; color: #f43f5e;">{neg_pct:.1f}%</div>
#                 </div>
#             </div>
#             """, unsafe_allow_html=True)
#     else:
#         st.info("No distribution data available")

#     st.markdown('</div>', unsafe_allow_html=True)

# # Bottom Section - Executive Summary & Risk Analysis
# st.markdown("<br>", unsafe_allow_html=True)
# col_bottom_left, col_bottom_right = st.columns([1, 2])

# with col_bottom_left:
#     # Monthly Performance (placeholder using bar chart with emotion confidence)
#     st.markdown('<div style="font-size: 16px; font-weight: 600; color: #f8fafc; margin-bottom: 20px;">Emotion Analysis</div>', unsafe_allow_html=True)

#     fig_bar = go.Figure(data=[go.Bar(
#         x=['Agent', 'Customer'],
#         y=[agent_emotion_conf, cust_emotion_conf],
#         marker_color=['#6366f1', '#f59e0b'],
#         text=[f"{agent_emotion_label}<br>{agent_emotion_conf:.0%}", f"{cust_emotion_label}<br>{cust_emotion_conf:.0%}"],
#         textposition='auto',
#         textfont=dict(color='#f8fafc', size=11))]
#     )

#     fig_bar.update_layout(
#         paper_bgcolor='rgba(0,0,0,0)',
#         plot_bgcolor='rgba(0,0,0,0)',
#         font=dict(color='#94a3b8'),
#         xaxis=dict(showgrid=False, color='#64748b'),
#         yaxis=dict(showgrid=True, gridcolor='#334155', color='#64748b', range=[0, 1], tickformat='.0%'),
#         margin=dict(l=40, r=20, t=20, b=40),
#         height=280,
#         showlegend=False
#     )

#     st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
#     st.markdown('</div>', unsafe_allow_html=True)

# with col_bottom_right:
#     # Executive Summary & Risk Table
#     st.markdown('<div class="custom-table">', unsafe_allow_html=True)
#     st.markdown("""
#     <div class="table-header">
#         <span style="font-size: 16px; font-weight: 600; color: #f8fafc;">Executive Summary & Risk Analysis</span>
#     </div>
#     """, unsafe_allow_html=True)

#     # Summary text
#     if exec_summary:
#         st.markdown(f"""
#         <div style="padding: 20px 24px; border-bottom: 1px solid #334155; line-height: 1.7; color: #cbd5e1; font-size: 14px;">
#             {exec_summary.replace(chr(10), '<br>')}
#         </div>
#         """, unsafe_allow_html=True)

#     # Risk indicators row
#     cols = st.columns(3)
#     with cols[0]:
#         comp_badge = "badge-positive" if compliance_risk == "Low" else "badge-warning" if compliance_risk == "Medium" else "badge-negative"
#         st.markdown(f"""
#         <div style="text-align: center; padding: 16px;">
#             <div style="font-size: 11px; color: #64748b; text-transform: uppercase; margin-bottom: 8px;">Compliance Risk</div>
#             <span class="badge {comp_badge}" style="font-size: 14px; padding: 8px 16px;">{compliance_risk}</span>
#         </div>
#         """, unsafe_allow_html=True)

#     with cols[1]:
#         issue_badge = "badge-negative" if issue_detected else "badge-positive"
#         issue_text = "Yes" if issue_detected else "No"
#         st.markdown(f"""
#         <div style="text-align: center; padding: 16px; border-left: 1px solid #334155; border-right: 1px solid #334155;">
#             <div style="font-size: 11px; color: #64748b; text-transform: uppercase; margin-bottom: 8px;">Issue Detected</div>
#             <span class="badge {issue_badge}" style="font-size: 14px; padding: 8px 16px;">{issue_text}</span>
#         </div>
#         """, unsafe_allow_html=True)

#     with cols[2]:
#         emotion_badge = "badge-neutral"
#         st.markdown(f"""
#         <div style="text-align: center; padding: 16px;">
#             <div style="font-size: 11px; color: #64748b; text-transform: uppercase; margin-bottom: 8px;">Dominant Emotion</div>
#             <span class="badge {emotion_badge}" style="font-size: 14px; padding: 8px 16px; text-transform: capitalize;">{dominant_emotion}</span>
#         </div>
#         """, unsafe_allow_html=True)

#     # Explanation
#     st.markdown(f"""
#     <div style="padding: 16px 24px; background: #0f172a; border-top: 1px solid #334155;">
#         <div style="font-size: 11px; color: #64748b; text-transform: uppercase; margin-bottom: 8px;">Analysis Explanation</div>
#         <div style="color: #94a3b8; font-size: 13px; line-height: 1.6;">{sentiment_explanation}</div>
#     </div>
#     """, unsafe_allow_html=True)

#     st.markdown('</div>', unsafe_allow_html=True)

# # Entities Section
# if orgs or persons or locations:
#     st.markdown("<br>", unsafe_allow_html=True)
#     st.markdown('<div class="section-header">Detected Entities</div>', unsafe_allow_html=True)

#     cols = st.columns(3)

#     with cols[0]:
#         st.markdown('<div class="data-label" style="margin-bottom: 12px;">Organizations</div>', unsafe_allow_html=True)
#         if orgs:
#             for org in orgs:
#                 st.markdown(f'<span class="entity-tag entity-org">{org}</span>', unsafe_allow_html=True)
#         else:
#             st.markdown('<span style="color: #64748b;">None detected</span>', unsafe_allow_html=True)

#     with cols[1]:
#         st.markdown('<div class="data-label" style="margin-bottom: 12px;">Persons</div>', unsafe_allow_html=True)
#         if persons:
#             for person in persons:
#                 st.markdown(f'<span class="entity-tag entity-person">{person}</span>', unsafe_allow_html=True)
#         else:
#             st.markdown('<span style="color: #64748b;">None detected</span>', unsafe_allow_html=True)

#     with cols[2]:
#         st.markdown('<div class="data-label" style="margin-bottom: 12px;">Locations</div>', unsafe_allow_html=True)
#         if locations:
#             for loc in locations:
#                 st.markdown(f'<span class="entity-tag entity-location">{loc}</span>', unsafe_allow_html=True)
#         else:
#             st.markdown('<span style="color: #64748b;">None detected</span>', unsafe_allow_html=True)

# ============================================================
# AUDIO PLAYER - Call Recording from S3
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">🔊 Call Recording</div>', unsafe_allow_html=True)

audio_bytes = load_audio_from_s3(call_id)

if audio_bytes:
    st.markdown("""
    <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px;margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
            <div style="width:36px;height:36px;background:#6366f1;border-radius:8px;display:flex;align-items:center;justify-content:center;">🎧</div>
            <div>
                <div style="font-size:15px;font-weight:600;color:#f8fafc;">Listen to Call</div>
                <div style="font-size:12px;color:#64748b;">Streaming from S3</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.audio(audio_bytes, format="audio/mp3")
else:
    st.info("🎧 No recording available for this call")

# ============================================================
# FULL CALL TRANSCRIPTION
# ============================================================
transcription = load_transcription(call_id)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">Full Call Transcription</div>', unsafe_allow_html=True)

with st.expander("View Transcription", expanded=False):
    if transcription:
        st.markdown(f"""
        <div class="transcription-box">
            {transcription.replace(chr(10), "<br>")}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No transcription found for this call.")

# # Ask AI Section

# selected_call_id = st.session_state.get("selected_call_id")

# st.markdown("<br>", unsafe_allow_html=True)
# st.markdown('<div class="section-header">Ask AI About This Call</div>', unsafe_allow_html=True)
# # Add CSS to make placeholder text visible
# st.markdown("""
# <style>
#     /* Make placeholder text visible */
#     div[data-testid="stTextInput"] input::placeholder {
#         color: #94a3b8 !important;  /* Light gray color */
#         opacity: 1 !important;       /* Full opacity */
#         font-size: 14px !important;  /* Slightly larger */
#         font-weight: 500 !important; /* Medium weight */
#     }

#     /* Ensure input text is also visible */
#     div[data-testid="stTextInput"] input {
#         color: #f8fafc !important;  /* White text */
#         font-size: 14px !important;
#     }
# </style>
# """, unsafe_allow_html=True)
# if selected_call_id:
#     question = st.text_input("Ask anything about this call", placeholder="Why was the customer unhappy?")

#     if st.button("Ask AI", key="ask_ai_btn"):
#         if question:
#             with st.spinner("AI analyzing call..."):
#                 try:
#                     response = requests.post(
#                         "http://localhost:8000/ask_call_ai",
#                         json={"call_id": selected_call_id, "question": question}
#                     )

#                     if response.status_code == 200:
#                         answer = response.json()["answer"]
#                         st.markdown(f"""
#                         <div class="data-card" style="background: #334155; margin-top: 16px;">
#                             <div class="data-label">AI Response</div>
#                             <div style="color: #f8fafc; font-size: 15px; line-height: 1.6;">{answer}</div>
#                         </div>
#                         """, unsafe_allow_html=True)
#                     else:
#                         st.error("AI service failed")
#                 except Exception as e:
#                     st.error(f"Error: {str(e)}")

st.markdown("<div style='text-align: center; color: #64748b; padding: 40px 0 20px; font-size: 12px;'>© 2026 IndiaBondsAI Call Analytics</div>", unsafe_allow_html=True)
