import os
import smtplib
import logging
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# Load configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@smarty.ai")


def get_welcome_html_template(
    user_name: str, gender: str = "male"
) -> str:
    is_female = gender.lower() == "female"
    accent_color = "#ec4899" if is_female else "#10b981"
    accent_light = (
        "rgba(236,72,153,0.15)"
        if is_female
        else "rgba(16,185,129,0.15)"
    )
    brand_sub = (
        "FEMME FITNESS v4.0"
        if is_female
        else "NEURAL FITNESS v4.0"
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Welcome to Smarty AI</title>
        <style>
            body {{
                font-family: 'Inter', Helvetica, Arial, sans-serif;
                background-color: #020617;
                color: #f1f5f9;
                margin: 0;
                padding: 0;
                -webkit-font-smoothing: antialiased;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #0b1329;
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 24px;
                overflow: hidden;
                box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            }}
            .header {{
                background: linear-gradient(135deg, #0f172a, #020617);
                padding: 40px 30px;
                text-align: center;
                border-bottom: 2px solid {accent_color};
            }}
            .logo {{
                font-size: 28px;
                font-weight: 900;
                font-style: italic;
                letter-spacing: -0.05em;
                color: #ffffff;
                margin: 0;
            }}
            .logo span {{
                color: {accent_color};
            }}
            .tagline {{
                font-size: 8px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 0.4em;
                color: #64748b;
                margin-top: 5px;
            }}
            .content {{
                padding: 40px 30px;
                line-height: 1.8;
                font-size: 15px;
                color: #cbd5e1;
            }}
            .headline {{
                font-size: 24px;
                font-weight: 800;
                color: #ffffff;
                margin-top: 0;
                margin-bottom: 15px;
            }}
            .badge {{
                display: inline-block;
                padding: 5px 12px;
                border-radius: 12px;
                background-color: {accent_light};
                color: {accent_color};
                font-size: 11px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                margin-bottom: 25px;
            }}
            .feature-list {{
                margin: 30px 0;
                padding: 0;
                list-style: none;
            }}
            .feature-item {{
                margin-bottom: 20px;
                padding-left: 30px;
                position: relative;
            }}
            .feature-item::before {{
                content: "⚡";
                position: absolute;
                left: 0;
                color: {accent_color};
                font-weight: bold;
            }}
            .feature-title {{
                font-weight: bold;
                color: #ffffff;
            }}
            .cta-button {{
                display: block;
                text-align: center;
                background-color: {accent_color};
                color: #020617 !important;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-size: 12px;
                text-decoration: none;
                padding: 18px 30px;
                border-radius: 16px;
                margin: 35px 0 15px 0;
                box-shadow: 0 10px 20px {accent_light};
            }}
            .footer {{
                background-color: #020617;
                padding: 25px 30px;
                text-align: center;
                font-size: 11px;
                color: #475569;
                border-top: 1px solid rgba(255,255,255,0.05);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">SMARTY <span>AI</span></div>
                <div class="tagline">{brand_sub}</div>
            </div>
            <div class="content">
                <div class="headline">
                    WELCOME TO THE TEAM, {user_name.upper()}
                </div>
                <div class="badge">calibration successful</div>
                <p>
                    You have unlocked access to the next generation of digital
                    fitness intelligence. Your profile has been initialized
                    and synced safely to our cloud database.
                </p>

                <ul class="feature-list">
                    <li class="feature-item">
                        <span class="feature-title">
                            Cinematic Food Scanner:
                        </span>
                        Snap, compute, and log meals effortlessly
                        with AI vision.
                    </li>
                    <li class="feature-item">
                        <span class="feature-title">
                            Algorithmic Workout Recommender:
                        </span>
                        Every exercise is generated and curated dynamically
                        to match your fitness aims.
                    </li>
                    {
                        (
                            "<li class='feature-item'>"
                            "<span class='feature-title'>"
                            "FemmeCare Cycle Syncing:"
                            "</span> "
                            "Push training load adjustments synced directly "
                            "to cycle and symptom logs."
                            "</li>"
                        )
                        if is_female
                        else ""
                    }
                    <li class="feature-item">
                        <span class="feature-title">Live AI Coaching:</span>
                        A tactical 24/7 assistant analyzing your health
                        vectors in real-time.
                    </li>
                </ul>

                <p>
                    Log in now to complete your fitness onboarding alignment
                    profile.
                </p>

                <a href="http://localhost:5173" class="cta-button">
                    Launch Dashboard
                </a>
            </div>
            <div class="footer">
                &copy; 2026 Smarty AI Inc. All Rights Reserved.<br>
                This is an automated system email. Do not reply directly.
            </div>
        </div>
    </body>
    </html>
    """


def send_welcome_email_async(
    user_email: str, user_name: str, gender: str = "male"
):
    """Internal SMTP send action to be dispatched inside a thread."""
    if not SMTP_HOST or not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning(
            "SMTP settings missing. Welcome email dispatch skipped."
        )
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Welcome to Smarty AI Fitness Intelligence"
        msg["From"] = SMTP_FROM_EMAIL
        msg["To"] = user_email

        html_body = get_welcome_html_template(user_name, gender)
        msg.attach(MIMEText(html_body, "html"))

        # Setup SMTP Connection
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, user_email, msg.as_string())
        server.quit()
        logger.info(f"Welcome email successfully sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to dispatch welcome email: {e}")


def send_welcome_email(
    user_email: str, user_name: str, gender: str = "male"
):
    """Dispatches welcome email asynchronously."""
    email_thread = threading.Thread(
        target=send_welcome_email_async,
        args=(user_email, user_name, gender)
    )
    email_thread.start()


def get_verification_html_template(
    user_name: str, verification_code: str
) -> str:
    """Generate HTML for email verification."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Verify Your Email – Smarty AI</title>
        <style>
            body {{
                font-family: 'Inter', Helvetica, Arial, sans-serif;
                background-color: #020617;
                color: #f1f5f9;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background-color: #0b1329;
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 24px;
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #0f172a, #020617);
                padding: 40px 30px;
                text-align: center;
                border-bottom: 2px solid #10b981;
            }}
            .logo {{
                font-size: 28px;
                font-weight: 900;
                font-style: italic;
                letter-spacing: -0.05em;
                color: #ffffff;
            }}
            .logo span {{
                color: #10b981;
            }}
            .content {{
                padding: 40px 30px;
                line-height: 1.8;
                font-size: 15px;
                color: #cbd5e1;
            }}
            .code-box {{
                background: rgba(16,185,129,0.1);
                border: 2px solid #10b981;
                border-radius: 16px;
                text-align: center;
                padding: 20px;
                margin: 25px 0;
                font-size: 32px;
                font-weight: 900;
                letter-spacing: 0.3em;
                color: #10b981;
            }}
            .footer {{
                background-color: #020617;
                padding: 25px 30px;
                text-align: center;
                font-size: 11px;
                color: #475569;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">SMARTY <span>AI</span></div>
            </div>
            <div class="content">
                <h2 style="color:#fff;margin-top:0">Verify Your Email</h2>
                <p>Hi {user_name},</p>
                <p>
                    Enter this verification code to complete your
                    registration:
                </p>
                <div class="code-box">{verification_code}</div>
                <p style="font-size:12px;color:#64748b">
                    This code expires in 15 minutes. If you didn't create an
                    account, you can safely ignore this email.
                </p>
            </div>
            <div class="footer">
                &copy; 2026 Smarty AI Inc. All Rights Reserved.
            </div>
        </div>
    </body>
    </html>
    """


def send_verification_email_async(
    user_email: str, user_name: str, verification_code: str
):
    """Internal SMTP send for verification email."""
    if not SMTP_HOST or not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning(
            "SMTP settings missing. Verification email skipped. "
            f"Code for {user_email}: {verification_code}"
        )
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Verify Your Email – Smarty AI"
        msg["From"] = SMTP_FROM_EMAIL
        msg["To"] = user_email

        html_body = get_verification_html_template(
            user_name, verification_code
        )
        msg.attach(MIMEText(html_body, "html"))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, user_email, msg.as_string())
        server.quit()
        logger.info(f"Verification email sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")


def send_verification_email(
    user_email: str, user_name: str, verification_code: str
):
    """Dispatches verification email asynchronously."""
    email_thread = threading.Thread(
        target=send_verification_email_async,
        args=(user_email, user_name, verification_code),
    )
    email_thread.start()
