import streamlit as st
import psycopg2
import psycopg2.extras
from psycopg2 import pool
import pandas as pd
import os
from datetime import datetime, date
from urllib.parse import urlparse
import boto3
import re

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Call Analytics Dashboard",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DARK THEME + PROFESSIONAL CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* GLOBAL DARK THEME */
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #12121f 50%, #0d0d18 100%);
        color: #e2e8f0;
    }
    
    .main .block-container {
        padding: 1.5rem 2rem 2rem 2rem;
        max-width: 1400px;
    }
    
    /* SIDEBAR DARK */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c0c14 0%, #141425 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    section[data-testid="stSidebar"] .css-1d391kg, 
    section[data-testid="stSidebar"] .css-1lcbmhc {
        background: transparent !important;
    }
    
    /* HIDE STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .css-1dp5vir {display: none;}
    .css-14xtw13 {display: none;}
    
    /* SCROLLBAR */
    ::-webkit-scrollbar {
        width: 5px;
        height: 5px;
    }
    ::-webkit-scrollbar-track {
        background: #0a0a0f;
    }
    ::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #64748b;
    }
    
    /* BUTTONS */
    .stButton>button {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
        color: #cbd5e1;
        border-radius: 10px;
        padding: 0.4rem 0.9rem;
        font-weight: 500;
        font-size: 0.82rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, rgba(102,126,234,0.2) 0%, rgba(118,75,162,0.2) 100%);
        border-color: rgba(102,126,234,0.4);
        color: #fff;
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.2);
    }
    .stButton>button:active {
        transform: translateY(0);
    }
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        font-weight: 600;
    }
    .stButton>button[kind="primary"]:hover {
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        color: white;
    }
    
    /* SELECTBOX / INPUT */
    .stSelectbox>div>div, .stDateInput>div>div {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
    }
    .stDateInput input {
        color: #f1f5f9 !important;
    }
    
    /* METRIC CARDS (Glassmorphism) */
    .metric-card {
        background: rgba(25, 25, 40, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        color: white;
        position: relative;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2.5px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        opacity: 0.8;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(102,126,234,0.15);
        box-shadow: 0 16px 40px rgba(0,0,0,0.3), 0 0 30px rgba(102,126,234,0.08);
    }
    .metric-card-secondary::before {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
    }
    .metric-card-success::before {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(135deg, #fff 0%, #e2e8f0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }
    .metric-label {
        font-size: 0.72rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 0.4rem;
        font-weight: 600;
    }
    .metric-icon {
        font-size: 1.4rem;
        margin-bottom: 0.5rem;
        opacity: 0.8;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 0.25rem;
    }
    
    /* TABLE HEADER STYLES */
    .table-header-text {
        font-size: 0.68rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        padding: 0.6rem 0;
    }
    
    /* CELL STYLES */
    .cell-name {
        font-weight: 600;
        color: #f8fafc;
        font-size: 0.92rem;
        padding: 0.5rem 0;
    }
    .cell-metric-label {
        font-size: 0.62rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.15rem;
    }
    .cell-metric-value {
        font-size: 0.92rem;
        font-weight: 700;
        color: #f1f5f9;
    }
    .cell-muted {
        font-size: 0.85rem;
        color: #cbd5e1;
        padding: 0.5rem 0;
    }
    
    /* BADGES */
    .agent-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(102,126,234,0.18) 0%, rgba(118,75,162,0.18) 100%);
        color: #c7d2fe;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(102,126,234,0.12);
    }
    .agent-avg-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(79,172,254,0.15) 0%, rgba(0,242,254,0.15) 100%);
        color: #bae6fd;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(79,172,254,0.12);
    }
    
    /* STATUS BADGES */
    .status-processed {
        background: rgba(16, 185, 129, 0.15);
        color: #6ee7b7;
        padding: 0.3rem 0.7rem;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        border: 1px solid rgba(16, 185, 129, 0.2);
        display: inline-block;
    }
    .status-pending {
        background: rgba(245, 158, 11, 0.15);
        color: #fcd34d;
        padding: 0.3rem 0.7rem;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        border: 1px solid rgba(245, 158, 11, 0.2);
        display: inline-block;
    }
    .status-error {
        background: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        padding: 0.3rem 0.7rem;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        border: 1px solid rgba(239, 68, 68, 0.2);
        display: inline-block;
    }
    
    /* TRANSCRIPTION */
    .transcription-box {
        background: rgba(25, 25, 40, 0.45);
        border-left: 3px solid #667eea;
        border-radius: 0 14px 14px 0;
        padding: 1.2rem;
        font-family: 'Inter', sans-serif;
        line-height: 1.7;
        color: #cbd5e1;
        max-height: 450px;
        overflow-y: auto;
        border: 1px solid rgba(255,255,255,0.05);
        border-left-width: 3px;
    }
    .speaker-tag {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 5px;
        font-size: 0.68rem;
        font-weight: 700;
        margin-right: 0.4rem;
        text-transform: uppercase;
    }
    .speaker-SPEAKER_00 {
        background: rgba(59, 130, 246, 0.18);
        color: #93c5fd;
    }
    .speaker-SPEAKER_01 {
        background: rgba(236, 72, 153, 0.18);
        color: #f9a8d4;
    }
    
    /* INFO CARDS (CALL DETAIL) */
    .info-card {
        background: rgba(25, 25, 40, 0.45);
        backdrop-filter: blur(12px);
        border-radius: 14px;
        padding: 1rem;
        border: 1px solid rgba(255,255,255,0.05);
        text-align: center;
        transition: all 0.3s ease;
    }
    .info-card:hover {
        border-color: rgba(102,126,234,0.12);
        transform: translateY(-2px);
    }
    .info-card-label {
        font-size: 0.68rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .info-card-value {
        font-size: 1.05rem;
        font-weight: 700;
        color: #f8fafc;
    }
    
    /* SIDEBAR NAV */
    .nav-btn {
        width: 100%;
        padding: 0.7rem 1rem;
        border-radius: 10px;
        border: none;
        background: transparent;
        color: #94a3b8;
        font-weight: 500;
        text-align: left;
        cursor: pointer;
        transition: all 0.3s;
        margin-bottom: 0.25rem;
        font-size: 0.85rem;
    }
    .nav-btn:hover, .nav-btn.active {
        background: rgba(102,126,234,0.1);
        color: #e0e7ff;
    }
    .nav-btn.active {
        border-left: 2px solid #667eea;
    }
    
    /* TOP BAR */
    .top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.2rem;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .page-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.02em;
    }
    .page-subtitle {
        font-size: 0.82rem;
        color: #94a3b8;
        margin-top: 0.15rem;
    }
    
    /* SECTION TITLE */
    .section-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: rgba(255,255,255,0.05);
        margin-left: 0.8rem;
    }
    
    /* AUDIO PLAYER */
    audio {
        width: 100%;
        border-radius: 10px;
    }
    
    /* EXPANDER */
    .streamlit-expanderHeader {
        background: rgba(25, 25, 40, 0.45) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        color: #cbd5e1 !important;
    }
    .streamlit-expanderContent {
        background: rgba(25, 25, 40, 0.3) !important;
        border-radius: 0 0 10px 10px !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
        border-top: none !important;
    }
    
    /* SPINNER */
    .stSpinner > div {
        border-color: #667eea transparent transparent transparent !important;
    }
    
    /* ALERTS */
    .stAlert {
        background: rgba(25, 25, 40, 0.5) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 10px !important;
    }
    .stAlert [data-testid="stMarkdownContainer"] {
        color: #cbd5e1 !important;
    }
    
    /* CODE BLOCKS */
    code {
        background: rgba(255,255,255,0.06) !important;
        color: #e2e8f0 !important;
        padding: 0.2rem 0.5rem !important;
        border-radius: 6px !important;
        font-size: 0.82rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATABASE CONFIG
# ============================================================
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "your_db"),
    "user": os.getenv("DB_USER", "your_user"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

# ============================================================
# S3 CLIENT
# ============================================================
@st.cache_resource
def get_s3_client():
    return boto3.client(
        "s3",
        region_name=os.getenv("REGION_NAME", "us-east-1")
    )

def get_presigned_url(s3_url, expiration=3600):
    try:
        parsed = urlparse(s3_url)
        if s3_url.startswith("s3://"):
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
        else:
            bucket = parsed.netloc.split(".")[0]
            key = parsed.path.lstrip("/")

        s3_client = get_s3_client()
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        st.error(f"Error generating audio URL: {e}")
        return None

# ============================================================
# DATABASE CONNECTION
# ============================================================
@st.cache_resource
def get_connection_pool():
    return psycopg2.pool.SimpleConnectionPool(1, 5, **DB_CONFIG)

def get_db_connection():
    pool = get_connection_pool()
    return pool.getconn()

def release_connection(conn):
    pool = get_connection_pool()
    pool.putconn(conn)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def format_duration(seconds):
    if seconds is None:
        return "--:--"
    try:
        seconds = int(float(str(seconds).strip()))
    except (ValueError, TypeError):
        return "--:--"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

def calculate_avg_duration(total_seconds, total_calls):
    if not total_calls or total_calls == 0:
        return "--:--"
    try:
        total_seconds = int(float(str(total_seconds).strip()))
        avg_seconds = total_seconds // total_calls
        return format_duration(avg_seconds)
    except (ValueError, TypeError):
        return "--:--"

def format_datetime(dt):
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    return dt.strftime("%d %b %Y, %I:%M %p")

def get_status_badge(status):
    status_lower = (status or "").lower()
    if status_lower == "processed":
        return '<span class="status-processed">● Processed</span>'
    elif "error" in status_lower or "not found" in status_lower:
        return '<span class="status-error">● Error</span>'
    else:
        return '<span class="status-pending">● Pending</span>'

def format_transcription(text):
    if not text:
        return "No transcription available."

    pattern = r"\[(SPEAKER_\d+)\]:\s*(.*?)(?=\[SPEAKER_\d+\]:|$)"
    matches = re.findall(pattern, text, re.DOTALL)

    if not matches:
        return text

    formatted = ""
    for speaker, content in matches:
        speaker_class = f"speaker-{speaker}"
        formatted += f'<span class="speaker-tag {speaker_class}">{speaker}</span>'
        formatted += f'<span style="color: #cbd5e1;">{content.strip()}</span><br><br>'

    return formatted

# ============================================================
# DATA FETCHING FUNCTIONS
# ============================================================

def get_total_agents(selected_date=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if selected_date:
                cur.execute("""
                    SELECT COUNT(DISTINCT user_name)
                    FROM call_audio
                    WHERE user_name IS NOT NULL
                    AND user_name != ''
                    AND status = 'processed'
                    AND DATE(created_at) = %s
                """, (selected_date,))
            else:
                cur.execute("""
                    SELECT COUNT(DISTINCT user_name)
                    FROM call_audio
                    WHERE user_name IS NOT NULL
                    AND user_name != ''
                    AND status = 'processed'
                """)
            return cur.fetchone()[0] or 0
    finally:
        release_connection(conn)

def get_total_calls(selected_date=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if selected_date:
                cur.execute("""
                    SELECT COUNT(*)
                    FROM call_audio
                    WHERE DATE(created_at) = %s
                    AND status = 'processed'
                """, (selected_date,))
            else:
                cur.execute("""
                    SELECT COUNT(*)
                    FROM call_audio
                    WHERE status = 'processed'
                """)
            return cur.fetchone()[0] or 0
    finally:
        release_connection(conn)

def get_agent_list(selected_date=None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if selected_date:
                cur.execute("""
                    SELECT
                        user_name,
                        COUNT(*) as total_calls,
                        SUM(
                            CASE
                                WHEN call_duration_sec IS NULL THEN 0
                                WHEN TRIM(call_duration_sec::text) = '' THEN 0
                                ELSE call_duration_sec::integer
                            END
                        ) as total_duration
                    FROM call_audio
                    WHERE user_name IS NOT NULL
                    AND user_name != ''
                    AND status = 'processed'
                    AND DATE(created_at) = %s
                    GROUP BY user_name
                    ORDER BY total_calls DESC
                """, (selected_date,))
            else:
                cur.execute("""
                    SELECT
                        user_name,
                        COUNT(*) as total_calls,
                        SUM(
                            CASE
                                WHEN call_duration_sec IS NULL THEN 0
                                WHEN TRIM(call_duration_sec::text) = '' THEN 0
                                ELSE call_duration_sec::integer
                            END
                        ) as total_duration
                    FROM call_audio
                    WHERE user_name IS NOT NULL
                    AND user_name != ''
                    AND status = 'processed'
                    GROUP BY user_name
                    ORDER BY total_calls DESC
                """)
            return cur.fetchall()
    finally:
        release_connection(conn)

def get_agent_calls(agent_name, selected_date=None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if selected_date:
                cur.execute("""
                    SELECT
                        call_audio_id,
                        call_recording_link,
                        call_duration_sec,
                        created_at,
                        status,
                        transcribed_text
                    FROM call_audio
                    WHERE user_name = %s
                    AND DATE(created_at) = %s
                    AND status = 'processed'
                    ORDER BY created_at DESC
                """, (agent_name, selected_date))
            else:
                cur.execute("""
                    SELECT
                        call_audio_id,
                        call_recording_link,
                        call_duration_sec,
                        created_at,
                        status,
                        transcribed_text
                    FROM call_audio
                    WHERE user_name = %s
                    AND status = 'processed'
                    ORDER BY created_at DESC
                """, (agent_name,))
            return cur.fetchall()
    finally:
        release_connection(conn)

def get_call_detail(call_audio_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM call_audio
                WHERE call_audio_id = %s
            """, (call_audio_id,))
            return cur.fetchone()
    finally:
        release_connection(conn)

# ============================================================
# SESSION STATE MANAGEMENT
# ============================================================
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'
if 'selected_agent' not in st.session_state:
    st.session_state.selected_agent = None
if 'selected_call' not in st.session_state:
    st.session_state.selected_call = None
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None

# Navigation history stack
if 'history' not in st.session_state:
    st.session_state.history = []
if 'history_index' not in st.session_state:
    st.session_state.history_index = -1

def push_history(page, agent=None, call=None):
    state = {
        'page': page,
        'selected_agent': agent,
        'selected_call': call,
        'selected_date': st.session_state.selected_date
    }
    if st.session_state.history_index < len(st.session_state.history) - 1:
        st.session_state.history = st.session_state.history[:st.session_state.history_index + 1]
    st.session_state.history.append(state)
    st.session_state.history_index += 1

def go_back():
    if st.session_state.history_index > 0:
        st.session_state.history_index -= 1
        state = st.session_state.history[st.session_state.history_index]
        st.session_state.page = state['page']
        st.session_state.selected_agent = state['selected_agent']
        st.session_state.selected_call = state['selected_call']
        st.session_state.selected_date = state['selected_date']
        st.rerun()
    else:
        go_to_dashboard()
        st.rerun()

def refresh_page():
    st.rerun()

def go_to_dashboard():
    push_history('dashboard', None, None)
    st.session_state.page = 'dashboard'
    st.session_state.selected_agent = None
    st.session_state.selected_call = None

def go_to_agent_calls(agent_name):
    push_history('agent_calls', agent_name, None)
    st.session_state.page = 'agent_calls'
    st.session_state.selected_agent = agent_name
    st.session_state.selected_call = None

def go_to_call_detail(call_audio_id):
    push_history('call_detail', st.session_state.selected_agent, call_audio_id)
    st.session_state.page = 'call_detail'
    st.session_state.selected_call = call_audio_id

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding: 1rem 0 1.2rem 0; text-align: center;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #f8fafc; margin-bottom: 0.2rem;">CA</div>
            <div style="font-weight: 700; color: #f1f5f9; font-size: 1rem; letter-spacing: -0.02em;">Call Analytics</div>
            <div style="font-size: 0.68rem; color: #64748b; margin-top: 0.15rem; text-transform: uppercase; letter-spacing: 2px;">Dashboard</div>
        </div>
        <div style="height: 1px; background: rgba(255,255,255,0.05); margin: 0.4rem 0 0.8rem 0;"></div>
        """, unsafe_allow_html=True)
        
        page = st.session_state.page
        
        if st.button("Dashboard", key="nav_dash", use_container_width=True):
            go_to_dashboard()
            st.rerun()
        
        if page == 'agent_calls' or page == 'call_detail':
            if st.button(f"{st.session_state.selected_agent or 'Agent'}", key="nav_agent", use_container_width=True):
                if st.session_state.selected_agent:
                    go_to_agent_calls(st.session_state.selected_agent)
                    st.rerun()
            
            if page == 'call_detail':
                if st.button("Call Detail", key="nav_call", use_container_width=True):
                    pass
        
        st.markdown("""
        <div style="height: 1px; background: rgba(255,255,255,0.05); margin: 0.8rem 0;"></div>
        <div style="padding: 0 0.5rem;">
            <div style="font-size: 0.68rem; color: #475569; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; margin-bottom: 0.6rem;">System</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Refresh Data", key="nav_refresh", use_container_width=True):
            refresh_page()
        
        if st.button("Go Back", key="nav_back", use_container_width=True):
            go_back()
        
        st.markdown("""
        <div style="position: fixed; bottom: 1rem; left: 1rem; right: 1rem;">
            <div style="height: 1px; background: rgba(255,255,255,0.05); margin-bottom: 0.6rem;"></div>
            <div style="font-size: 0.68rem; color: #475569; text-align: center;">
                Call Analytics v2.0<br>
                <span style="color: #10b981;">●</span> System Online
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# PAGE 1: DASHBOARD
# ============================================================
def render_dashboard():
    st.markdown("""
    <div class="top-bar">
        <div>
            <div class="page-title">Dashboard Overview</div>
            <div class="page-subtitle">Real-time insights into your call operations</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 8])
    with col1:
        date_option = st.selectbox(
            "Filter",
            ["All Time", "Specific Date"],
            index=0,
            key="date_filter_option",
            label_visibility="collapsed"
        )
    
    selected_date = None
    with col2:
        if date_option == "Specific Date":
            selected_date = st.date_input(
                "Date",
                value=st.session_state.selected_date or date.today(),
                key="date_picker",
                label_visibility="collapsed"
            )
            st.session_state.selected_date = selected_date
        else:
            st.session_state.selected_date = None
    
    total_agents = get_total_agents(selected_date)
    total_calls = get_total_calls(selected_date)
    avg_calls = round(total_calls / total_agents, 1) if total_agents > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">👥</div>
            <div class="metric-value">{total_agents}</div>
            <div class="metric-label">Total Agents</div>
            <div class="metric-sub">Active workforce</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card metric-card-secondary">
            <div class="metric-icon">📞</div>
            <div class="metric-value">{total_calls}</div>
            <div class="metric-label">Total Calls</div>
            <div class="metric-sub">Processed calls</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card metric-card-success">
            <div class="metric-icon">📊</div>
            <div class="metric-value">{avg_calls}</div>
            <div class="metric-label">Avg Calls / Agent</div>
            <div class="metric-sub">Performance metric</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">Agent Directory</div>', unsafe_allow_html=True)
    
    agents = get_agent_list(selected_date)
    
    if not agents:
        st.info("No agents found for the selected criteria.")
        return
    
    # Table Header
    hc1, hc2, hc3, hc4, hc5 = st.columns([2.5, 1.5, 1.5, 1.5, 1.0])
    with hc1:
        st.markdown('<div class="table-header-text">Agent Name</div>', unsafe_allow_html=True)
    with hc2:
        st.markdown('<div class="table-header-text" style="text-align:center">Total Calls</div>', unsafe_allow_html=True)
    with hc3:
        st.markdown('<div class="table-header-text" style="text-align:center">Total Duration</div>', unsafe_allow_html=True)
    with hc4:
        st.markdown('<div class="table-header-text" style="text-align:center">Avg Duration</div>', unsafe_allow_html=True)
    with hc5:
        st.markdown('<div class="table-header-text" style="text-align:right">Action</div>', unsafe_allow_html=True)
    
    # Agent Rows - Button on SAME LINE using columns
    for agent in agents:
        name = agent['user_name']
        calls = agent['total_calls']
        duration = format_duration(agent['total_duration'])
        avg_duration = calculate_avg_duration(agent['total_duration'], calls)
        
        c1, c2, c3, c4, c5 = st.columns([2.5, 1.5, 1.5, 1.5, 1.0])
        
        with c1:
            st.markdown(f'<div class="cell-name">👤 {name}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div style="text-align:center;padding:0.5rem 0;"><span class="agent-badge">{calls}</span></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div style="text-align:center;padding:0.5rem 0;"><div class="cell-metric-value">⏱️ {duration}</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div style="text-align:center;padding:0.5rem 0;"><span class="agent-avg-badge">{avg_duration}</span></div>', unsafe_allow_html=True)
        with c5:
            if st.button("View →", key=f"agent_btn_{name}", type="primary", use_container_width=True):
                go_to_agent_calls(name)
                st.rerun()

# ============================================================
# PAGE 2: AGENT CALLS
# ============================================================
def render_agent_calls():
    agent_name = st.session_state.selected_agent
    selected_date = st.session_state.selected_date
    
    date_str = f"Calls on {selected_date.strftime('%d %b %Y')}" if selected_date else "All Calls"
    st.markdown(f"""
    <div class="top-bar">
        <div>
            <div class="page-title">👤 {agent_name}</div>
            <div class="page-subtitle">{date_str}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    calls = get_agent_calls(agent_name, selected_date)
    
    if not calls:
        st.info("No calls found for this agent.")
        return
    
    # Table Header
    hc1, hc2, hc3, hc4, hc5 = st.columns([2.0, 1.0, 1.5, 1.0, 1.0])
    with hc1:
        st.markdown('<div class="table-header-text">Call ID</div>', unsafe_allow_html=True)
    with hc2:
        st.markdown('<div class="table-header-text" style="text-align:center">Duration</div>', unsafe_allow_html=True)
    with hc3:
        st.markdown('<div class="table-header-text" style="text-align:center">Date & Time</div>', unsafe_allow_html=True)
    with hc4:
        st.markdown('<div class="table-header-text" style="text-align:center">Status</div>', unsafe_allow_html=True)
    with hc5:
        st.markdown('<div class="table-header-text" style="text-align:right">Action</div>', unsafe_allow_html=True)
    
    # Call Rows - Button on SAME LINE
    for call in calls:
        call_id = call['call_audio_id']
        duration = format_duration(call['call_duration_sec'])
        dt = format_datetime(call['created_at'])
        status = call['status'] or "Unknown"
        
        c1, c2, c3, c4, c5 = st.columns([2.0, 1.0, 1.5, 1.0, 1.0])
        
        with c1:
            st.markdown(f'<div class="cell-muted"><code>{call_id}</code></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="cell-muted" style="text-align:center">⏱️ {duration}</div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="cell-muted" style="text-align:center;font-size:0.82rem">{dt}</div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div style="text-align:center">{get_status_badge(status)}</div>', unsafe_allow_html=True)
        with c5:
            if st.button("View →", key=f"view_{call_id}", type="primary", use_container_width=True):
                go_to_call_detail(call_id)
                st.rerun()

# ============================================================
# PAGE 3: CALL DETAIL
# ============================================================
def render_call_detail():
    call_id = st.session_state.selected_call
    call = get_call_detail(call_id)
    
    if not call:
        st.error("Call not found!")
        return
    
    agent_name = call['user_name'] or "Unknown"
    
    st.markdown(f"""
    <div class="top-bar">
        <div>
            <div class="page-title">📋 Call Details</div>
            <div class="page-subtitle" style="font-family:monospace;">ID: {call_id}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="info-card">
            <div class="info-card-label">Agent</div>
            <div class="info-card-value">{agent_name}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        duration = format_duration(call['call_duration_sec'])
        st.markdown(f"""
        <div class="info-card">
            <div class="info-card-label">Duration</div>
            <div class="info-card-value">{duration}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        dt = format_datetime(call['created_at'])
        st.markdown(f"""
        <div class="info-card">
            <div class="info-card-label">Date</div>
            <div class="info-card-value" style="font-size:0.92rem;">{dt}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        status = call['status'] or "Unknown"
        st.markdown(f"""
        <div class="info-card">
            <div class="info-card-label">Status</div>
            <div style="margin-top:0.2rem;">{get_status_badge(status)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    s3_link = call['call_recording_link']
    if s3_link:
        st.markdown('<div class="section-title">🔊 Call Recording</div>', unsafe_allow_html=True)
        with st.spinner("Loading audio..."):
            audio_url = get_presigned_url(s3_link)
        if audio_url:
            st.audio(audio_url, format="audio/mp3")
        else:
            st.warning("⚠️ Unable to load audio.")
            st.code(s3_link, language="text")
    else:
        st.warning("No recording link available.")
    
    st.markdown('<div class="section-title">📝 Transcription</div>', unsafe_allow_html=True)
    status = (call['status'] or "").lower()
    
    if status == "processed":
        transcribed_text = call['transcribed_text']
        if transcribed_text:
            formatted_text = format_transcription(transcribed_text)
            st.markdown(f"""
            <div class="transcription-box">
                {formatted_text}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Status is 'processed' but no transcription text is available.")
    else:
        st.info(f"""
        🔄 **Transcription not available yet.**\n\n
        Current status: `{call['status'] or 'Unknown'}`\n\n
        The transcription will appear here once the status changes to **'processed'**.
        """)
    
    if call.get('error_message'):
        with st.expander("⚠️ Error Details"):
            st.error(call['error_message'])

# ============================================================
# MAIN ROUTER
# ============================================================
def main():
    render_sidebar()
    
    page = st.session_state.page
    if page == 'dashboard':
        render_dashboard()
    elif page == 'agent_calls':
        render_agent_calls()
    elif page == 'call_detail':
        render_call_detail()

if __name__ == "__main__":
    main()
