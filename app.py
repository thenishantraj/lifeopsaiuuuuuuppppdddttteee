import streamlit as st
import os
import sys
from datetime import datetime, timedelta
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import LifeOpsDatabase
from crew_setup import LifeOpsCrew

os.environ["OPENAI_API_KEY"] = "not-required"
os.environ["OPENAI_API_BASE"] = ""
os.environ["OPENAI_MODEL_NAME"] = ""

st.set_page_config(
    page_title="LifeOps AI — Life Management Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

db = LifeOpsDatabase()


def get_api_key() -> str:
    key = ""
    try:
        key = st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        pass
    if not key:
        key = os.environ.get("GOOGLE_API_KEY", "")
    return key


def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #F7F8FC !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #1A1D23 !important;
}

#MainMenu, footer, header, [data-testid="stSidebar"],
[data-testid="collapsedControl"], [data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
}

[data-testid="stMainBlockContainer"], .block-container {
    padding: 88px 28px 40px 28px !important;
    max-width: 1320px !important;
}

/* ─── TOPNAV ─── */
.topnav {
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
    height: 62px;
    background: rgba(255,255,255,0.92);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-bottom: 1px solid #E8EBF3;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 28px;
    gap: 16px;
}
.topnav-brand {
    font-size: 18px; font-weight: 700; color: #1A1D23;
    display: flex; align-items: center; gap: 8px; white-space: nowrap;
    letter-spacing: -0.3px;
}
.topnav-brand .brand-dot { color: #6366F1; }
.topnav-pages {
    display: flex; align-items: center; gap: 2px; flex: 1; justify-content: center;
}
.topnav-right { display: flex; align-items: center; gap: 10px; }
.user-chip {
    background: #F0F0FF; border-radius: 20px; padding: 5px 12px;
    font-size: 13px; font-weight: 500; color: #4F46E5;
}
.streak-chip {
    background: #FFF7ED; border-radius: 20px; padding: 5px 12px;
    font-size: 13px; font-weight: 600; color: #D97706;
}

/* ─── STREAMLIT BUTTON OVERRIDES FOR TOPNAV ─── */
.topnav-pages div[data-testid="stButton"] > button,
.topnav-right div[data-testid="stButton"] > button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
    border-radius: 8px !important;
    border: none !important;
    background: transparent !important;
    color: #5B6170 !important;
    transition: all 0.15s ease !important;
    white-space: nowrap !important;
    line-height: 1.4 !important;
    height: auto !important;
    min-height: 32px !important;
}
.topnav-pages div[data-testid="stButton"] > button:hover {
    background: #F0F1F9 !important;
    color: #1A1D23 !important;
}
.topnav-pages div[data-testid="stButton"][data-active="true"] > button {
    background: #EEF2FF !important;
    color: #4F46E5 !important;
    font-weight: 600 !important;
}

/* ─── PAGE HEADER ─── */
.page-header { margin-bottom: 28px; }
.page-title {
    font-size: 26px; font-weight: 700; color: #1A1D23;
    letter-spacing: -0.5px; line-height: 1.2;
}
.page-sub { font-size: 14px; color: #8B909A; margin-top: 4px; font-weight: 400; }

/* ─── CARDS ─── */
.card {
    background: #fff;
    border-radius: 14px;
    padding: 20px 22px;
    border: 1px solid #EAECF0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s;
    margin-bottom: 16px;
}
.card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.07); }

.metric-card {
    background: #fff;
    border-radius: 14px;
    padding: 20px;
    border: 1px solid #EAECF0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    text-align: center;
    transition: all 0.2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
.metric-icon { font-size: 28px; margin-bottom: 8px; }
.metric-value { font-size: 28px; font-weight: 700; color: #1A1D23; letter-spacing: -0.5px; }
.metric-label { font-size: 11px; font-weight: 500; color: #8B909A; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 4px; }
.metric-change { font-size: 12px; font-weight: 500; color: #16A34A; margin-top: 2px; }

/* ─── SECTION HEADERS ─── */
.section-header {
    font-size: 16px; font-weight: 600; color: #1A1D23;
    letter-spacing: -0.2px; margin-bottom: 14px; margin-top: 8px;
    display: flex; align-items: center; gap: 8px;
}

/* ─── LIST ITEMS ─── */
.list-item {
    background: #FAFBFD; border: 1px solid #EAECF0;
    border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
    transition: all 0.15s;
}
.list-item:hover { background: #F5F5FF; border-color: #C7C7F5; }
.list-item-title { font-weight: 600; font-size: 14px; color: #1A1D23; }
.list-item-meta { font-size: 12px; color: #8B909A; margin-top: 3px; }

/* ─── BADGES ─── */
.badge {
    display: inline-block; padding: 2px 9px;
    border-radius: 20px; font-size: 11px; font-weight: 600;
}
.badge-health { background: #DCFCE7; color: #166534; }
.badge-finance { background: #FEF9C3; color: #854D0E; }
.badge-study { background: #EEF2FF; color: #3730A3; }
.badge-personal { background: #F3E8FF; color: #6B21A8; }
.badge-work { background: #FEE2E2; color: #991B1B; }
.badge-urgent { background: #FFF1F2; color: #BE123C; }
.badge-medium { background: #FFF7ED; color: #C2410C; }
.badge-low { background: #F0FDF4; color: #166534; }

/* ─── TIMER ─── */
.timer-card {
    background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
    border-radius: 18px; padding: 32px 24px; text-align: center;
    color: white; box-shadow: 0 8px 32px rgba(99,102,241,0.3);
}
.timer-phase {
    display: inline-block; padding: 4px 16px; border-radius: 20px;
    background: rgba(255,255,255,0.2); font-size: 12px; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 16px;
}
.timer-digits {
    font-family: 'DM Mono', monospace; font-size: 64px; font-weight: 500;
    letter-spacing: -2px; line-height: 1; margin-bottom: 8px;
}
.timer-subject { font-size: 15px; opacity: 0.85; }

/* ─── PROFILE ─── */
.profile-avatar-lg {
    width: 80px; height: 80px; border-radius: 50%;
    background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 32px; margin: 0 auto 12px auto;
    box-shadow: 0 4px 16px rgba(99,102,241,0.3);
}
.stat-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
    margin-top: 16px;
}
.stat-item {
    text-align: center; background: #F7F8FC; border-radius: 10px; padding: 12px 8px;
}
.stat-val { font-size: 20px; font-weight: 700; color: #1A1D23; }
.stat-lbl { font-size: 11px; color: #8B909A; margin-top: 2px; }

/* ─── REPORT CARD ─── */
.report-card {
    background: #fff; border-radius: 14px; padding: 24px;
    border: 1px solid #EAECF0; margin-bottom: 16px;
}
.report-card h2 { font-size: 18px; font-weight: 700; color: #1A1D23; margin-bottom: 12px; }
.report-card h3 { font-size: 15px; font-weight: 600; color: #374151; margin: 12px 0 6px; }
.report-card ul { margin-left: 18px; }
.report-card li { font-size: 14px; color: #4B5563; line-height: 1.7; }

/* ─── PROGRESS ─── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #6366F1, #8B5CF6) !important;
    border-radius: 4px !important;
}

/* ─── INPUTS ─── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    border-radius: 8px !important; border: 1px solid #E2E5EF !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 14px !important;
    background: #fff !important; color: #1A1D23 !important;
    transition: border-color 0.15s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}
.stSelectbox > div > div {
    border-radius: 8px !important; border: 1px solid #E2E5EF !important;
}

/* ─── BUTTONS ─── */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important; border-radius: 9px !important;
    font-size: 14px !important; transition: all 0.15s ease !important;
    border: 1px solid #E2E5EF !important;
    background: #fff !important; color: #374151 !important;
}
.stButton > button:hover {
    background: #F7F8FC !important; border-color: #C7C7F5 !important;
    color: #4F46E5 !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
    color: white !important; border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(99,102,241,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(99,102,241,0.45) !important;
    color: white !important;
}

/* ─── TABS ─── */
.stTabs [data-baseweb="tab-list"] {
    background: #F7F8FC !important; border-radius: 10px !important;
    padding: 3px !important; gap: 2px !important; border: none !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; border-radius: 8px !important;
    color: #8B909A !important; font-weight: 500 !important; font-size: 13px !important;
    padding: 6px 14px !important; border: none !important;
}
.stTabs [aria-selected="true"] {
    background: white !important; color: #4F46E5 !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}

/* ─── EXPANDER ─── */
.streamlit-expanderHeader {
    background: #FAFBFD !important; border-radius: 10px !important;
    border: 1px solid #EAECF0 !important; font-weight: 600 !important;
    font-size: 14px !important;
}

/* ─── SCROLLBAR ─── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #9CA3AF; }

/* ─── LOGIN ─── */
.login-wrap {
    min-height: 100vh; background: linear-gradient(135deg, #EEF2FF 0%, #F5F3FF 50%, #FAF5FF 100%);
    display: flex; align-items: center; justify-content: center; padding: 40px 16px;
}
.login-card {
    background: white; border-radius: 20px; padding: 40px 36px;
    max-width: 460px; width: 100%;
    box-shadow: 0 20px 60px rgba(99,102,241,0.12), 0 4px 16px rgba(0,0,0,0.06);
    border: 1px solid rgba(99,102,241,0.08);
}
.login-logo {
    text-align: center; margin-bottom: 28px;
}
.login-logo-icon { font-size: 48px; margin-bottom: 10px; }
.login-logo-title {
    font-size: 24px; font-weight: 700; color: #1A1D23; letter-spacing: -0.5px;
}
.login-logo-sub { font-size: 14px; color: #8B909A; margin-top: 4px; }

/* ─── ANALYSIS SCORE ─── */
.score-ring {
    width: 80px; height: 80px; border-radius: 50%;
    background: conic-gradient(#6366F1 0deg, #EEF2FF 0deg);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; font-weight: 700; color: #4F46E5;
    box-shadow: inset 0 0 0 8px white;
    margin: 0 auto 8px;
}

/* ─── INSIGHTS ─── */
.insight-card {
    background: linear-gradient(135deg, #EEF2FF, #F5F3FF);
    border: 1px solid #C7D2FE; border-radius: 12px; padding: 16px 18px;
    margin-bottom: 10px;
}
.insight-card strong { color: #4338CA; font-size: 14px; }
.insight-card p { font-size: 13px; color: #4B5563; margin-top: 4px; line-height: 1.6; }

/* ─── CALENDAR HEAT ─── */
.heat-row { display: flex; gap: 3px; margin-bottom: 3px; }
.heat-cell {
    width: 12px; height: 12px; border-radius: 2px; background: #EEF2FF;
}
.heat-1 { background: #C7D2FE; }
.heat-2 { background: #818CF8; }
.heat-3 { background: #4F46E5; }

/* ─── DARK THEME ─── */
[data-theme="dark"] .stApp, [data-theme="dark"] html, [data-theme="dark"] body {
    background: #0F1117 !important; color: #E5E7EB !important;
}

/* RESPONSIVE */
@media (max-width: 768px) {
    [data-testid="stMainBlockContainer"], .block-container {
        padding: 72px 12px 24px 12px !important;
    }
    .topnav { padding: 0 12px; }
    .metric-value { font-size: 22px; }
}
</style>
""", unsafe_allow_html=True)


def init_state():
    defaults = {
        'authenticated': False, 'user_id': None, 'user_data': None,
        'current_page': 'Dashboard', 'analysis_results': None,
        'user_inputs': {}, 'processing': False,
        'pomodoro_active': False, 'pomodoro_time': 25 * 60,
        'pomodoro_work': True, 'pomodoro_subject': '',
        'break_time': 5 * 60,
        'todo_items': [], 'medicines': [], 'bills': [], 'notes': []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def load_user_data():
    if st.session_state.authenticated and st.session_state.user_id:
        uid = st.session_state.user_id
        st.session_state.todo_items = db.get_pending_actions(uid)
        st.session_state.medicines = db.get_all_medicines(uid)
        st.session_state.bills = db.get_all_bills(uid)
        st.session_state.notes = db.get_notes(uid)


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def render_topnav():
    pages = [
        ("📊", "Dashboard"), ("💊", "Health Vault"),
        ("💰", "Finance Hub"), ("📚", "Study Center"),
        ("⚡", "Productivity"), ("👤", "Profile"),
    ]
    cur = st.session_state.current_page
    user = st.session_state.user_data or {}
    name = user.get("name", "User").split()[0]

    try:
        streak = db.get_consistency_streak(st.session_state.user_id)
    except Exception:
        streak = 0

    st.markdown('<div class="topnav">', unsafe_allow_html=True)
    left, center, right = st.columns([2, 6, 2])

    with left:
        st.markdown(
            '<div class="topnav-brand">🧠 LifeOps<span class="brand-dot">.</span></div>',
            unsafe_allow_html=True
        )

    with center:
        st.markdown('<div class="topnav-pages">', unsafe_allow_html=True)
        cols = st.columns(len(pages))
        for i, (icon, page) in enumerate(pages):
            with cols[i]:
                label = f"{icon} {page}" if cur != page else f"**{icon} {page}**"
                btn_type = "primary" if cur == page else "secondary"
                if st.button(f"{icon} {page}", key=f"nav_{page}", use_container_width=True, type=btn_type):
                    st.session_state.current_page = page
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        c1, c2 = st.columns([2, 1])
        with c1:
            if streak > 0:
                st.markdown(f'<div class="streak-chip">🔥 {streak}d</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="user-chip">👋 {name}</div>', unsafe_allow_html=True)
        with c2:
            if st.button("↩", key="nav_logout", help="Logout"):
                logout()

    st.markdown('</div>', unsafe_allow_html=True)


def login_page():
    st.markdown("""
<style>
[data-testid="stMainBlockContainer"], .block-container {
    padding: 20px !important; max-width: 100% !important;
}
</style>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding: 40px 0 20px;">
            <div style="font-size:52px; margin-bottom:12px;">🧠</div>
            <div style="font-size:26px; font-weight:700; color:#1A1D23; letter-spacing:-0.5px;">LifeOps AI</div>
            <div style="font-size:14px; color:#8B909A; margin-top:6px; margin-bottom:32px;">Your intelligent life management platform</div>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["  Sign In  ", "  Create Account  "])

        with tab1:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email address", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Sign in to LifeOps →", type="primary", use_container_width=True)
                if submitted:
                    if not email or not password:
                        st.error("Please fill in all fields")
                    else:
                        user = db.authenticate_user(email, password)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user_id = user['id']
                            st.session_state.user_data = user
                            st.session_state.current_page = "Dashboard"
                            os.environ["GOOGLE_API_KEY"] = get_api_key()
                            load_user_data()
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please try again.")

        with tab2:
            with st.form("signup_form", clear_on_submit=True):
                s_name = st.text_input("Full name", placeholder="Alex Kumar")
                s_email = st.text_input("Email address", placeholder="you@example.com")
                s_pass = st.text_input("Password", type="password", placeholder="Min 6 characters")
                s_pass2 = st.text_input("Confirm password", type="password", placeholder="Repeat password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Create free account →", type="primary", use_container_width=True):
                    if not all([s_name, s_email, s_pass, s_pass2]):
                        st.error("Please fill in all fields")
                    elif len(s_pass) < 6:
                        st.error("Password must be at least 6 characters")
                    elif s_pass != s_pass2:
                        st.error("Passwords do not match")
                    elif db.create_user(s_email, s_pass, s_name):
                        st.success("✅ Account created! Please sign in.")
                    else:
                        st.error("Email already registered. Please sign in.")

        st.markdown("""
        <div style="text-align:center; margin-top:32px; padding: 16px; background:#F7F8FC; border-radius:12px;">
            <div style="font-size:13px; font-weight:600; color:#1A1D23; margin-bottom:8px;">✨ What's included</div>
            <div style="font-size:12px; color:#8B909A; line-height:2;">
                🤖 AI Life Analysis &nbsp;·&nbsp; 💊 Health Vault &nbsp;·&nbsp; 💰 Finance Hub<br>
                📚 Study Optimizer &nbsp;·&nbsp; ⚡ Task Manager &nbsp;·&nbsp; 📝 Smart Notes
            </div>
        </div>
        """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str):
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">{title}</div>
        <div class="page-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def create_health_chart(stress: int, sleep: float):
    fig = go.Figure()
    categories = ['Stress Mgmt', 'Sleep', 'Hydration', 'Exercise', 'Nutrition']
    stress_score = max(0, 10 - stress) * 10
    sleep_score = min(100, (sleep / 8) * 100)
    values = [stress_score, sleep_score, 70, 50, 65]
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]], theta=categories + [categories[0]],
        fill='toself', name='Current',
        line_color='#6366F1', fillcolor='rgba(99,102,241,0.15)',
        line_width=2
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9), gridcolor='#E5E7EB'),
            angularaxis=dict(tickfont=dict(size=11, color='#4B5563')),
            bgcolor='white'
        ),
        showlegend=False, height=280,
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=20, b=20)
    )
    return fig


def create_finance_chart(budget: float, expenses: float):
    savings = max(0, budget - expenses)
    labels = ['Expenses', 'Savings']
    values = [expenses, savings]
    colors = ['#F87171', '#34D399']
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.65,
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        textinfo='none', hovertemplate='%{label}: $%{value:,.0f}<extra></extra>'
    )])
    rate = int(savings / budget * 100) if budget > 0 else 0
    fig.add_annotation(text=f'{rate}%<br><span style="font-size:10px">saved</span>', x=0.5, y=0.5,
                       font=dict(size=20, color='#1A1D23', family='DM Sans'), showarrow=False)
    fig.update_layout(
        showlegend=True, height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', yanchor='bottom', y=-0.1, xanchor='center', x=0.5, font=dict(size=12)),
        margin=dict(l=10, r=10, t=10, b=30)
    )
    return fig


def create_study_chart(days: int, hours: int):
    if days <= 0: days = 7
    days_to_show = min(days, 14)
    dates, study_hrs = [], []
    for i in range(days_to_show):
        d = datetime.now() + timedelta(days=i)
        dates.append(d.strftime("%b %d"))
        if i >= days_to_show - 2:
            study_hrs.append(max(1, hours * 0.5))
        elif i >= days_to_show - 5:
            study_hrs.append(hours * 1.1)
        else:
            study_hrs.append(hours)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dates, y=study_hrs, marker_color='#818CF8',
        text=[f'{h:.1f}h' for h in study_hrs], textposition='outside',
        textfont=dict(size=10), hovertemplate='%{x}: %{y:.1f}h<extra></extra>'
    ))
    fig.update_layout(
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor='#F3F4F6', tickfont=dict(size=10), title='Hours'),
        height=240, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=10, t=20, b=20)
    )
    return fig


def dashboard_page():
    page_header("📊 Life Dashboard", "Your command center — everything at a glance")
    uid = st.session_state.user_id
    inputs = st.session_state.user_inputs

    # Metrics row
    try:
        streak = db.get_consistency_streak(uid)
        stats = db.get_user_statistics(uid)
    except Exception:
        streak, stats = 0, {"total_actions": 0, "completed_actions": 0, "completion_rate": 0}

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        stress = inputs.get('stress_level', 5)
        color = "#EF4444" if stress >= 7 else "#F59E0B" if stress >= 4 else "#10B981"
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">🧠</div>
            <div class="metric-value" style="color:{color}">{stress}/10</div>
            <div class="metric-label">Stress Level</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        days_left = 0
        if inputs.get('exam_date'):
            try:
                target = datetime.strptime(inputs['exam_date'], "%Y-%m-%d")
                days_left = max(0, (target - datetime.now()).days)
            except Exception:
                pass
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">📅</div>
            <div class="metric-value">{days_left}</div>
            <div class="metric-label">Days to Exam</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        budget = inputs.get('monthly_budget', 0)
        expenses = inputs.get('current_expenses', 0)
        savings = max(0, budget - expenses)
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">💰</div>
            <div class="metric-value">${savings:,}</div>
            <div class="metric-label">Monthly Savings</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">🔥</div>
            <div class="metric-value">{streak}</div>
            <div class="metric-label">Day Streak</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # AI Analysis config
    with st.expander("🚀 Run AI Life Analysis", expanded=not bool(st.session_state.analysis_results)):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**🩺 Health**")
            stress_level = st.slider("Stress level", 1, 10, inputs.get('stress_level', 5), key="sl_stress")
            sleep_hours = st.number_input("Sleep hours/night", 0, 12, inputs.get('sleep_hours', 7), key="sl_sleep")
            exercise = st.selectbox("Exercise frequency", ["Rarely", "1–2×/week", "3–4×/week", "Daily"], key="sl_ex")
        with c2:
            st.markdown("**📚 Study**")
            exam_date = st.date_input("Exam date", min_value=datetime.now().date(),
                                       value=(datetime.now() + timedelta(days=30)).date(), key="sl_exam")
            study_hrs = st.number_input("Study hours/day", 0, 14, inputs.get('current_study_hours', 3), key="sl_shrs")
        with c3:
            st.markdown("**💰 Finance**")
            budget = st.number_input("Monthly budget ($)", 0, 100000, inputs.get('monthly_budget', 2000), step=100, key="sl_budget")
            expenses = st.number_input("Monthly expenses ($)", 0, 100000, inputs.get('current_expenses', 1500), step=100, key="sl_exp")

        problem = st.text_area("What's your main challenge right now?",
                                inputs.get('problem', 'I need to balance exam prep, stay healthy, and manage my budget.'),
                                height=80, key="sl_problem")

        st.session_state.user_inputs = {
            'stress_level': stress_level, 'sleep_hours': sleep_hours,
            'exercise_frequency': exercise, 'exam_date': exam_date.strftime("%Y-%m-%d"),
            'days_until_exam': (exam_date - datetime.now().date()).days,
            'current_study_hours': study_hrs, 'monthly_budget': budget,
            'current_expenses': expenses, 'problem': problem
        }

        api_key = get_api_key()
        if not api_key:
            st.warning("⚠️ **Google API Key not configured.** Analysis will use smart offline mode. To enable live AI, add `GOOGLE_API_KEY` to Streamlit Secrets.")

        c1, _, c3 = st.columns([2, 1, 2])
        with c1:
            if st.button("⚡ Analyze My Life", type="primary", use_container_width=True, key="run_analysis"):
                run_ai_analysis(st.session_state.user_inputs)
        with c3:
            if st.session_state.analysis_results:
                if st.button("🗑️ Clear Results", use_container_width=True, key="clear_analysis"):
                    st.session_state.analysis_results = None
                    st.rerun()

    # Charts row
    if inputs:
        ca, cb, cc = st.columns(3)
        with ca:
            st.markdown('<div class="section-header">🩺 Health Radar</div>', unsafe_allow_html=True)
            st.plotly_chart(create_health_chart(stress_level, sleep_hours), use_container_width=True, config={"displayModeBar": False})
        with cb:
            st.markdown('<div class="section-header">💰 Budget Split</div>', unsafe_allow_html=True)
            st.plotly_chart(create_finance_chart(budget, expenses), use_container_width=True, config={"displayModeBar": False})
        with cc:
            st.markdown('<div class="section-header">📚 Study Plan</div>', unsafe_allow_html=True)
            st.plotly_chart(create_study_chart(
                (exam_date - datetime.now().date()).days if inputs.get('exam_date') else 30,
                study_hrs
            ), use_container_width=True, config={"displayModeBar": False})

    # AI Results
    if st.session_state.analysis_results:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">🤖 AI Analysis Report</div>', unsafe_allow_html=True)
        results = st.session_state.analysis_results
        vr = results.get("validation_report", {})
        score = vr.get("overall_score", 80)

        s1, s2, s3, s4 = st.columns(4)
        for col, label, val in [(s1, "Health", "✅"), (s2, "Finance", "✅"), (s3, "Study", "✅"), (s4, "Score", f"{score}/100")]:
            with col:
                st.metric(label, val if label != "Score" else val)

        cross = results.get("cross_domain_insights", "")
        if cross:
            st.markdown('<div class="insight-card"><strong>🔗 Cross-Domain Insights</strong><p>' + cross.replace('\n', '<br>') + '</p></div>', unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["🩺 Health Plan", "💰 Finance Plan", "📚 Study Plan", "🎯 Master Plan"])
        for tab, key in [(t1, "health"), (t2, "finance"), (t3, "study"), (t4, "coordination")]:
            with tab:
                st.markdown(f'<div class="report-card">', unsafe_allow_html=True)
                st.markdown(results.get(key, "No data available."))
                st.markdown('</div>', unsafe_allow_html=True)


def health_vault_page():
    page_header("💊 Health Vault", "Track medicines, log health data, monitor trends")
    uid = st.session_state.user_id

    tab1, tab2, tab3 = st.tabs(["💊 Medicines", "📝 Daily Log", "📈 Trends"])

    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            with st.expander("➕ Add Medicine", expanded=False):
                m1, m2 = st.columns(2)
                with m1:
                    med_name = st.text_input("Name", placeholder="e.g. Vitamin D3", key="med_name")
                    med_dose = st.text_input("Dosage", placeholder="e.g. 1000 IU", key="med_dose")
                with m2:
                    med_freq = st.selectbox("Frequency", ["Daily", "Twice Daily", "Weekly", "As Needed"], key="med_freq")
                    med_time = st.selectbox("Time", ["Morning", "Afternoon", "Evening", "Night", "Anytime"], key="med_time")
                if st.button("Add Medicine", type="primary", key="add_med"):
                    if med_name.strip():
                        db.add_medicine(uid, med_name.strip(), med_dose, med_freq, med_time)
                        st.session_state.medicines = db.get_all_medicines(uid)
                        st.success(f"Added {med_name}")
                        st.rerun()
                    else:
                        st.warning("Enter medicine name")

        with c2:
            meds = db.get_all_medicines(uid)
            if meds:
                st.markdown(f'<div class="section-header">💊 Active Medicines ({len(meds)})</div>', unsafe_allow_html=True)
                for med in meds:
                    col_a, col_b, col_c = st.columns([5, 1, 1])
                    last_taken = "Never"
                    if med.get('last_taken'):
                        try:
                            lt = datetime.fromisoformat(med['last_taken'])
                            diff = (datetime.now() - lt).days
                            last_taken = "Today" if diff == 0 else f"{diff}d ago"
                        except Exception:
                            last_taken = "Unknown"
                    with col_a:
                        st.markdown(f"""<div class="list-item">
                            <div class="list-item-title">💊 {med['name']}</div>
                            <div class="list-item-meta">{med.get('dosage','—')} · {med.get('frequency','—')} · {med.get('time_of_day','Anytime')} · Last: {last_taken}</div>
                        </div>""", unsafe_allow_html=True)
                    with col_b:
                        if st.button("✅", key=f"med_take_{med['id']}", help="Mark taken"):
                            db.update_medicine_taken(uid, med['id'])
                            st.success("Marked!")
                            st.rerun()
                    with col_c:
                        if st.button("🗑", key=f"med_del_{med['id']}", help="Remove"):
                            db.delete_medicine(uid, med['id'])
                            st.session_state.medicines = db.get_all_medicines(uid)
                            st.rerun()
            else:
                st.info("No medicines added yet. Start by adding one above.")

    with tab2:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown('<div class="section-header">📝 Log Today\'s Health</div>', unsafe_allow_html=True)
            log_date = st.date_input("Date", datetime.now().date(), key="hl_date")
            mood = st.slider("Mood (1=bad, 10=great)", 1, 10, 6, key="hl_mood")
            sleep_q = st.slider("Sleep quality", 1, 10, 7, key="hl_sleep")
            energy = st.slider("Energy level", 1, 10, 6, key="hl_energy")
            water = st.number_input("Water glasses", 0, 20, 8, key="hl_water")
            weight = st.number_input("Weight (kg, optional)", 0.0, 300.0, 0.0, step=0.1, key="hl_weight")
            symptoms = st.text_area("Notes / Symptoms", placeholder="How are you feeling today?", height=80, key="hl_symptoms")

            if st.button("💾 Save Log", type="primary", key="save_hl"):
                db.add_health_log(uid, log_date.strftime("%Y-%m-%d"), symptoms, sleep_q, energy, water, mood, weight if weight > 0 else 0)
                st.success("Health log saved!")
                db._record_checkin(uid)

        with c2:
            st.markdown('<div class="section-header">📋 Recent Logs</div>', unsafe_allow_html=True)
            recent = db.get_health_logs(uid, days=7)
            if recent:
                for log in recent[:5]:
                    st.markdown(f"""<div class="list-item">
                        <div class="list-item-title">📅 {log['date']}</div>
                        <div class="list-item-meta">
                            Mood: {log.get('mood', '—')}/10 · Energy: {log.get('energy_level', '—')}/10 · Sleep: {log.get('sleep_quality', '—')}/10 · Water: {log.get('water_intake', '—')}🥤
                        </div>
                        {f'<div class="list-item-meta">📝 {log["symptoms"][:60]}...</div>' if log.get('symptoms') else ''}
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("No logs yet. Log your first day above!")

    with tab3:
        logs = db.get_health_logs(uid, days=14)
        if len(logs) >= 2:
            df = pd.DataFrame(logs)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            fig = go.Figure()
            for col, name, color in [('energy_level', 'Energy', '#6366F1'), ('sleep_quality', 'Sleep', '#10B981'), ('mood', 'Mood', '#F59E0B')]:
                if col in df.columns:
                    fig.add_trace(go.Scatter(x=df['date'], y=df[col], name=name, line=dict(color=color, width=2),
                                             mode='lines+markers', marker=dict(size=6)))
            fig.update_layout(
                height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(range=[0, 11], gridcolor='#F3F4F6'),
                xaxis=dict(showgrid=False),
                legend=dict(orientation='h', y=-0.15),
                margin=dict(l=30, r=10, t=10, b=40)
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Log health data for at least 2 days to see trends.")


def finance_hub_page():
    page_header("💰 Finance Hub", "Budget management, bill tracking, and financial goals")
    uid = st.session_state.user_id

    tab1, tab2, tab3 = st.tabs(["📋 Bills", "🧮 Budget Planner", "📊 Analytics"])

    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            with st.expander("➕ Add Bill", expanded=False):
                b1, b2 = st.columns(2)
                with b1:
                    bill_name = st.text_input("Bill name", placeholder="Netflix, Rent, etc.", key="bill_name")
                    bill_amt = st.number_input("Amount ($)", 0.0, 100000.0, 100.0, step=10.0, key="bill_amt")
                with b2:
                    bill_due = st.number_input("Due day (1–31)", 1, 31, 15, key="bill_due")
                    bill_cat = st.selectbox("Category", ["Rent/Mortgage", "Utilities", "Insurance", "Subscriptions", "Loan", "Other"], key="bill_cat")
                if st.button("Add Bill", type="primary", key="add_bill"):
                    if bill_name.strip():
                        db.add_bill(uid, bill_name.strip(), bill_amt, bill_due, bill_cat)
                        st.session_state.bills = db.get_all_bills(uid)
                        st.success(f"Added {bill_name}")
                        st.rerun()
                    else:
                        st.warning("Enter bill name")

        with c2:
            bills = db.get_all_bills(uid)
            today_day = datetime.now().day
            if bills:
                total = sum(b['amount'] for b in bills)
                paid = sum(b['amount'] for b in bills if b['paid_this_month'])
                st.markdown(f"""
                <div class="metric-card" style="text-align:left; margin-bottom:16px; padding:16px 20px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div><div class="metric-label">TOTAL MONTHLY</div><div class="metric-value">${total:,.0f}</div></div>
                        <div><div class="metric-label">PAID</div><div class="metric-value" style="color:#10B981">${paid:,.0f}</div></div>
                        <div><div class="metric-label">REMAINING</div><div class="metric-value" style="color:#EF4444">${total-paid:,.0f}</div></div>
                    </div>
                </div>""", unsafe_allow_html=True)

                for bill in sorted(bills, key=lambda x: x['due_day']):
                    due_soon = abs(bill['due_day'] - today_day) <= 3
                    paid_flag = bool(bill.get('paid_this_month'))
                    col_a, col_b, col_c = st.columns([5, 1, 1])
                    with col_a:
                        status_icon = "✅" if paid_flag else ("⚠️" if due_soon else "⏰")
                        st.markdown(f"""<div class="list-item" style="{'border-left:3px solid #F59E0B' if due_soon and not paid_flag else 'border-left:3px solid #10B981' if paid_flag else ''}">
                            <div class="list-item-title">{status_icon} {bill['name']} — ${bill['amount']:,.0f}</div>
                            <div class="list-item-meta">Due: Day {bill['due_day']} · {bill['category']} {'· ⚠️ Due soon!' if due_soon and not paid_flag else '· ✅ Paid' if paid_flag else ''}</div>
                        </div>""", unsafe_allow_html=True)
                    with col_b:
                        if not paid_flag:
                            if st.button("✅", key=f"pay_{bill['id']}", help="Mark paid"):
                                db.mark_bill_paid(uid, bill['id'])
                                st.session_state.bills = db.get_all_bills(uid)
                                st.rerun()
                    with col_c:
                        if st.button("🗑", key=f"del_bill_{bill['id']}", help="Delete"):
                            db.delete_bill(uid, bill['id'])
                            st.session_state.bills = db.get_all_bills(uid)
                            st.rerun()
            else:
                st.info("No bills added. Add recurring bills to track them.")

    with tab2:
        st.markdown('<div class="section-header">🧮 Smart Budget Calculator</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            income = st.number_input("Monthly income ($)", 0, 500000, 3000, step=100, key="fp_income")
            savings_goal = st.slider("Savings goal (%)", 5, 50, 20, key="fp_savings_pct")
            st.markdown("<br>", unsafe_allow_html=True)

            needs_pct = 50
            wants_pct = 100 - savings_goal - needs_pct
            wants_pct = max(10, wants_pct)

            cats = {
                f"🏠 Needs ({needs_pct}%)": income * needs_pct / 100,
                f"🎉 Wants ({wants_pct}%)": income * wants_pct / 100,
                f"💰 Savings ({savings_goal}%)": income * savings_goal / 100,
            }
            for cat, amt in cats.items():
                r_col, v_col = st.columns([3, 1])
                with r_col:
                    st.progress(int(amt / income * 100) / 100 if income > 0 else 0, text=cat)
                with v_col:
                    st.write(f"**${amt:,.0f}**")
        with c2:
            st.markdown("**6-Month Savings Projection**")
            months = list(range(1, 7))
            monthly_save = income * savings_goal / 100
            cumulative = [monthly_save * m for m in months]
            fig = go.Figure(go.Bar(
                x=[f"Month {m}" for m in months], y=cumulative,
                marker_color='#6366F1', text=[f'${v:,.0f}' for v in cumulative],
                textposition='outside', textfont=dict(size=10)
            ))
            fig.update_layout(height=240, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               showlegend=False, yaxis=dict(showgrid=True, gridcolor='#F3F4F6'),
                               xaxis=dict(showgrid=False), margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with tab3:
        bills_for_chart = db.get_all_bills(uid)
        if bills_for_chart:
            cats_data = {}
            for b in bills_for_chart:
                cats_data[b['category']] = cats_data.get(b['category'], 0) + b['amount']
            fig = go.Figure(data=[go.Pie(
                labels=list(cats_data.keys()), values=list(cats_data.values()),
                hole=0.4, textinfo='label+percent',
                marker=dict(colors=['#6366F1', '#8B5CF6', '#A78BFA', '#C4B5FD', '#DDD6FE', '#F5F3FF'])
            )])
            fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)',
                               showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
            st.markdown('<div class="section-header">Bills by Category</div>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Add bills to see analytics.")


def study_center_page():
    page_header("📚 Study Center", "Focus sessions, study planning, and performance tracking")
    uid = st.session_state.user_id

    tab1, tab2, tab3 = st.tabs(["🍅 Focus Timer", "📊 Statistics", "📅 Sessions"])

    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            if not st.session_state.pomodoro_active:
                st.markdown('<div class="section-header">⚙️ Configure Session</div>', unsafe_allow_html=True)
                work_min = st.number_input("Work minutes", 5, 90, 25, key="p_work")
                break_min = st.number_input("Break minutes", 1, 30, 5, key="p_break")
                subject = st.text_input("Subject", placeholder="Mathematics, Physics…", key="p_subj")
                focus = st.slider("Focus level going in", 1, 10, 7, key="p_focus")
                if st.button("▶ Start Focus Session", type="primary", use_container_width=True, key="p_start"):
                    st.session_state.pomodoro_active = True
                    st.session_state.pomodoro_time = work_min * 60
                    st.session_state.break_time = break_min * 60
                    st.session_state.pomodoro_work = True
                    st.session_state.pomodoro_subject = subject or "General Study"
                    st.session_state.p_work_min = work_min
                    st.session_state.p_focus_level = focus
                    st.rerun()
            else:
                mins, secs = divmod(st.session_state.pomodoro_time, 60)
                phase = "FOCUS" if st.session_state.pomodoro_work else "BREAK"
                st.markdown(f"""
                <div class="timer-card">
                    <div class="timer-phase">{phase}</div>
                    <div class="timer-digits">{mins:02d}:{secs:02d}</div>
                    <div class="timer-subject">📚 {st.session_state.pomodoro_subject}</div>
                </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    if st.button("⏸ Pause", use_container_width=True, key="p_pause"):
                        st.session_state.pomodoro_active = False
                        st.rerun()
                with cc2:
                    if st.button("⏭ Skip", use_container_width=True, key="p_skip"):
                        if st.session_state.pomodoro_work:
                            st.session_state.pomodoro_time = st.session_state.break_time
                            st.session_state.pomodoro_work = False
                        else:
                            st.session_state.pomodoro_time = st.session_state.get('p_work_min', 25) * 60
                            st.session_state.pomodoro_work = True
                        st.rerun()
                with cc3:
                    if st.button("⏹ End", use_container_width=True, key="p_end"):
                        work_min = st.session_state.get('p_work_min', 25)
                        elapsed = work_min * 60 - st.session_state.pomodoro_time
                        duration = max(1, elapsed // 60)
                        if duration >= 1 and st.session_state.pomodoro_work:
                            db.add_study_session(uid, duration, st.session_state.pomodoro_subject,
                                                 st.session_state.get('p_focus_level', 7))
                            st.success(f"✅ Session saved: {duration} min")
                        st.session_state.pomodoro_active = False
                        st.rerun()

        with c2:
            st.markdown('<div class="section-header">💡 Study Tips</div>', unsafe_allow_html=True)
            tips = [
                ("🧠", "Active Recall", "Close your notes and write everything you remember. More effective than re-reading."),
                ("🔄", "Spaced Repetition", "Review day 1, day 3, day 7, day 21 for long-term retention."),
                ("✍️", "Feynman Technique", "Explain concepts like you're teaching a 10-year-old to find gaps."),
                ("🎯", "Interleaving", "Mix topics within sessions instead of blocked study for better transfer."),
                ("💤", "Sleep to Learn", "Memory consolidation happens during sleep — don't sacrifice it!"),
            ]
            for icon, title, desc in tips:
                st.markdown(f"""<div class="list-item">
                    <div class="list-item-title">{icon} {title}</div>
                    <div class="list-item-meta">{desc}</div>
                </div>""", unsafe_allow_html=True)

    with tab2:
        summary = db.get_weekly_study_summary(uid)
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("Weekly Hours", f"{summary['total_minutes']//60}h {summary['total_minutes']%60}m")
        with m2: st.metric("Sessions", summary['sessions'])
        with m3: st.metric("Avg Focus", f"{summary['avg_score']}/10")
        with m4: st.metric("Daily Avg", f"{summary['total_minutes']/7/60:.1f}h")

        sessions = summary.get("sessions_data", [])
        if sessions:
            df = pd.DataFrame(sessions)
            df['date'] = pd.to_datetime(df['date'])
            df = df.groupby('date').agg({'duration_minutes': 'sum', 'productivity_score': 'mean'}).reset_index()
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df['date'], y=df['duration_minutes'] / 60, name='Hours', marker_color='#818CF8'))
            fig.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               yaxis_title='Hours', xaxis=dict(showgrid=False),
                               yaxis=dict(gridcolor='#F3F4F6'), margin=dict(l=30, r=10, t=10, b=20))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Complete study sessions to see your weekly analytics.")

    with tab3:
        sessions_all = db.get_study_sessions(uid, limit=20)
        if sessions_all:
            for s in sessions_all:
                score_color = "#10B981" if s['productivity_score'] >= 7 else "#F59E0B" if s['productivity_score'] >= 4 else "#EF4444"
                st.markdown(f"""<div class="list-item">
                    <div class="list-item-title">📚 {s['subject']} — {s['duration_minutes']} min</div>
                    <div class="list-item-meta">📅 {s['date']} &nbsp;·&nbsp; <span style="color:{score_color}">⭐ {s['productivity_score']}/10 focus</span></div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No sessions yet. Start a Focus Timer session above!")


def productivity_page():
    page_header("⚡ Productivity Hub", "Task management, smart notes, and daily planning")
    uid = st.session_state.user_id

    tab1, tab2 = st.tabs(["✅ Tasks", "📝 Notes"])

    with tab1:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            with st.form("task_form", clear_on_submit=True):
                fc1, fc2, fc3 = st.columns([4, 2, 2])
                with fc1: new_task = st.text_input("Task description", placeholder="What needs to be done?", key="new_task_inp")
                with fc2: task_cat = st.selectbox("Category", ["Personal", "Health", "Finance", "Study", "Work"], key="task_cat")
                with fc3: task_pri = st.selectbox("Priority", ["high", "medium", "low"], key="task_pri")
                if st.form_submit_button("Add Task", type="primary", use_container_width=True):
                    if new_task.strip():
                        db.add_action_item(uid, new_task.strip(), task_cat, "User", task_pri)
                        st.session_state.todo_items = db.get_pending_actions(uid)
                        st.rerun()

            tasks = db.get_pending_actions(uid)
            if tasks:
                st.markdown(f'<div class="section-header">📋 Active Tasks ({len(tasks)})</div>', unsafe_allow_html=True)
                for task in tasks:
                    cat = task.get('category', 'Personal')
                    pri = task.get('priority', 'medium')
                    pri_colors = {"high": "#EF4444", "medium": "#F59E0B", "low": "#10B981"}
                    pri_color = pri_colors.get(pri, "#8B909A")
                    col_a, col_b, col_c = st.columns([6, 1, 1])
                    with col_a:
                        cat_badge = f'<span class="badge badge-{cat.lower()}">{cat}</span>'
                        pri_badge = f'<span class="badge badge-{pri}" style="color:{pri_color}">{pri.upper()}</span>'
                        created = task.get('created_at', '')[:10]
                        st.markdown(f"""<div class="list-item">
                            <div class="list-item-title">{task['task']}</div>
                            <div class="list-item-meta">{cat_badge} {pri_badge} &nbsp;·&nbsp; Added {created}</div>
                        </div>""", unsafe_allow_html=True)
                    with col_b:
                        if st.button("✅", key=f"done_{task['id']}", help="Complete"):
                            db.mark_action_complete(uid, task['id'])
                            st.session_state.todo_items = db.get_pending_actions(uid)
                            st.rerun()
                    with col_c:
                        if st.button("🗑", key=f"del_{task['id']}", help="Delete"):
                            db.delete_action(uid, task['id'])
                            st.session_state.todo_items = db.get_pending_actions(uid)
                            st.rerun()
            else:
                st.info("🎉 All caught up! Add your first task above.")

        with c2:
            st.markdown('<div class="section-header">📊 Task Stats</div>', unsafe_allow_html=True)
            try:
                stats = db.get_user_statistics(uid)
                total, completed = stats['total_actions'], stats['completed_actions']
                rate = stats['completion_rate']
                st.progress(rate / 100, text=f"Completion rate: {rate:.0f}%")
                st.markdown("<br>", unsafe_allow_html=True)
                sc1, sc2 = st.columns(2)
                with sc1: st.metric("Total", total)
                with sc2: st.metric("Done", completed)
            except Exception:
                st.info("No task stats yet.")

    with tab2:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown('<div class="section-header">✍️ New Note</div>', unsafe_allow_html=True)
            with st.form("note_form", clear_on_submit=True):
                note_title = st.text_input("Title", placeholder="Note title…", key="nt_title")
                note_content = st.text_area("Content", height=180, placeholder="Write your thoughts…", key="nt_content")
                note_tags = st.text_input("Tags (comma-separated)", placeholder="work, ideas, health", key="nt_tags")
                if st.form_submit_button("Save Note", type="primary", use_container_width=True):
                    if note_title.strip() and note_content.strip():
                        db.add_note(uid, note_title.strip(), note_content.strip(), note_tags)
                        st.session_state.notes = db.get_notes(uid)
                        st.rerun()
                    else:
                        st.warning("Title and content required")

        with c2:
            st.markdown('<div class="section-header">📓 Saved Notes</div>', unsafe_allow_html=True)
            notes = db.get_notes(uid)
            if notes:
                for note in notes[:10]:
                    col_n, col_d = st.columns([5, 1])
                    with col_n:
                        with st.expander(f"{'📌 ' if note.get('pinned') else '📄 '}{note['title']}", expanded=False):
                            st.write(note['content'])
                            if note.get('tags'):
                                st.caption(f"🏷️ {note['tags']}")
                            st.caption(f"📅 {note['updated_at'][:10]}")
                    with col_d:
                        if st.button("🗑", key=f"del_note_{note['id']}", help="Delete"):
                            db.delete_note(uid, note['id'])
                            st.session_state.notes = db.get_notes(uid)
                            st.rerun()
            else:
                st.info("No notes yet. Create your first note!")


def profile_page():
    page_header("👤 Profile & Settings", "Manage account, preferences, and view your stats")
    uid = st.session_state.user_id
    user = st.session_state.user_data or {}

    tab1, tab2, tab3 = st.tabs(["👤 Account", "⚙️ Settings", "📊 Analytics"])

    with tab1:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"""
            <div class="card" style="text-align:center; padding:28px 20px;">
                <div class="profile-avatar-lg">👤</div>
                <div style="font-size:20px; font-weight:700; color:#1A1D23; letter-spacing:-0.3px;">{user.get('name', 'User')}</div>
                <div style="font-size:13px; color:#8B909A; margin-top:4px;">{user.get('email', '')}</div>
                <div style="margin-top:16px; padding:8px 16px; background:#EEF2FF; border-radius:20px; display:inline-block;">
                    <span style="font-size:12px; font-weight:600; color:#4F46E5;">✨ Free Account</span>
                </div>
                <div style="font-size:11px; color:#8B909A; margin-top:10px;">Member since {user.get('joined_at', '')[:10]}</div>
            </div>""", unsafe_allow_html=True)

        with c2:
            try:
                stats = db.get_user_statistics(uid)
                streak = db.get_consistency_streak(uid)
                analyses = db.get_recent_analyses(uid, limit=3)
            except Exception:
                stats = {"total_actions": 0, "completed_actions": 0, "medicines_count": 0,
                         "bills_count": 0, "notes_count": 0, "study_sessions": 0,
                         "ai_analyses": 0, "completion_rate": 0}
                streak, analyses = 0, []

            st.markdown('<div class="section-header">📊 Your Stats</div>', unsafe_allow_html=True)
            g1, g2, g3 = st.columns(3)
            metrics = [
                (g1, "Total Tasks", stats['total_actions'], "✅ Completed", stats['completed_actions']),
                (g2, "Day Streak", streak, "🔥 Keep going!", ""),
                (g3, "Completion", f"{stats['completion_rate']:.0f}%", "📊 Rate", ""),
            ]
            for col, lbl, val, sub_lbl, sub_val in metrics:
                with col:
                    st.metric(lbl, val, sub_val if sub_val != "" else None)

            st.markdown("<br>", unsafe_allow_html=True)
            g4, g5, g6 = st.columns(3)
            with g4: st.metric("Medicines", stats['medicines_count'])
            with g5: st.metric("Bills", stats['bills_count'])
            with g6: st.metric("Notes", stats['notes_count'])

            if analyses:
                st.markdown('<div class="section-header" style="margin-top:20px;">🤖 Recent Analyses</div>', unsafe_allow_html=True)
                for a in analyses:
                    st.markdown(f"""<div class="list-item">
                        <div class="list-item-meta">📅 {a['created_at'][:16].replace('T',' ')} &nbsp;·&nbsp; Score: {a.get('score', '—')}/100</div>
                    </div>""", unsafe_allow_html=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-header">👤 Edit Profile</div>', unsafe_allow_html=True)
            with st.form("profile_form"):
                new_name = st.text_input("Display name", value=user.get('name', ''), key="pf_name")
                st.text_input("Email (cannot change)", value=user.get('email', ''), disabled=True, key="pf_email")
                if st.form_submit_button("Update Profile", type="primary"):
                    if new_name.strip():
                        db.update_user_settings(uid, {'name': new_name.strip()})
                        st.session_state.user_data['name'] = new_name.strip()
                        st.success("Profile updated!")
                    else:
                        st.warning("Name cannot be empty")

            st.markdown('<div class="section-header" style="margin-top:20px;">🔐 Change Password</div>', unsafe_allow_html=True)
            with st.form("password_form"):
                old_pass = st.text_input("Current password", type="password", key="pf_old")
                new_pass = st.text_input("New password", type="password", key="pf_new")
                confirm_pass = st.text_input("Confirm new password", type="password", key="pf_conf")
                if st.form_submit_button("Change Password", type="primary"):
                    if not all([old_pass, new_pass, confirm_pass]):
                        st.error("Fill all fields")
                    elif new_pass != confirm_pass:
                        st.error("Passwords don't match")
                    elif len(new_pass) < 6:
                        st.error("Min 6 characters")
                    elif db.change_password(uid, old_pass, new_pass):
                        st.success("✅ Password changed successfully!")
                    else:
                        st.error("Current password incorrect")

        with c2:
            st.markdown('<div class="section-header">🔔 Notifications</div>', unsafe_allow_html=True)
            with st.form("notif_form"):
                n_email = st.toggle("Email notifications", value=bool(user.get('notifications_email', 1)), key="n_email")
                n_push = st.toggle("Push reminders", value=bool(user.get('notifications_push', 1)), key="n_push")
                n_weekly = st.toggle("Weekly progress reports", value=bool(user.get('notifications_weekly', 1)), key="n_weekly")
                if st.form_submit_button("Save Notifications", type="primary"):
                    db.update_user_settings(uid, {
                        'notifications_email': int(n_email),
                        'notifications_push': int(n_push),
                        'notifications_weekly': int(n_weekly)
                    })
                    st.success("Saved!")

            st.markdown('<div class="section-header" style="margin-top:20px;">🎨 Appearance</div>', unsafe_allow_html=True)
            with st.form("theme_form"):
                font_size = st.select_slider("Font size", ["Small", "Medium", "Large"],
                                             value=user.get('font_size', 'Medium'), key="pf_font")
                if st.form_submit_button("Apply", type="primary"):
                    db.update_user_settings(uid, {'font_size': font_size})
                    st.session_state.user_data['font_size'] = font_size
                    st.success("Applied!")

            st.markdown('<div class="section-header" style="margin-top:20px;">🗑️ Account Actions</div>', unsafe_allow_html=True)
            if st.button("🚪 Sign Out", use_container_width=True):
                logout()

    with tab3:
        try:
            stats = db.get_user_statistics(uid)
            completion = stats['completion_rate']
            st.markdown('<div class="section-header">📈 Activity Overview</div>', unsafe_allow_html=True)

            domains = ['Tasks', 'Health', 'Finance', 'Study', 'Notes']
            values = [
                min(100, stats['total_actions'] * 5),
                min(100, len(db.get_health_logs(uid)) * 10),
                min(100, stats['bills_count'] * 15),
                min(100, stats['study_sessions'] * 8),
                min(100, stats['notes_count'] * 10)
            ]
            fig = go.Figure(go.Bar(
                x=domains, y=values, marker_color=['#6366F1', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899'],
                text=[f'{v}%' for v in values], textposition='outside', textfont=dict(size=11)
            ))
            fig.update_layout(
                height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(range=[0, 115], showgrid=True, gridcolor='#F3F4F6'),
                xaxis=dict(showgrid=False), margin=dict(l=10, r=10, t=20, b=10),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        except Exception as e:
            st.info("Complete more activities to see analytics here!")


def run_ai_analysis(user_inputs: dict):
    api_key = get_api_key()
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    else:
        st.warning("⚠️ No API key found. Using smart offline analysis.")

    with st.spinner("🧠 Analyzing your life with AI…"):
        try:
            crew = LifeOpsCrew(user_inputs)
            results = crew.kickoff()
            st.session_state.analysis_results = results
            if st.session_state.user_id:
                db.save_ai_analysis(st.session_state.user_id, results)
                db._record_checkin(st.session_state.user_id)
            st.success("✅ Analysis complete!")
            st.balloons()
        except Exception as e:
            st.error(f"Analysis failed: {str(e)[:200]}")


def main():
    init_state()
    inject_css()

    if not st.session_state.authenticated:
        login_page()
        return

    render_topnav()

    page = st.session_state.current_page
    if page == "Dashboard":
        dashboard_page()
    elif page == "Health Vault":
        health_vault_page()
    elif page == "Finance Hub":
        finance_hub_page()
    elif page == "Study Center":
        study_center_page()
    elif page == "Productivity":
        productivity_page()
    elif page == "Profile":
        profile_page()
    else:
        dashboard_page()


if __name__ == "__main__":
    main()
