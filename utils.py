import os
import random
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_smtp_credentials():
    """Read sender email + app password from Streamlit secrets OR env vars."""
    sender = ""
    password = ""
    # Try Streamlit secrets first (works on cloud + local with secrets.toml)
    try:
        import streamlit as st
        sender = st.secrets.get("SENDER_EMAIL", "")
        password = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        pass
    # Fall back to environment variables
    if not sender:
        sender = os.environ.get("SENDER_EMAIL", "")
    if not password:
        password = os.environ.get("APP_PASSWORD", "")
    return sender, password


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def generate_otp(length=6):
    """Return a random numeric OTP string of the given length."""
    return "".join(random.choices(string.digits, k=length))


def send_otp_email(receiver_email):
    """
    Generate a 6-digit OTP and send it to receiver_email via Gmail SMTP SSL.

    Returns
    -------
    (success, otp, message)
        success  : bool   – True if email was sent
        otp      : str    – the code (empty string on failure)
        message  : str    – human-readable status / error description
    """
    sender_email, app_password = _get_smtp_credentials()

    if not sender_email or not app_password:
        return (
            False,
            "",
            "Email credentials not configured. "
            "Add SENDER_EMAIL and APP_PASSWORD to .streamlit/secrets.toml or your .env file.",
        )

    otp = generate_otp()
    sent_at = datetime.now().strftime("%d %b %Y at %I:%M %p")

    # ── HTML email body ───────────────────────────────────────────────────────
    html_body = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><title>LifeOps AI - Verify Your Account</title></head>
<body style="margin:0;padding:0;background:#F7F8FC;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#F7F8FC;padding:40px 0;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:16px;border:1px solid #E2E8F0;
                    box-shadow:0 4px 24px rgba(99,102,241,0.08);">
        <!-- Header -->
        <tr><td align="center"
              style="background:linear-gradient(135deg,#6366F1,#8B5CF6);
                     border-radius:16px 16px 0 0;padding:32px 24px 28px;">
          <div style="font-size:42px;margin-bottom:10px;">&#129504;</div>
          <div style="font-size:22px;font-weight:700;color:#ffffff;">LifeOps AI</div>
          <div style="font-size:13px;color:rgba(255,255,255,0.8);margin-top:4px;">
            Email Verification
          </div>
        </td></tr>
        <!-- Body -->
        <tr><td style="padding:36px 40px 28px;">
          <p style="margin:0 0 8px;font-size:16px;font-weight:600;color:#1A1D23;">Hello!</p>
          <p style="margin:0 0 24px;font-size:14px;color:#64748B;line-height:1.7;">
            You requested to create a LifeOps AI account. Use the verification
            code below to complete your registration.
            This code is valid for <strong>10 minutes</strong>.
          </p>
          <!-- OTP Box -->
          <div style="background:#EEF2FF;border:2px dashed #818CF8;border-radius:12px;
                      padding:24px;text-align:center;margin-bottom:24px;">
            <div style="font-size:11px;font-weight:700;color:#6366F1;letter-spacing:2px;
                         text-transform:uppercase;margin-bottom:8px;">
              Your Verification Code
            </div>
            <div style="font-size:42px;font-weight:800;
                         font-family:'Courier New',monospace;
                         color:#4F46E5;letter-spacing:8px;">
              """ + otp + """
            </div>
            <div style="font-size:11px;color:#94A3B8;margin-top:8px;">
              Sent on """ + sent_at + """
            </div>
          </div>
          <p style="margin:0;font-size:13px;color:#94A3B8;line-height:1.7;">
            If you did not request this, you can safely ignore this email.
            Your account will not be created without OTP verification.
          </p>
        </td></tr>
        <!-- Footer -->
        <tr><td style="padding:16px 40px 28px;border-top:1px solid #F1F5F9;">
          <p style="margin:0;font-size:12px;color:#CBD5E1;text-align:center;">
            LifeOps AI &mdash; Life Management Platform<br/>
            This is an automated message &mdash; please do not reply.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    plain_body = (
        "Your LifeOps AI verification code is: " + otp + "\n\n"
        "This code expires in 10 minutes.\n"
        "If you did not request this, ignore this email."
    )

    # ── Build MIME message ────────────────────────────────────────────────────
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "LifeOps AI - Your Verification Code: " + otp
    msg["From"] = "LifeOps AI <" + sender_email + ">"
    msg["To"] = receiver_email
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    # ── Send via Gmail SMTP SSL port 465 ──────────────────────────────────────
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        return True, otp, "OTP sent successfully."

    except smtplib.SMTPAuthenticationError:
        return (
            False, "",
            "Gmail authentication failed. "
            "Make sure you are using a Google App Password, not your regular Gmail password. "
            "See README_OTP.md for setup instructions.",
        )
    except smtplib.SMTPRecipientsRefused:
        return (
            False, "",
            "The email address '" + receiver_email + "' was refused by the mail server.",
        )
    except smtplib.SMTPException as exc:
        return False, "", "SMTP error: " + str(exc)
    except OSError as exc:
        return False, "", "Network error - could not reach Gmail SMTP: " + str(exc)


# ─────────────────────────────────────────────────────────────────────────────
# MISC UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def load_env():
    """Load .env file if present and return GOOGLE_API_KEY."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    return os.environ.get("GOOGLE_API_KEY", "")


def format_date(date_str):
    """Convert YYYY-MM-DD to human-readable string."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
    except Exception:
        return date_str


def calculate_days_until(target_date):
    """Return days between today and target_date string (YYYY-MM-DD)."""
    try:
        return max(0, (datetime.strptime(target_date, "%Y-%m-%d") - datetime.now()).days)
    except Exception:
        return 0
