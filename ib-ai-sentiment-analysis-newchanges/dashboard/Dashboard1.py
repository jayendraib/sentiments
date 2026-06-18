###################### NEW CODE ON CLOUD WITH NEW UI 18-06-2026 CHANGED DIRCTLY FETCHING DATA FROM CALL AUDIO ######################

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
    initial_sidebar_state="collapsed"
)

# ============================================================
# CUSTOM CSS FOR PROFESSIONAL LOOK
# ============================================================
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 1.5rem;
        color: white;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 50px rgba(0,0,0,0.15);
    }
    .metric-card-secondary {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .metric-card-success {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }
    .agent-calls {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .transcription-box {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        border-radius: 0 12px 12px 0;
        padding: 1.5rem;
        font-family: 'Segoe UI', sans-serif;
        line-height: 1.8;
        color: #2d3436;
        max-height: 500px;
        overflow-y: auto;
    }
    .speaker-tag {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-right: 0.5rem;
        text-transform: uppercase;
    }
    .speaker-SPEAKER_00 {
        background: #e3f2fd;
        color: #1565c0;
    }
    .speaker-SPEAKER_01 {
        background: #fce4ec;
        color: #c2185b;
    }
    .status-processed {
        background: #d4edda;
        color: #155724;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-pending {
        background: #fff3cd;
        color: #856404;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-error {
        background: #f8d7da;
        color: #721c24;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .dashboard-header {
        text-align: center;
        padding: 1rem 0 2rem 0;
    }
    .dashboard-header h1 {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .dashboard-header p {
        color: #888;
        font-size: 1rem;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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
    """Get all calls for a specific agent"""
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

def format_datetime(dt):
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    return dt.strftime("%d %b %Y, %I:%M %p")

def get_status_badge(status):
    status_lower = (status or "").lower()
    if status_lower == "processed":
        return '<span class="status-processed">✅ Processed</span>'
    elif "error" in status_lower or "not found" in status_lower:
        return '<span class="status-error">❌ Error</span>'
    else:
        return '<span class="status-pending">⏳ Pending</span>'

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
        formatted += f'<span style="color: #2d3436;">{content.strip()}</span><br><br>'

    return formatted

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

def go_to_dashboard():
    st.session_state.page = 'dashboard'
    st.session_state.selected_agent = None
    st.session_state.selected_call = None

def go_to_agent_calls(agent_name):
    st.session_state.page = 'agent_calls'
    st.session_state.selected_agent = agent_name
    st.session_state.selected_call = None

def go_to_call_detail(call_audio_id):
    st.session_state.page = 'call_detail'
    st.session_state.selected_call = call_audio_id

# ============================================================
# PAGE 1: DASHBOARD
# ============================================================
def render_dashboard():
    st.markdown("""
    <div class="dashboard-header">
        <h1>📞 Call Analytics Dashboard</h1>
        <p>Real-time insights into your call operations</p>
    </div>
    """, unsafe_allow_html=True)

    # Date Filter
    col1, col2, col3 = st.columns([2, 2, 6])
    with col1:
        st.markdown("<br>", unsafe_allow_html=True)
        date_option = st.selectbox(
            "Filter By",
            ["All Time", "Specific Date"],
            index=0,
            key="date_filter_option"
        )

    selected_date = None
    with col2:
        if date_option == "Specific Date":
            st.markdown("<br>", unsafe_allow_html=True)
            selected_date = st.date_input(
                "Select Date",
                value=st.session_state.selected_date or date.today(),
                key="date_picker"
            )
            st.session_state.selected_date = selected_date
        else:
            st.session_state.selected_date = None

    # Metrics
    total_agents = get_total_agents(selected_date)
    total_calls = get_total_calls(selected_date)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_agents}</div>
            <div class="metric-label">Total Agents</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card metric-card-secondary">
            <div class="metric-value">{total_calls}</div>
            <div class="metric-label">Total Calls</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        avg_calls = round(total_calls / total_agents, 1) if total_agents > 0 else 0
        st.markdown(f"""
        <div class="metric-card metric-card-success">
            <div class="metric-value">{avg_calls}</div>
            <div class="metric-label">Avg Calls/Agent</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Agent List
    st.markdown("""
    <h3 style="color: #1a1a2e; margin-bottom: 1rem;">
        👥 Agent Directory
    </h3>
    """, unsafe_allow_html=True)

    agents = get_agent_list(selected_date)

    if not agents:
        st.info("No agents found for the selected criteria.")
        return

    for agent in agents:
        name = agent['user_name']
        calls = agent['total_calls']
        duration = format_duration(agent['total_duration'])

        col1, col2, col3 = st.columns([4, 2, 2])

        with col1:
            if st.button(
                f"👤 {name}",
                key=f"agent_{name}",
                use_container_width=True,
                type="secondary"
            ):
                go_to_agent_calls(name)
                st.rerun()

        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding-top: 0.5rem;">
                <span class="agent-calls">{calls} Calls</span>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="text-align: center; padding-top: 0.6rem; color: #888; font-size: 0.9rem;">
                ⏱️ {duration}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.3;'>", unsafe_allow_html=True)

# ============================================================
# PAGE 2: AGENT CALLS
# ============================================================
def render_agent_calls():
    agent_name = st.session_state.selected_agent
    selected_date = st.session_state.selected_date

    col1, col2 = st.columns([1, 9])
    with col1:
        if st.button("← Back", key="back_to_dash"):
            go_to_dashboard()
            st.rerun()

    with col2:
        st.markdown(f"""
        <h2 style="color: #1a1a2e; margin: 0;">
            👤 {agent_name}
        </h2>
        <p style="color: #888; margin: 0;">
            {"All calls" if not selected_date else f"Calls on {selected_date.strftime('%d %b %Y')}"}
        </p>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    calls = get_agent_calls(agent_name, selected_date)

    if not calls:
        st.info("No calls found for this agent.")
        return

    # Table header
    header_cols = st.columns([3, 2, 2, 2, 2])
    headers = ["Call ID", "Duration", "Date & Time", "Status", "Action"]
    for col, header in zip(header_cols, headers):
        col.markdown(f"""
        <div style="font-weight: 700; color: #667eea; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">
            {header}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.2;'>", unsafe_allow_html=True)

    for call in calls:
        call_id = call['call_audio_id']
        duration = format_duration(call['call_duration_sec'])
        dt = format_datetime(call['created_at'])
        status = call['status'] or "Unknown"

        cols = st.columns([3, 2, 2, 2, 2])

        with cols[0]:
            st.markdown(f"<code style='font-size: 0.85rem;'>{call_id}</code>", unsafe_allow_html=True)

        with cols[1]:
            st.markdown(f"<span style='color: #2d3436; font-weight: 500;'>⏱️ {duration}</span>", unsafe_allow_html=True)

        with cols[2]:
            st.markdown(f"<span style='color: #666; font-size: 0.9rem;'>{dt}</span>", unsafe_allow_html=True)

        with cols[3]:
            st.markdown(get_status_badge(status), unsafe_allow_html=True)

        with cols[4]:
            if st.button("View →", key=f"view_{call_id}", type="primary"):
                go_to_call_detail(call_id)
                st.rerun()

        st.markdown("<hr style='margin: 0.3rem 0; opacity: 0.15;'>", unsafe_allow_html=True)

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

    col1, col2 = st.columns([1, 9])
    with col1:
        if st.button("← Back", key="back_to_calls"):
            go_to_agent_calls(agent_name)
            st.rerun()

    with col2:
        st.markdown(f"""
        <h2 style="color: #1a1a2e; margin: 0;">
            📋 Call Details
        </h2>
        <p style="color: #888; margin: 0; font-family: monospace;">
            ID: {call_id}
        </p>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Call info cards
    info_col1, info_col2, info_col3, info_col4 = st.columns(4)

    with info_col1:
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 1rem; border: 1px solid #e0e0e0; text-align: center;">
            <div style="font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">Agent</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #1a1a2e; margin-top: 0.3rem;">{agent_name}</div>
        </div>
        """, unsafe_allow_html=True)

    with info_col2:
        duration = format_duration(call['call_duration_sec'])
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 1rem; border: 1px solid #e0e0e0; text-align: center;">
            <div style="font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">Duration</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #1a1a2e; margin-top: 0.3rem;">{duration}</div>
        </div>
        """, unsafe_allow_html=True)

    with info_col3:
        dt = format_datetime(call['created_at'])
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 1rem; border: 1px solid #e0e0e0; text-align: center;">
            <div style="font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">Date</div>
            <div style="font-size: 1rem; font-weight: 600; color: #1a1a2e; margin-top: 0.3rem;">{dt}</div>
        </div>
        """, unsafe_allow_html=True)

    with info_col4:
        status = call['status'] or "Unknown"
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 1rem; border: 1px solid #e0e0e0; text-align: center;">
            <div style="font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">Status</div>
            <div style="margin-top: 0.3rem;">{get_status_badge(status)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Audio Player
    s3_link = call['call_recording_link']

    if s3_link:
        st.markdown("""
        <h3 style="color: #1a1a2e; margin-bottom: 1rem;">
            🔊 Call Recording
        </h3>
        """, unsafe_allow_html=True)

        with st.spinner("Loading audio..."):
            audio_url = get_presigned_url(s3_link)

        if audio_url:
            st.audio(audio_url, format="audio/mp3")
        else:
            st.warning("⚠️ Unable to load audio. The recording may not be available.")
            st.code(s3_link, language="text")
    else:
        st.warning("No recording link available for this call.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Transcription
    st.markdown("""
    <h3 style="color: #1a1a2e; margin-bottom: 1rem;">
        📝 Transcription
    </h3>
    """, unsafe_allow_html=True)

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
        🔄 **Transcription not available yet.**

        Current status: `{call['status'] or 'Unknown'}`

        The transcription will appear here once the status changes to **'processed'**.
        """)

    if call.get('error_message'):
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("⚠️ Error Details"):
            st.error(call['error_message'])

# ============================================================
# MAIN ROUTER
# ============================================================
def main():
    page = st.session_state.page

    if page == 'dashboard':
        render_dashboard()
    elif page == 'agent_calls':
        render_agent_calls()
    elif page == 'call_detail':
        render_call_detail()

if __name__ == "__main__":
    main()


