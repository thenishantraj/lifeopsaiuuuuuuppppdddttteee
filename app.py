import streamlit as st
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ── Local imports ────────────────────────────────────────────────────────────
from database import LifeOpsDatabase
from crew_setup import LifeOpsCrew
from utils import send_otp_email, generate_otp

# ── Disable OpenAI globally (we use Gemini) ──────────────────────────────────
os.environ["OPENAI_API_KEY"] = "not-required"
os.environ["OPENAI_API_BASE"] = ""
os.environ["OPENAI_MODEL_NAME"] = ""

# ── App config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LifeOps AI — Life Management Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

db = LifeOpsDatabase()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_api_key():
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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #F7F8FC !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #1A1D23 !important;
}

#MainMenu, footer, header,
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
}

[data-testid="stMainBlockContainer"], .block-container {
    padding: 88px 28px 40px 28px !important;
    max-width: 1320px !important;
}

/* ── TOP NAV ─────────────────────────────────────────────────── */
.topnav {
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
    height: 62px;
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid #E8EBF3;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 28px; gap: 16px;
}
.topnav-brand {
    font-size: 18px; font-weight: 700; color: #1A1D23;
    display: flex; align-items: center; gap: 8px; white-space: nowrap;
    letter-spacing: -0.3px;
}
.brand-dot { color: #6366F1; }
.user-chip {
    background: #F0F0FF; border-radius: 20px; padding: 5px 12px;
    font-size: 13px; font-weight: 500; color: #4F46E5;
}
.streak-chip {
    background: #FFF7ED; border-radius: 20px; padding: 5px 12px;
    font-size: 13px; font-weight: 600; color: #D97706;
}

/* ── NAV BUTTONS ─────────────────────────────────────────────── */
.topnav-pages div[data-testid="stButton"] > button,
.topnav-right div[data-testid="stButton"] > button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important; font-weight: 500 !important;
    padding: 6px 14px !important; border-radius: 8px !important;
    border: none !important; background: transparent !important;
    color: #5B6170 !important; white-space: nowrap !important;
    line-height: 1.4 !important; height: auto !important;
    min-height: 32px !important; transition: all 0.15s ease !important;
}
.topnav-pages div[data-testid="stButton"] > button:hover {
    background: #F0F1F9 !important; color: #1A1D23 !important;
}

/* ── PAGE HEADER ─────────────────────────────────────────────── */
.page-header { margin-bottom: 28px; }
.page-title { font-size: 26px; font-weight: 700; color: #1A1D23; letter-spacing: -0.5px; }
.page-sub { font-size: 14px; color: #8B909A; margin-top: 4px; }

/* ── CARDS ───────────────────────────────────────────────────── */
.metric-card {
    background: #fff; border-radius: 14px; padding: 20px;
    border: 1px solid #EAECF0; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    text-align: center; transition: all 0.2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
.metric-icon { font-size: 28px; margin-bottom: 8px; }
.metric-value { font-size: 28px; font-weight: 700; color: #1A1D23; letter-spacing: -0.5px; }
.metric-label { font-size: 11px; font-weight: 500; color: #8B909A; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 4px; }
.card { background:#fff; border-radius:14px; padding:20px 22px; border:1px solid #EAECF0; box-shadow:0 1px 4px rgba(0,0,0,0.04); margin-bottom:16px; }

/* ── LIST ITEMS ──────────────────────────────────────────────── */
.list-item {
    background: #FAFBFD; border: 1px solid #EAECF0;
    border-radius: 10px; padding: 12px 16px; margin-bottom: 8px; transition: all 0.15s;
}
.list-item:hover { background: #F5F5FF; border-color: #C7C7F5; }
.list-item-title { font-weight: 600; font-size: 14px; color: #1A1D23; }
.list-item-meta { font-size: 12px; color: #8B909A; margin-top: 3px; }

/* ── SECTION HEADER ──────────────────────────────────────────── */
.section-header {
    font-size: 16px; font-weight: 600; color: #1A1D23;
    letter-spacing: -0.2px; margin-bottom: 14px; margin-top: 8px;
}

/* ── BADGES ──────────────────────────────────────────────────── */
.badge { display:inline-block; padding:2px 9px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-health   { background:#DCFCE7; color:#166534; }
.badge-finance  { background:#FEF9C3; color:#854D0E; }
.badge-study    { background:#EEF2FF; color:#3730A3; }
.badge-personal { background:#F3E8FF; color:#6B21A8; }
.badge-work     { background:#FEE2E2; color:#991B1B; }
.badge-high     { background:#FFF1F2; color:#BE123C; }
.badge-medium   { background:#FFF7ED; color:#C2410C; }
.badge-low      { background:#F0FDF4; color:#166534; }

/* ── TIMER ───────────────────────────────────────────────────── */
.timer-card {
    background: linear-gradient(135deg,#667EEA,#764BA2);
    border-radius: 18px; padding: 32px 24px; text-align: center;
    color: white; box-shadow: 0 8px 32px rgba(99,102,241,0.3);
}
.timer-phase {
    display:inline-block; padding:4px 16px; border-radius:20px;
    background:rgba(255,255,255,0.2); font-size:12px; font-weight:700;
    letter-spacing:1.5px; text-transform:uppercase; margin-bottom:16px;
}
.timer-digits {
    font-family:'DM Mono',monospace; font-size:64px; font-weight:500;
    letter-spacing:-2px; line-height:1; margin-bottom:8px;
}
.timer-subject { font-size:15px; opacity:0.85; }

/* ── PROFILE ─────────────────────────────────────────────────── */
.profile-avatar-lg {
    width:80px; height:80px; border-radius:50%;
    background:linear-gradient(135deg,#667EEA,#764BA2);
    display:flex; align-items:center; justify-content:center;
    font-size:32px; margin:0 auto 12px auto;
    box-shadow:0 4px 16px rgba(99,102,241,0.3);
}

/* ── REPORT CARD ─────────────────────────────────────────────── */
.report-card { background:#fff; border-radius:14px; padding:24px; border:1px solid #EAECF0; margin-bottom:16px; }
.insight-card { background:linear-gradient(135deg,#EEF2FF,#F5F3FF); border:1px solid #C7D2FE; border-radius:12px; padding:16px 18px; margin-bottom:10px; }

/* ── PROGRESS ────────────────────────────────────────────────── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg,#6366F1,#8B5CF6) !important;
    border-radius: 4px !important;
}

/* ── INPUTS ──────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    border-radius:8px !important; border:1px solid #E2E5EF !important;
    font-family:'DM Sans',sans-serif !important; font-size:14px !important;
    background:#fff !important; color:#1A1D23 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color:#6366F1 !important;
    box-shadow:0 0 0 3px rgba(99,102,241,0.12) !important;
}
.stSelectbox > div > div { border-radius:8px !important; border:1px solid #E2E5EF !important; }

/* ── BUTTONS ─────────────────────────────────────────────────── */
.stButton > button {
    font-family:'DM Sans',sans-serif !important; font-weight:500 !important;
    border-radius:9px !important; font-size:14px !important;
    border:1px solid #E2E5EF !important; background:#fff !important;
    color:#374151 !important; transition:all 0.15s ease !important;
}
.stButton > button:hover { background:#F7F8FC !important; border-color:#C7C7F5 !important; color:#4F46E5 !important; }
.stButton > button[kind="primary"] {
    background:linear-gradient(135deg,#6366F1,#8B5CF6) !important;
    color:white !important; border:none !important; font-weight:600 !important;
    box-shadow:0 2px 8px rgba(99,102,241,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    transform:translateY(-1px) !important;
    box-shadow:0 4px 16px rgba(99,102,241,0.45) !important; color:white !important;
}

/* ── TABS ────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background:#F7F8FC !important; border-radius:10px !important;
    padding:3px !important; gap:2px !important; border:none !important;
}
.stTabs [data-baseweb="tab"] {
    background:transparent !important; border-radius:8px !important;
    color:#8B909A !important; font-weight:500 !important; font-size:13px !important;
    padding:6px 14px !important; border:none !important;
}
.stTabs [aria-selected="true"] {
    background:white !important; color:#4F46E5 !important;
    font-weight:600 !important; box-shadow:0 1px 4px rgba(0,0,0,0.08) !important;
}

/* ── SCROLLBAR ───────────────────────────────────────────────── */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:#D1D5DB; border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:#9CA3AF; }

/* ── RESPONSIVE ──────────────────────────────────────────────── */
@media (max-width: 768px) {
    [data-testid="stMainBlockContainer"], .block-container { padding:72px 12px 24px 12px !important; }
    .topnav { padding:0 12px; }
    .metric-value { font-size:22px; }
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "authenticated": False,
        "user_id": None,
        "user_data": None,
        "current_page": "Dashboard",
        "analysis_results": None,
        "user_inputs": {},
        "processing": False,
        "pomodoro_active": False,
        "pomodoro_time": 25 * 60,
        "pomodoro_work": True,
        "pomodoro_subject": "",
        "break_time": 5 * 60,
        "todo_items": [],
        "medicines": [],
        "bills": [],
        "notes": [],
        # OTP signup flow
        "otp_pending": False,
        "otp_code": "",
        "otp_email": "",
        "otp_name": "",
        "otp_pass": "",
        "otp_ts": None,
        "otp_attempts": 0,
        # Forgot password flow
        "fp_step": 0,          # 0=off 1=enter-email 2=otp-sent 3=new-password
        "fp_email": "",
        "fp_otp_code": "",
        "fp_otp_ts": None,
        "fp_otp_attempts": 0,
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


# ─────────────────────────────────────────────────────────────────────────────
# TOP NAVIGATION
# ─────────────────────────────────────────────────────────────────────────────

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
            unsafe_allow_html=True,
        )

    with center:
        st.markdown('<div class="topnav-pages">', unsafe_allow_html=True)
        cols = st.columns(len(pages))
        for i, (icon, page) in enumerate(pages):
            with cols[i]:
                btn_type = "primary" if cur == page else "secondary"
                if st.button(icon + " " + page, key="nav_" + page,
                              use_container_width=True, type=btn_type):
                    st.session_state.current_page = page
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        c1, c2 = st.columns([2, 1])
        with c1:
            if streak > 0:
                st.markdown(
                    '<div class="streak-chip">🔥 ' + str(streak) + 'd</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="user-chip">👋 ' + name + '</div>',
                    unsafe_allow_html=True,
                )
        with c2:
            if st.button("↩", key="nav_logout", help="Logout"):
                logout()

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — LOGIN PAGE
# ─────────────────────────────────────────────────────────────────────────────

def _render_signup_form():
    """Step 1: Collect info, validate, send OTP."""
    with st.form("signup_form", clear_on_submit=False):
        s_name  = st.text_input("Full name",        placeholder="Alex Kumar",       key="sf_name")
        s_email = st.text_input("Email address",    placeholder="you@example.com",  key="sf_email")
        s_pass  = st.text_input("Password",         type="password",
                                placeholder="Min 6 characters",                     key="sf_pass")
        s_pass2 = st.text_input("Confirm password", type="password",
                                placeholder="Repeat password",                      key="sf_pass2")
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "Send Verification Code →", type="primary", use_container_width=True
        )

    if not submitted:
        return

    # ── Validation ────────────────────────────────────────────────────────────
    if not all([s_name, s_email, s_pass, s_pass2]):
        st.error("Please fill in all fields.")
        return
    if len(s_pass) < 6:
        st.error("Password must be at least 6 characters.")
        return
    if s_pass != s_pass2:
        st.error("Passwords do not match.")
        return

    # ── Email uniqueness check ────────────────────────────────────────────────
    email_clean = s_email.lower().strip()
    if db.email_exists(email_clean):
        existing = db.authenticate_user(email_clean, s_pass)
        if existing not in (None, "unverified"):
            st.error("This email is already registered. Please sign in.")
            return
        if existing is None:
            # email exists but wrong password — already taken by someone else
            st.error("This email is already registered. Please sign in.")
            return
        # existing == "unverified" → allow resend

    # ── Send OTP ──────────────────────────────────────────────────────────────
    with st.spinner("Sending verification code to your email…"):
        success, otp_code, msg = send_otp_email(email_clean)

    if not success:
        st.error("Could not send OTP: " + msg)
        st.info("Tip: Configure SENDER_EMAIL and APP_PASSWORD in .streamlit/secrets.toml")
        return

    # ── Save pending state ────────────────────────────────────────────────────
    st.session_state.otp_pending  = True
    st.session_state.otp_code     = otp_code
    st.session_state.otp_email    = email_clean
    st.session_state.otp_name     = s_name.strip()
    st.session_state.otp_pass     = s_pass
    st.session_state.otp_ts       = datetime.now()
    st.session_state.otp_attempts = 0

    db.create_user_unverified(email_clean, s_pass, s_name.strip())
    st.rerun()


def _render_otp_verify_ui():
    """Step 2: Verify OTP and activate account."""
    email = st.session_state.otp_email

    st.markdown(
        '<div style="background:#EEF2FF;border:1px solid #C7D2FE;border-radius:12px;'
        'padding:18px 20px;margin-bottom:20px;">'
        '<div style="font-size:15px;font-weight:700;color:#4338CA;margin-bottom:4px;">'
        "✉️ Verification Code Sent</div>"
        '<div style="font-size:13px;color:#64748B;">'
        "A 6-digit code was sent to <strong>" + email + "</strong>.<br/>"
        "Enter it below within <strong>10 minutes</strong>.</div></div>",
        unsafe_allow_html=True,
    )

    # ── Expiry check (10 minutes) ─────────────────────────────────────────────
    otp_ts = st.session_state.get("otp_ts")
    if otp_ts and (datetime.now() - otp_ts).total_seconds() > 600:
        st.warning("⏱️ OTP expired. Please register again.")
        db.delete_unverified_user(email)
        st.session_state.otp_pending  = False
        st.session_state.otp_code     = ""
        st.session_state.otp_attempts = 0
        st.rerun()
        return

    otp_input = st.text_input(
        "Enter 6-digit code", placeholder="e.g. 482910",
        max_chars=6, key="otp_input_field"
    )

    col_v, col_r, col_b = st.columns([2, 1, 1])

    with col_v:
        if st.button("✅ Verify & Create Account", type="primary",
                     use_container_width=True, key="btn_verify_otp"):
            if not otp_input.strip():
                st.error("Please enter the OTP.")
            elif st.session_state.otp_attempts >= 5:
                st.error("Too many incorrect attempts. Please register again.")
                db.delete_unverified_user(email)
                st.session_state.otp_pending = False
                st.rerun()
            elif otp_input.strip() == st.session_state.otp_code:
                if db.verify_user_email(email):
                    st.success("🎉 Email verified! Your account is ready. Please sign in.")
                    st.session_state.otp_pending  = False
                    st.session_state.otp_code     = ""
                    st.session_state.otp_attempts = 0
                    st.rerun()
                else:
                    st.error("Activation failed. Please try registering again.")
            else:
                st.session_state.otp_attempts += 1
                remaining = 5 - st.session_state.otp_attempts
                st.error("Incorrect OTP. " + str(remaining) + " attempt(s) remaining.")

    with col_r:
        if st.button("🔄 Resend", use_container_width=True, key="btn_resend_otp"):
            with st.spinner("Resending…"):
                success, new_otp, msg = send_otp_email(email)
            if success:
                st.session_state.otp_code     = new_otp
                st.session_state.otp_ts       = datetime.now()
                st.session_state.otp_attempts = 0
                st.success("New code sent!")
            else:
                st.error("Resend failed: " + msg)

    with col_b:
        if st.button("← Back", use_container_width=True, key="btn_back_signup"):
            db.delete_unverified_user(email)
            st.session_state.otp_pending = False
            st.rerun()



def _render_forgot_password():
    """3-step forgot password: enter email → verify OTP → set new password."""
    step = st.session_state.fp_step

    # Step 1 ── ask for email
    if step == 1:
        st.markdown(
            '''<div style="background:#EEF2FF;border:1px solid #C7D2FE;
            border-radius:12px;padding:16px 20px;margin-bottom:16px;">
            <div style="font-size:15px;font-weight:700;color:#4338CA;margin-bottom:4px;">
            🔑 Reset Your Password</div>
            <div style="font-size:13px;color:#64748B;">
            Enter the email address you used to register. We will send a verification code.</div>
            </div>''',
            unsafe_allow_html=True,
        )
        with st.form("fp_email_form"):
            fp_email = st.text_input("Registered email", placeholder="you@example.com",
                                     key="fp_email_input")
            sub = st.form_submit_button("Send Reset Code →", type="primary",
                                        use_container_width=True)
        if sub:
            if not fp_email.strip():
                st.error("Please enter your email.")
            elif not db.email_exists(fp_email.strip()):
                st.error("No account found with this email address.")
            else:
                # Check it is a verified account
                fp_email_clean = fp_email.strip().lower()
                conn_check = None
                if not db.is_email_verified(fp_email_clean):
                    st.error("This account is not verified yet. "
                             "Please complete registration first.")
                    return
                with st.spinner("Sending reset code…"):
                    success, otp_code, msg = send_otp_email(fp_email_clean)
                if not success:
                    st.error("Could not send code: " + msg)
                    return
                st.session_state.fp_email       = fp_email_clean
                st.session_state.fp_otp_code    = otp_code
                st.session_state.fp_otp_ts      = datetime.now()
                st.session_state.fp_otp_attempts = 0
                st.session_state.fp_step        = 2
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Sign In", key="fp_back_1"):
            st.session_state.fp_step = 0
            st.rerun()

    # Step 2 ── verify OTP
    elif step == 2:
        fp_email = st.session_state.fp_email
        st.markdown(
            '''<div style="background:#EEF2FF;border:1px solid #C7D2FE;
            border-radius:12px;padding:16px 20px;margin-bottom:16px;">
            <div style="font-size:15px;font-weight:700;color:#4338CA;margin-bottom:4px;">
            ✉️ Enter Verification Code</div>
            <div style="font-size:13px;color:#64748B;">
            A 6-digit code was sent to <strong>''' + fp_email + '''</strong>.<br/>
            Valid for <strong>10 minutes</strong>.</div></div>''',
            unsafe_allow_html=True,
        )
        # Expiry check
        otp_ts = st.session_state.get("fp_otp_ts")
        if otp_ts and (datetime.now() - otp_ts).total_seconds() > 600:
            st.warning("⏱️ Code expired. Please request a new one.")
            st.session_state.fp_step = 1
            st.rerun()
            return

        otp_in = st.text_input("6-digit code", placeholder="e.g. 847291",
                                max_chars=6, key="fp_otp_input")
        cv, cr, cb = st.columns([2, 1, 1])
        with cv:
            if st.button("✅ Verify Code", type="primary",
                         use_container_width=True, key="fp_verify_btn"):
                if not otp_in.strip():
                    st.error("Please enter the code.")
                elif st.session_state.fp_otp_attempts >= 5:
                    st.error("Too many wrong attempts. Please start over.")
                    st.session_state.fp_step = 1
                    st.rerun()
                elif otp_in.strip() == st.session_state.fp_otp_code:
                    st.session_state.fp_step = 3
                    st.rerun()
                else:
                    st.session_state.fp_otp_attempts += 1
                    remaining = 5 - st.session_state.fp_otp_attempts
                    st.error("Wrong code. " + str(remaining) + " attempt(s) left.")
        with cr:
            if st.button("🔄 Resend", use_container_width=True, key="fp_resend"):
                with st.spinner("Resending…"):
                    ok, new_code, err = send_otp_email(fp_email)
                if ok:
                    st.session_state.fp_otp_code     = new_code
                    st.session_state.fp_otp_ts       = datetime.now()
                    st.session_state.fp_otp_attempts = 0
                    st.success("New code sent!")
                else:
                    st.error("Failed: " + err)
        with cb:
            if st.button("← Back", use_container_width=True, key="fp_back_2"):
                st.session_state.fp_step = 1
                st.rerun()

    # Step 3 ── set new password
    elif step == 3:
        fp_email = st.session_state.fp_email
        st.markdown(
            '''<div style="background:#DCFCE7;border:1px solid #BBF7D0;
            border-radius:12px;padding:16px 20px;margin-bottom:16px;">
            <div style="font-size:15px;font-weight:700;color:#166534;margin-bottom:4px;">
            ✅ Identity Verified</div>
            <div style="font-size:13px;color:#166534;">
            Set a new password for <strong>''' + fp_email + '''</strong></div>
            </div>''',
            unsafe_allow_html=True,
        )
        with st.form("fp_newpass_form"):
            new_p  = st.text_input("New password", type="password",
                                   placeholder="Min 6 characters", key="fp_new_pass")
            new_p2 = st.text_input("Confirm new password", type="password",
                                   placeholder="Repeat password", key="fp_confirm_pass")
            sub = st.form_submit_button("Update Password →", type="primary",
                                        use_container_width=True)
        if sub:
            if not new_p or not new_p2:
                st.error("Please fill both fields.")
            elif len(new_p) < 6:
                st.error("Password must be at least 6 characters.")
            elif new_p != new_p2:
                st.error("Passwords do not match.")
            else:
                if db.reset_password_by_email(fp_email, new_p):
                    st.success("🎉 Password updated successfully! Please sign in.")
                    # Clear all fp state
                    st.session_state.fp_step         = 0
                    st.session_state.fp_email        = ""
                    st.session_state.fp_otp_code     = ""
                    st.session_state.fp_otp_ts       = None
                    st.session_state.fp_otp_attempts = 0
                    st.rerun()
                else:
                    st.error("Failed to update password. Please try again.")


def login_page():
    st.markdown("""
<style>
[data-testid="stMainBlockContainer"], .block-container {
    padding: 20px !important; max-width: 100% !important;
}
</style>""", unsafe_allow_html=True)

    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding:40px 0 20px;">
            <div style="font-size:52px; margin-bottom:12px;">🧠</div>
            <div style="font-size:26px; font-weight:700; color:#1A1D23; letter-spacing:-0.5px;">LifeOps AI</div>
            <div style="font-size:14px; color:#8B909A; margin-top:6px; margin-bottom:32px;">Your intelligent life management platform</div>
        </div>""", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["  Sign In  ", "  Create Account  "])

        with tab1:
            # ── Forgot password flow takes over tab1 when active ──────────────
            if st.session_state.fp_step > 0:
                _render_forgot_password()
            else:
                with st.form("login_form", clear_on_submit=False):
                    email    = st.text_input("Email address", placeholder="you@example.com")
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    st.markdown("<br>", unsafe_allow_html=True)
                    submitted = st.form_submit_button(
                        "Sign in to LifeOps →", type="primary", use_container_width=True
                    )
                if submitted:
                    if not email or not password:
                        st.error("Please fill in all fields.")
                    else:
                        result = db.authenticate_user(email, password)
                        if result == "unverified":
                            st.warning(
                                "⚠️ Your email is not verified yet. "
                                "Please complete OTP verification in the Create Account tab."
                            )
                        elif result:
                            st.session_state.authenticated = True
                            st.session_state.user_id       = result["id"]
                            st.session_state.user_data     = result
                            st.session_state.current_page  = "Dashboard"
                            api_k = get_api_key()
                            if api_k:
                                os.environ["GOOGLE_API_KEY"] = api_k
                            load_user_data()
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please try again.")

                # Forgot password link
                st.markdown("<br>", unsafe_allow_html=True)
                col_fp, _ = st.columns([1, 2])
                with col_fp:
                    if st.button("🔑 Forgot Password?", key="open_fp",
                                 use_container_width=True):
                        st.session_state.fp_step = 1
                        st.rerun()

        with tab2:
            if st.session_state.otp_pending:
                _render_otp_verify_ui()
            else:
                _render_signup_form()

        st.markdown("""
        <div style="text-align:center;margin-top:32px;padding:16px;background:#F7F8FC;border-radius:12px;">
            <div style="font-size:13px;font-weight:600;color:#1A1D23;margin-bottom:8px;">✨ What's included</div>
            <div style="font-size:12px;color:#8B909A;line-height:2;">
                🤖 AI Life Analysis &nbsp;·&nbsp; 💊 Health Vault &nbsp;·&nbsp; 💰 Finance Hub<br>
                📚 Study Optimizer &nbsp;·&nbsp; ⚡ Task Manager &nbsp;·&nbsp; 📝 Smart Notes
            </div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED WIDGETS
# ─────────────────────────────────────────────────────────────────────────────

def page_header(title, subtitle):
    st.markdown(
        '<div class="page-header">'
        '<div class="page-title">' + title + "</div>"
        '<div class="page-sub">' + subtitle + "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def create_health_chart(stress, sleep):
    cats = ["Stress Mgmt", "Sleep", "Hydration", "Exercise", "Nutrition"]
    vals = [max(0, 10 - stress) * 10, min(100, (sleep / 8) * 100), 70, 50, 65]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], theta=cats + [cats[0]], fill="toself",
        line_color="#6366F1", fillcolor="rgba(99,102,241,0.15)", line_width=2
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9)),
            angularaxis=dict(tickfont=dict(size=11, color="#4B5563")),
            bgcolor="white",
        ),
        showlegend=False, height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=20, b=20),
    )
    return fig


def create_finance_chart(budget, expenses):
    savings = max(0, budget - expenses)
    rate = int(savings / budget * 100) if budget > 0 else 0
    fig = go.Figure(data=[go.Pie(
        labels=["Expenses", "Savings"], values=[expenses, savings], hole=0.65,
        marker=dict(colors=["#F87171", "#34D399"], line=dict(color="white", width=2)),
        textinfo="none",
    )])
    fig.add_annotation(
        text=str(rate) + "%<br><span style='font-size:10px'>saved</span>",
        x=0.5, y=0.5, font=dict(size=20, color="#1A1D23"), showarrow=False
    )
    fig.update_layout(
        showlegend=True, height=250, paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        margin=dict(l=10, r=10, t=10, b=30),
    )
    return fig


def create_study_chart(days, hours):
    if days <= 0:
        days = 7
    days_to_show = min(days, 14)
    dates, hrs = [], []
    for i in range(days_to_show):
        dates.append((datetime.now() + timedelta(days=i)).strftime("%b %d"))
        if i >= days_to_show - 2:
            hrs.append(max(1, hours * 0.5))
        elif i >= days_to_show - 5:
            hrs.append(hours * 1.1)
        else:
            hrs.append(float(hours))
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dates, y=hrs, marker_color="#818CF8",
        text=[str(round(h, 1)) + "h" for h in hrs], textposition="outside",
        textfont=dict(size=10),
    ))
    fig.update_layout(
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#F3F4F6", title="Hours"),
        height=240, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=10, t=20, b=20),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────────────────────

def dashboard_page():
    page_header("📊 Life Dashboard", "Your command center — everything at a glance")
    uid    = st.session_state.user_id
    inputs = st.session_state.user_inputs

    try:
        streak = db.get_consistency_streak(uid)
    except Exception:
        streak = 0

    # ── Metric row ────────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        stress = inputs.get("stress_level", 5)
        color = "#EF4444" if stress >= 7 else "#F59E0B" if stress >= 4 else "#10B981"
        st.markdown(
            '<div class="metric-card"><div class="metric-icon">🧠</div>'
            '<div class="metric-value" style="color:' + color + '">' + str(stress) + '/10</div>'
            '<div class="metric-label">Stress Level</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        days_left = 0
        if inputs.get("exam_date"):
            try:
                days_left = max(0, (datetime.strptime(inputs["exam_date"], "%Y-%m-%d") - datetime.now()).days)
            except Exception:
                pass
        st.markdown(
            '<div class="metric-card"><div class="metric-icon">📅</div>'
            '<div class="metric-value">' + str(days_left) + '</div>'
            '<div class="metric-label">Days to Exam</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        budget   = inputs.get("monthly_budget", 0)
        expenses = inputs.get("current_expenses", 0)
        savings  = max(0, budget - expenses)
        st.markdown(
            '<div class="metric-card"><div class="metric-icon">💰</div>'
            '<div class="metric-value">$' + str(savings) + '</div>'
            '<div class="metric-label">Monthly Savings</div></div>',
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            '<div class="metric-card"><div class="metric-icon">🔥</div>'
            '<div class="metric-value">' + str(streak) + '</div>'
            '<div class="metric-label">Day Streak</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AI config expander ────────────────────────────────────────────────────
    with st.expander("🚀 Run AI Life Analysis",
                     expanded=not bool(st.session_state.analysis_results)):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**🩺 Health**")
            stress_level = st.slider("Stress level", 1, 10,
                                     inputs.get("stress_level", 5), key="sl_stress")
            sleep_hours  = st.number_input("Sleep hours/night", 0, 12,
                                           inputs.get("sleep_hours", 7), key="sl_sleep")
            exercise     = st.selectbox("Exercise frequency",
                                        ["Rarely", "1–2×/week", "3–4×/week", "Daily"],
                                        key="sl_ex")
        with c2:
            st.markdown("**📚 Study**")
            exam_date  = st.date_input(
                "Exam date",
                min_value=datetime.now().date(),
                value=(datetime.now() + timedelta(days=30)).date(),
                key="sl_exam",
            )
            study_hrs = st.number_input("Study hours/day", 0, 14,
                                        inputs.get("current_study_hours", 3), key="sl_shrs")
        with c3:
            st.markdown("**💰 Finance**")
            budget   = st.number_input("Monthly budget ($)", 0, 500000,
                                       inputs.get("monthly_budget", 2000), step=100, key="sl_budget")
            expenses = st.number_input("Monthly expenses ($)", 0, 500000,
                                       inputs.get("current_expenses", 1500), step=100, key="sl_exp")

        problem = st.text_area(
            "What's your main challenge?",
            inputs.get("problem", "I need to balance exam prep, stay healthy, and manage my budget."),
            height=80, key="sl_problem",
        )

        st.session_state.user_inputs = {
            "stress_level": stress_level, "sleep_hours": sleep_hours,
            "exercise_frequency": exercise,
            "exam_date": exam_date.strftime("%Y-%m-%d"),
            "days_until_exam": (exam_date - datetime.now().date()).days,
            "current_study_hours": study_hrs,
            "monthly_budget": budget, "current_expenses": expenses, "problem": problem,
        }

        _api_key_cached = get_api_key()
        if not _api_key_cached:
            st.warning(" ")

        r1, _, r3 = st.columns([2, 1, 2])
        with r1:
            if st.button("⚡ Analyze My Life", type="primary",
                         use_container_width=True, key="run_analysis"):
                run_ai_analysis(st.session_state.user_inputs)
        with r3:
            if st.session_state.analysis_results:
                if st.button("🗑️ Clear Results", use_container_width=True,
                             key="clear_analysis"):
                    st.session_state.analysis_results = None
                    st.rerun()

    # ── Charts ────────────────────────────────────────────────────────────────
    if inputs:
        ca, cb, cc = st.columns(3)
        with ca:
            st.markdown('<div class="section-header">🩺 Health Radar</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(
                create_health_chart(
                    inputs.get("stress_level", stress_level),
                    inputs.get("sleep_hours", sleep_hours),
                ),
                use_container_width=True, config={"displayModeBar": False},
            )
        with cb:
            st.markdown('<div class="section-header">💰 Budget Split</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(
                create_finance_chart(
                    inputs.get("monthly_budget", budget),
                    inputs.get("current_expenses", expenses),
                ),
                use_container_width=True, config={"displayModeBar": False},
            )
        with cc:
            st.markdown('<div class="section-header">📚 Study Plan</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(
                create_study_chart(
                    inputs.get("days_until_exam", 30),
                    inputs.get("current_study_hours", study_hrs),
                ),
                use_container_width=True, config={"displayModeBar": False},
            )

    # ── AI results ────────────────────────────────────────────────────────────
    if st.session_state.analysis_results:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">🤖 AI Analysis Report</div>',
                    unsafe_allow_html=True)
        results = st.session_state.analysis_results
        score   = results.get("validation_report", {}).get("overall_score", 80)

        s1, s2, s3, s4 = st.columns(4)
        for col, lbl, val in [
            (s1, "Health", "✅"), (s2, "Finance", "✅"),
            (s3, "Study", "✅"), (s4, "Score", str(score) + "/100"),
        ]:
            with col:
                st.metric(lbl, val)

        cross = results.get("cross_domain_insights", "")
        if cross:
            st.markdown(
                '<div class="insight-card"><strong>🔗 Cross-Domain Insights</strong>'
                "<p>" + cross.replace("\n", "<br>") + "</p></div>",
                unsafe_allow_html=True,
            )

        t1, t2, t3, t4 = st.tabs(
            ["🩺 Health Plan", "💰 Finance Plan", "📚 Study Plan", "🎯 Master Plan"]
        )
        for tab, key in [(t1, "health"), (t2, "finance"),
                         (t3, "study"), (t4, "coordination")]:
            with tab:
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.markdown(results.get(key, "No data available."))
                st.markdown("</div>", unsafe_allow_html=True)


def health_vault_page():
    page_header("💊 Health Vault",
                "Track medicines, log health data, monitor trends")
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
                    med_freq = st.selectbox("Frequency",
                        ["Daily", "Twice Daily", "Weekly", "As Needed"], key="med_freq")
                    med_time = st.selectbox("Time",
                        ["Morning", "Afternoon", "Evening", "Night", "Anytime"], key="med_time")
                if st.button("Add Medicine", type="primary", key="add_med"):
                    if med_name.strip():
                        db.add_medicine(uid, med_name.strip(), med_dose, med_freq, med_time)
                        st.success("Added " + med_name)
                        st.rerun()
                    else:
                        st.warning("Enter medicine name")

        with c2:
            meds = db.get_all_medicines(uid)
            if meds:
                st.markdown(
                    '<div class="section-header">💊 Active Medicines (' + str(len(meds)) + ')</div>',
                    unsafe_allow_html=True,
                )
                for med in meds:
                    last_taken = "Never"
                    if med.get("last_taken"):
                        try:
                            diff = (datetime.now() - datetime.fromisoformat(med["last_taken"])).days
                            last_taken = "Today" if diff == 0 else str(diff) + "d ago"
                        except Exception:
                            last_taken = "Unknown"
                    col_a, col_b, col_c = st.columns([5, 1, 1])
                    with col_a:
                        st.markdown(
                            '<div class="list-item">'
                            '<div class="list-item-title">💊 ' + med["name"] + "</div>"
                            '<div class="list-item-meta">'
                            + (med.get("dosage") or "—") + " · "
                            + (med.get("frequency") or "—") + " · "
                            + (med.get("time_of_day") or "Anytime")
                            + " · Last: " + last_taken + "</div></div>",
                            unsafe_allow_html=True,
                        )
                    with col_b:
                        if st.button("✅", key="med_take_" + med["id"], help="Mark taken"):
                            db.update_medicine_taken(uid, med["id"])
                            st.success("Marked!")
                            st.rerun()
                    with col_c:
                        if st.button("🗑", key="med_del_" + med["id"], help="Remove"):
                            db.delete_medicine(uid, med["id"])
                            st.rerun()
            else:
                st.info("No medicines added yet.")

    with tab2:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown('<div class="section-header">📝 Log Today\'s Health</div>',
                        unsafe_allow_html=True)
            log_date = st.date_input("Date", datetime.now().date(), key="hl_date")
            mood     = st.slider("Mood (1=bad, 10=great)", 1, 10, 6, key="hl_mood")
            sleep_q  = st.slider("Sleep quality", 1, 10, 7, key="hl_sleep")
            energy   = st.slider("Energy level", 1, 10, 6, key="hl_energy")
            water    = st.number_input("Water glasses", 0, 20, 8, key="hl_water")
            weight   = st.number_input("Weight (kg, optional)", 0.0, 300.0, 0.0,
                                       step=0.1, key="hl_weight")
            symptoms = st.text_area("Notes / Symptoms",
                                    placeholder="How are you feeling today?",
                                    height=80, key="hl_symptoms")
            if st.button("💾 Save Log", type="primary", key="save_hl"):
                db.add_health_log(uid, log_date.strftime("%Y-%m-%d"),
                                  symptoms, sleep_q, energy, water, mood,
                                  weight if weight > 0 else 0)
                st.success("Health log saved!")
                db._record_checkin(uid)

        with c2:
            st.markdown('<div class="section-header">📋 Recent Logs</div>',
                        unsafe_allow_html=True)
            recent = db.get_health_logs(uid, days=7)
            if recent:
                for log in recent[:5]:
                    sym = log.get("symptoms", "") or ""
                    st.markdown(
                        '<div class="list-item">'
                        '<div class="list-item-title">📅 ' + log["date"] + "</div>"
                        '<div class="list-item-meta">'
                        "Mood: " + str(log.get("mood","—")) + "/10 · "
                        "Energy: " + str(log.get("energy_level","—")) + "/10 · "
                        "Sleep: " + str(log.get("sleep_quality","—")) + "/10 · "
                        "Water: " + str(log.get("water_intake","—")) + "🥤</div>"
                        + ('<div class="list-item-meta">📝 ' + sym[:60] + "…</div>" if sym else "")
                        + "</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No logs yet. Log your first day above!")

    with tab3:
        logs = db.get_health_logs(uid, days=14)
        if len(logs) >= 2:
            df = pd.DataFrame(logs)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
            fig = go.Figure()
            for col_name, name, color in [
                ("energy_level", "Energy", "#6366F1"),
                ("sleep_quality", "Sleep", "#10B981"),
                ("mood", "Mood", "#F59E0B"),
            ]:
                if col_name in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df["date"], y=df[col_name], name=name,
                        line=dict(color=color, width=2),
                        mode="lines+markers", marker=dict(size=6),
                    ))
            fig.update_layout(
                height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0, 11], gridcolor="#F3F4F6"),
                xaxis=dict(showgrid=False),
                legend=dict(orientation="h", y=-0.15),
                margin=dict(l=30, r=10, t=10, b=40),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Log health data for at least 2 days to see trends.")


def finance_hub_page():
    page_header("💰 Finance Hub",
                "Budget management, bill tracking, and financial goals")
    uid = st.session_state.user_id
    tab1, tab2, tab3 = st.tabs(["📋 Bills", "🧮 Budget Planner", "📊 Analytics"])

    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            with st.expander("➕ Add Bill", expanded=False):
                b1, b2 = st.columns(2)
                with b1:
                    bill_name = st.text_input("Bill name", placeholder="Netflix, Rent…",
                                              key="bill_name")
                    bill_amt  = st.number_input("Amount ($)", 0.0, 100000.0, 100.0,
                                                step=10.0, key="bill_amt")
                with b2:
                    bill_due = st.number_input("Due day (1–31)", 1, 31, 15, key="bill_due")
                    bill_cat = st.selectbox("Category",
                        ["Rent/Mortgage", "Utilities", "Insurance",
                         "Subscriptions", "Loan", "Other"], key="bill_cat")
                if st.button("Add Bill", type="primary", key="add_bill"):
                    if bill_name.strip():
                        db.add_bill(uid, bill_name.strip(), bill_amt, bill_due, bill_cat)
                        st.success("Added " + bill_name)
                        st.rerun()
                    else:
                        st.warning("Enter bill name")

        with c2:
            bills = db.get_all_bills(uid)
            today_day = datetime.now().day
            if bills:
                total = sum(b["amount"] for b in bills)
                paid  = sum(b["amount"] for b in bills if b["paid_this_month"])
                st.markdown(
                    '<div class="metric-card" style="text-align:left;margin-bottom:16px;padding:16px 20px;">'
                    '<div style="display:flex;justify-content:space-between;align-items:center;">'
                    '<div><div class="metric-label">TOTAL MONTHLY</div>'
                    '<div class="metric-value">$' + str(round(total, 0)) + '</div></div>'
                    '<div><div class="metric-label">PAID</div>'
                    '<div class="metric-value" style="color:#10B981">$' + str(round(paid, 0)) + '</div></div>'
                    '<div><div class="metric-label">REMAINING</div>'
                    '<div class="metric-value" style="color:#EF4444">$' + str(round(total - paid, 0)) + '</div></div>'
                    "</div></div>",
                    unsafe_allow_html=True,
                )
                for bill in bills:
                    due_soon  = abs(bill["due_day"] - today_day) <= 3
                    paid_flag = bool(bill.get("paid_this_month"))
                    icon = "✅" if paid_flag else ("⚠️" if due_soon else "⏰")
                    border = ("border-left:3px solid #10B981" if paid_flag
                              else "border-left:3px solid #F59E0B" if due_soon else "")
                    col_a, col_b, col_c = st.columns([5, 1, 1])
                    with col_a:
                        st.markdown(
                            '<div class="list-item" style="' + border + '">'
                            '<div class="list-item-title">' + icon + " " + bill["name"]
                            + " — $" + str(round(bill["amount"], 2)) + "</div>"
                            '<div class="list-item-meta">Due: Day ' + str(bill["due_day"])
                            + " · " + bill["category"]
                            + (" · ✅ Paid" if paid_flag else " · ⚠️ Due soon!" if due_soon else "")
                            + "</div></div>",
                            unsafe_allow_html=True,
                        )
                    with col_b:
                        if not paid_flag:
                            if st.button("✅", key="pay_" + bill["id"], help="Mark paid"):
                                db.mark_bill_paid(uid, bill["id"])
                                st.rerun()
                    with col_c:
                        if st.button("🗑", key="del_bill_" + bill["id"], help="Delete"):
                            db.delete_bill(uid, bill["id"])
                            st.rerun()
            else:
                st.info("No bills added. Add recurring bills to track them.")

    with tab2:
        st.markdown('<div class="section-header">🧮 Smart Budget Calculator</div>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            income       = st.number_input("Monthly income ($)", 0, 500000, 3000,
                                           step=100, key="fp_income")
            savings_goal = st.slider("Savings goal (%)", 5, 50, 20, key="fp_savings_pct")
            needs_pct    = 50
            wants_pct    = max(10, 100 - savings_goal - needs_pct)
            st.markdown("<br>", unsafe_allow_html=True)
            for cat, pct in [
                ("🏠 Needs (" + str(needs_pct) + "%)", needs_pct),
                ("🎉 Wants (" + str(wants_pct) + "%)", wants_pct),
                ("💰 Savings (" + str(savings_goal) + "%)", savings_goal),
            ]:
                amt = income * pct / 100
                r_col, v_col = st.columns([3, 1])
                with r_col:
                    st.progress(pct / 100, text=cat)
                with v_col:
                    st.write("**$" + str(round(amt)) + "**")
        with c2:
            months     = list(range(1, 7))
            monthly_s  = income * savings_goal / 100
            cumulative = [monthly_s * m for m in months]
            fig = go.Figure(go.Bar(
                x=["Month " + str(m) for m in months], y=cumulative,
                marker_color="#6366F1",
                text=["$" + str(round(v)) for v in cumulative], textposition="outside",
            ))
            fig.update_layout(
                height=240, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                yaxis=dict(showgrid=True, gridcolor="#F3F4F6"),
                xaxis=dict(showgrid=False),
                margin=dict(l=10, r=10, t=20, b=10),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with tab3:
        bills_for_chart = db.get_all_bills(uid)
        if bills_for_chart:
            cats_data = {}
            for b in bills_for_chart:
                cats_data[b["category"]] = cats_data.get(b["category"], 0) + b["amount"]
            fig = go.Figure(data=[go.Pie(
                labels=list(cats_data.keys()), values=list(cats_data.values()),
                hole=0.4, textinfo="label+percent",
                marker=dict(colors=["#6366F1","#8B5CF6","#A78BFA","#C4B5FD","#DDD6FE"]),
            )])
            fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                               showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
            st.markdown('<div class="section-header">Bills by Category</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Add bills to see analytics.")


def study_center_page():
    page_header("📚 Study Center",
                "Focus sessions, study planning, and performance tracking")
    uid = st.session_state.user_id
    tab1, tab2, tab3 = st.tabs(["🍅 Focus Timer", "📊 Statistics", "📅 Sessions"])

    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            if not st.session_state.pomodoro_active:
                st.markdown('<div class="section-header">⚙️ Configure Session</div>',
                            unsafe_allow_html=True)
                work_min = st.number_input("Work minutes", 5, 90, 25, key="p_work")
                break_min = st.number_input("Break minutes", 1, 30, 5, key="p_break")
                subject   = st.text_input("Subject", placeholder="Mathematics, Physics…",
                                          key="p_subj")
                focus     = st.slider("Focus level going in", 1, 10, 7, key="p_focus")
                if st.button("▶ Start Focus Session", type="primary",
                             use_container_width=True, key="p_start"):
                    st.session_state.pomodoro_active  = True
                    st.session_state.pomodoro_time    = work_min * 60
                    st.session_state.break_time       = break_min * 60
                    st.session_state.pomodoro_work    = True
                    st.session_state.pomodoro_subject = subject or "General Study"
                    st.session_state.p_work_min       = work_min
                    st.session_state.p_focus_level    = focus
                    st.rerun()
            else:
                # ── Auto-refresh every second while timer is running ──────────
                if AUTOREFRESH_AVAILABLE:
                    st_autorefresh(interval=1000, limit=None, key="pomodoro_refresh")

                # ── Decrement the timer by 1 second each refresh ──────────────
                if st.session_state.pomodoro_active:
                    if st.session_state.pomodoro_time > 0:
                        st.session_state.pomodoro_time -= 1
                    else:
                        # Time's up — switch phase
                        if st.session_state.pomodoro_work:
                            st.session_state.pomodoro_time = st.session_state.break_time
                            st.session_state.pomodoro_work = False
                            st.success("⏰ Break time! Well done.")
                        else:
                            work_min = st.session_state.get("p_work_min", 25)
                            st.session_state.pomodoro_time = work_min * 60
                            st.session_state.pomodoro_work = True
                            st.info("🍅 Break over — back to focus!")

                mins, secs = divmod(st.session_state.pomodoro_time, 60)
                phase = "FOCUS" if st.session_state.pomodoro_work else "BREAK"
                phase_color = "#E53935" if st.session_state.pomodoro_work else "#43A047"
                total_secs  = (st.session_state.get("p_work_min", 25) * 60
                               if st.session_state.pomodoro_work
                               else st.session_state.break_time)
                progress_pct = max(0, int(
                    (total_secs - st.session_state.pomodoro_time) / max(total_secs, 1) * 100
                ))

                st.markdown(
                    '<div class="timer-card" style="position:relative;">'
                    '<div class="timer-phase" style="background:rgba(255,255,255,0.25);">' + phase + "</div>"
                    '<div class="timer-digits">'
                    + str(mins).zfill(2) + ":" + str(secs).zfill(2) + "</div>"
                    '<div class="timer-subject">📚 '
                    + st.session_state.pomodoro_subject + "</div>"
                    '<div style="margin-top:14px;background:rgba(255,255,255,0.2);'
                    'border-radius:8px;height:6px;overflow:hidden;">'
                    '<div style="height:6px;border-radius:8px;background:rgba(255,255,255,0.85);'
                    'width:' + str(progress_pct) + '%;transition:width 0.5s ease;"></div>'
                    "</div></div>",
                    unsafe_allow_html=True,
                )
                if not AUTOREFRESH_AVAILABLE:
                    st.caption("ℹ️ Add `streamlit-autorefresh` to requirements.txt for live countdown.")

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
                            st.session_state.pomodoro_time = (
                                st.session_state.get("p_work_min", 25) * 60
                            )
                            st.session_state.pomodoro_work = True
                        st.rerun()
                with cc3:
                    if st.button("⏹ End", use_container_width=True, key="p_end"):
                        work_min = st.session_state.get("p_work_min", 25)
                        elapsed  = work_min * 60 - st.session_state.pomodoro_time
                        duration = max(1, elapsed // 60)
                        if st.session_state.pomodoro_work and elapsed > 30:
                            db.add_study_session(
                                uid, duration, st.session_state.pomodoro_subject,
                                st.session_state.get("p_focus_level", 7),
                            )
                            st.success("✅ Session saved: " + str(duration) + " min")
                        st.session_state.pomodoro_active = False
                        st.rerun()

        with c2:
            st.markdown('<div class="section-header">💡 Study Tips</div>',
                        unsafe_allow_html=True)
            tips = [
                ("🧠", "Active Recall",
                 "Close notes and write everything you remember. More effective than re-reading."),
                ("🔄", "Spaced Repetition",
                 "Review day 1, day 3, day 7, day 21 for long-term memory."),
                ("✍️", "Feynman Technique",
                 "Explain concepts like teaching a 10-year-old to find knowledge gaps."),
                ("🎯", "Interleaving",
                 "Mix subjects within sessions instead of studying one topic all at once."),
                ("💤", "Sleep to Learn",
                 "Memory consolidation happens during sleep — never sacrifice it!"),
            ]
            for icon, title, desc in tips:
                st.markdown(
                    '<div class="list-item">'
                    '<div class="list-item-title">' + icon + " " + title + "</div>"
                    '<div class="list-item-meta">' + desc + "</div></div>",
                    unsafe_allow_html=True,
                )

    with tab2:
        summary = db.get_weekly_study_summary(uid)
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("Weekly Hours",
                           str(summary["total_minutes"] // 60) + "h "
                           + str(summary["total_minutes"] % 60) + "m")
        with m2: st.metric("Sessions", summary["sessions"])
        with m3: st.metric("Avg Focus", str(summary["avg_score"]) + "/10")
        with m4: st.metric("Daily Avg", str(round(summary["total_minutes"] / 7 / 60, 1)) + "h")

        sessions = summary.get("sessions_data", [])
        if sessions:
            df = pd.DataFrame(sessions)
            df["date"] = pd.to_datetime(df["date"])
            df = df.groupby("date").agg(
                {"duration_minutes": "sum", "productivity_score": "mean"}
            ).reset_index()
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df["date"], y=df["duration_minutes"] / 60,
                name="Hours", marker_color="#818CF8",
            ))
            fig.update_layout(
                height=250, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                yaxis_title="Hours", xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#F3F4F6"),
                margin=dict(l=30, r=10, t=10, b=20),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Complete study sessions to see analytics.")

    with tab3:
        all_sessions = db.get_study_sessions(uid, limit=20)
        if all_sessions:
            for s in all_sessions:
                sc = s["productivity_score"]
                sc_color = "#10B981" if sc >= 7 else "#F59E0B" if sc >= 4 else "#EF4444"
                st.markdown(
                    '<div class="list-item">'
                    '<div class="list-item-title">📚 ' + s["subject"]
                    + " — " + str(s["duration_minutes"]) + " min</div>"
                    '<div class="list-item-meta">📅 ' + s["date"]
                    + ' &nbsp;·&nbsp; <span style="color:' + sc_color + '">⭐ '
                    + str(sc) + "/10 focus</span></div></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No sessions yet. Start a Focus Timer session above!")


def productivity_page():
    page_header("⚡ Productivity Hub",
                "Task management, smart notes, and daily planning")
    uid = st.session_state.user_id
    tab1, tab2 = st.tabs(["✅ Tasks", "📝 Notes"])

    with tab1:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            with st.form("task_form", clear_on_submit=True):
                fc1, fc2, fc3 = st.columns([4, 2, 2])
                with fc1:
                    new_task = st.text_input("Task", placeholder="What needs to be done?",
                                             key="new_task_inp")
                with fc2:
                    task_cat = st.selectbox("Category",
                        ["Personal", "Health", "Finance", "Study", "Work"], key="task_cat")
                with fc3:
                    task_pri = st.selectbox("Priority",
                        ["high", "medium", "low"], key="task_pri")
                if st.form_submit_button("Add Task", type="primary",
                                         use_container_width=True):
                    if new_task.strip():
                        db.add_action_item(uid, new_task.strip(), task_cat, "User", task_pri)
                        st.rerun()

            tasks = db.get_pending_actions(uid)
            if tasks:
                st.markdown(
                    '<div class="section-header">📋 Active Tasks (' + str(len(tasks)) + ')</div>',
                    unsafe_allow_html=True,
                )
                for task in tasks:
                    cat = task.get("category", "Personal")
                    pri = task.get("priority", "medium")
                    pri_colors = {"high": "#EF4444", "medium": "#F59E0B", "low": "#10B981"}
                    pri_color = pri_colors.get(pri, "#8B909A")
                    col_a, col_b, col_c = st.columns([6, 1, 1])
                    with col_a:
                        cat_badge = '<span class="badge badge-' + cat.lower() + '">' + cat + "</span>"
                        pri_badge = ('<span class="badge badge-' + pri
                                     + '" style="color:' + pri_color + '">'
                                     + pri.upper() + "</span>")
                        st.markdown(
                            '<div class="list-item">'
                            '<div class="list-item-title">' + task["task"] + "</div>"
                            '<div class="list-item-meta">'
                            + cat_badge + " " + pri_badge
                            + " &nbsp;·&nbsp; Added "
                            + task.get("created_at", "")[:10] + "</div></div>",
                            unsafe_allow_html=True,
                        )
                    with col_b:
                        if st.button("✅", key="done_" + task["id"], help="Complete"):
                            db.mark_action_complete(uid, task["id"])
                            st.rerun()
                    with col_c:
                        if st.button("🗑", key="del_" + task["id"], help="Delete"):
                            db.delete_action(uid, task["id"])
                            st.rerun()
            else:
                st.info("🎉 All caught up! Add your first task above.")

        with c2:
            st.markdown('<div class="section-header">📊 Task Stats</div>',
                        unsafe_allow_html=True)
            try:
                stats = db.get_user_statistics(uid)
                rate = stats["completion_rate"]
                st.progress(rate / 100, text="Completion rate: " + str(round(rate)) + "%")
                st.markdown("<br>", unsafe_allow_html=True)
                sc1, sc2 = st.columns(2)
                with sc1: st.metric("Total", stats["total_actions"])
                with sc2: st.metric("Done",  stats["completed_actions"])
            except Exception:
                st.info("No task stats yet.")

    with tab2:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown('<div class="section-header">✍️ New Note</div>',
                        unsafe_allow_html=True)
            with st.form("note_form", clear_on_submit=True):
                note_title   = st.text_input("Title", placeholder="Note title…",
                                             key="nt_title")
                note_content = st.text_area("Content", height=180,
                                            placeholder="Write your thoughts…",
                                            key="nt_content")
                note_tags    = st.text_input("Tags (comma-separated)",
                                             placeholder="work, ideas, health", key="nt_tags")
                if st.form_submit_button("Save Note", type="primary",
                                         use_container_width=True):
                    if note_title.strip() and note_content.strip():
                        db.add_note(uid, note_title.strip(), note_content.strip(), note_tags)
                        st.rerun()
                    else:
                        st.warning("Title and content required")

        with c2:
            st.markdown('<div class="section-header">📓 Saved Notes</div>',
                        unsafe_allow_html=True)
            notes = db.get_notes(uid)
            if notes:
                for note in notes[:10]:
                    col_n, col_d = st.columns([5, 1])
                    with col_n:
                        pin_icon = "📌 " if note.get("pinned") else "📄 "
                        with st.expander(pin_icon + note["title"], expanded=False):
                            st.write(note["content"])
                            if note.get("tags"):
                                st.caption("🏷️ " + note["tags"])
                            st.caption("📅 " + note["updated_at"][:10])
                    with col_d:
                        if st.button("🗑", key="del_note_" + note["id"], help="Delete"):
                            db.delete_note(uid, note["id"])
                            st.rerun()
            else:
                st.info("No notes yet. Create your first note!")


def profile_page():
    page_header("👤 Profile & Settings",
                "Manage account, preferences, and view your stats")
    uid  = st.session_state.user_id
    user = st.session_state.user_data or {}

    tab1, tab2, tab3 = st.tabs(["👤 Account", "⚙️ Settings", "📊 Analytics"])

    with tab1:
        c1, c2 = st.columns([1, 2])
        with c1:
            verified_badge = (
                '<span style="background:#DCFCE7;color:#166534;padding:4px 10px;'
                'border-radius:20px;font-size:12px;font-weight:600;">✅ Verified</span>'
            )
            st.markdown(
                '<div class="card" style="text-align:center;padding:28px 20px;">'
                '<div class="profile-avatar-lg">👤</div>'
                '<div style="font-size:20px;font-weight:700;color:#1A1D23;">'
                + user.get("name", "User") + "</div>"
                '<div style="font-size:13px;color:#8B909A;margin-top:4px;">'
                + user.get("email", "") + "</div>"
                '<div style="margin-top:10px;">' + verified_badge + "</div>"
                '<div style="margin-top:10px;padding:8px 16px;background:#EEF2FF;'
                "border-radius:20px;display:inline-block;\">"
                '<span style="font-size:12px;font-weight:600;color:#4F46E5;">✨ Free Account</span>'
                "</div>"
                '<div style="font-size:11px;color:#8B909A;margin-top:10px;">Member since '
                + user.get("joined_at", "")[:10] + "</div></div>",
                unsafe_allow_html=True,
            )

        with c2:
            try:
                stats    = db.get_user_statistics(uid)
                streak   = db.get_consistency_streak(uid)
                analyses = db.get_recent_analyses(uid, limit=3)
            except Exception:
                stats    = {"total_actions":0,"completed_actions":0,"medicines_count":0,
                            "bills_count":0,"notes_count":0,"study_sessions":0,
                            "ai_analyses":0,"completion_rate":0}
                streak, analyses = 0, []

            st.markdown('<div class="section-header">📊 Your Stats</div>',
                        unsafe_allow_html=True)
            g1, g2, g3 = st.columns(3)
            with g1: st.metric("Total Tasks",   stats["total_actions"])
            with g2: st.metric("Day Streak",    streak)
            with g3: st.metric("Completion",
                                str(round(stats["completion_rate"])) + "%")

            st.markdown("<br>", unsafe_allow_html=True)
            g4, g5, g6 = st.columns(3)
            with g4: st.metric("Medicines", stats["medicines_count"])
            with g5: st.metric("Bills",     stats["bills_count"])
            with g6: st.metric("Notes",     stats["notes_count"])

            if analyses:
                st.markdown(
                    '<div class="section-header" style="margin-top:20px;">'
                    "🤖 Recent Analyses</div>",
                    unsafe_allow_html=True,
                )
                for a in analyses:
                    st.markdown(
                        '<div class="list-item"><div class="list-item-meta">📅 '
                        + a["created_at"][:16].replace("T", " ")
                        + " &nbsp;·&nbsp; Score: "
                        + str(a.get("score", "—")) + "/100</div></div>",
                        unsafe_allow_html=True,
                    )

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-header">👤 Edit Profile</div>',
                        unsafe_allow_html=True)
            with st.form("profile_form"):
                new_name = st.text_input("Display name", value=user.get("name", ""),
                                         key="pf_name")
                st.text_input("Email (cannot change)", value=user.get("email", ""),
                              disabled=True, key="pf_email")
                if st.form_submit_button("Update Profile", type="primary"):
                    if new_name.strip():
                        db.update_user_settings(uid, {"name": new_name.strip()})
                        st.session_state.user_data["name"] = new_name.strip()
                        st.success("Profile updated!")
                    else:
                        st.warning("Name cannot be empty")

            st.markdown(
                '<div class="section-header" style="margin-top:20px;">🔐 Change Password</div>',
                unsafe_allow_html=True,
            )
            with st.form("password_form"):
                old_pass     = st.text_input("Current password", type="password",
                                             key="pf_old")
                new_pass     = st.text_input("New password", type="password",
                                             key="pf_new")
                confirm_pass = st.text_input("Confirm new password", type="password",
                                             key="pf_conf")
                if st.form_submit_button("Change Password", type="primary"):
                    if not all([old_pass, new_pass, confirm_pass]):
                        st.error("Fill all fields")
                    elif new_pass != confirm_pass:
                        st.error("Passwords don't match")
                    elif len(new_pass) < 6:
                        st.error("Min 6 characters")
                    elif db.change_password(uid, old_pass, new_pass):
                        st.success("✅ Password changed!")
                    else:
                        st.error("Current password incorrect")

        with c2:
            st.markdown('<div class="section-header">🔔 Notifications</div>',
                        unsafe_allow_html=True)
            with st.form("notif_form"):
                n_email  = st.toggle("Email notifications",
                                     value=bool(user.get("notifications_email", 1)),
                                     key="n_email")
                n_push   = st.toggle("Push reminders",
                                     value=bool(user.get("notifications_push", 1)),
                                     key="n_push")
                n_weekly = st.toggle("Weekly progress reports",
                                     value=bool(user.get("notifications_weekly", 1)),
                                     key="n_weekly")
                if st.form_submit_button("Save Notifications", type="primary"):
                    db.update_user_settings(uid, {
                        "notifications_email":  int(n_email),
                        "notifications_push":   int(n_push),
                        "notifications_weekly": int(n_weekly),
                    })
                    st.success("Saved!")

            st.markdown(
                '<div class="section-header" style="margin-top:20px;">🎨 Appearance</div>',
                unsafe_allow_html=True,
            )
            with st.form("theme_form"):
                font_size = st.select_slider(
                    "Font size", ["Small", "Medium", "Large"],
                    value=user.get("font_size", "Medium"), key="pf_font"
                )
                if st.form_submit_button("Apply", type="primary"):
                    db.update_user_settings(uid, {"font_size": font_size})
                    st.session_state.user_data["font_size"] = font_size
                    st.success("Applied!")

            st.markdown(
                '<div class="section-header" style="margin-top:20px;">🗑️ Account Actions</div>',
                unsafe_allow_html=True,
            )
            if st.button("🚪 Sign Out", use_container_width=True):
                logout()

    with tab3:
        try:
            stats = db.get_user_statistics(uid)
            st.markdown('<div class="section-header">📈 Activity Overview</div>',
                        unsafe_allow_html=True)
            domains = ["Tasks", "Health", "Finance", "Study", "Notes"]
            values  = [
                min(100, stats["total_actions"] * 5),
                min(100, len(db.get_health_logs(uid)) * 10),
                min(100, stats["bills_count"] * 15),
                min(100, stats["study_sessions"] * 8),
                min(100, stats["notes_count"] * 10),
            ]
            fig = go.Figure(go.Bar(
                x=domains, y=values,
                marker_color=["#6366F1","#10B981","#F59E0B","#8B5CF6","#EC4899"],
                text=[str(v) + "%" for v in values], textposition="outside",
                textfont=dict(size=11),
            ))
            fig.update_layout(
                height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0, 115], showgrid=True, gridcolor="#F3F4F6"),
                xaxis=dict(showgrid=False),
                margin=dict(l=10, r=10, t=20, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        except Exception:
            st.info("Complete more activities to see analytics here!")


# ─────────────────────────────────────────────────────────────────────────────
# AI ANALYSIS RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_ai_analysis(user_inputs):
    api_key = get_api_key()
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key

    with st.spinner("🧠 Analyzing your life with AI…"):
        try:
            crew    = LifeOpsCrew(user_inputs)
            results = crew.kickoff()
            st.session_state.analysis_results = results
            if st.session_state.user_id:
                db.save_ai_analysis(st.session_state.user_id, results)
                db._record_checkin(st.session_state.user_id)
            st.success("✅ Analysis complete!")
            st.balloons()
        except Exception as exc:
            st.error("Analysis failed: " + str(exc)[:200])


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

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
