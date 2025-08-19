import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

# List of multiple recipient emails
RECIPIENT_EMAILS = [
    "rachana@klesnc.edu.in",   
    "pavanathyadka@gmail.com",
    "nariyangarachana@gmail.com"
]

def send_email(report_text, chart_path, pdf_path):
    """
    Sends an email with the sales report text, PDF report, and chart image attached.
    Uses Gmail SMTP with credentials stored in environment variables.
    Sends email to multiple recipients defined inside this script.
    """

    user = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_PASS")

    if not user or not password:
        raise ValueError("GMAIL_USER and GMAIL_PASS must be set in your .env file")

    msg = EmailMessage()
    msg["Subject"] = "Daily Sales Report"
    msg["From"] = user
    msg["To"] = ", ".join(RECIPIENT_EMAILS)  # Multiple recipients
    msg.set_content(report_text)

    # Attach PDF report file
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        msg.add_attachment(pdf_data, maintype="application", subtype="pdf", filename=os.path.basename(pdf_path))
    else:
        raise FileNotFoundError(f"PDF report file not found: {pdf_path}")

    # Attach chart image file (PNG)
    if os.path.exists(chart_path):
        with open(chart_path, "rb") as f:
            img_data = f.read()
        msg.add_attachment(img_data, maintype="image", subtype="png", filename=os.path.basename(chart_path))
    else:
        raise FileNotFoundError(f"Chart image file not found: {chart_path}")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
        return True, f"Email sent successfully!"
    except Exception as e:
        return False, f"Failed to send email: {e}"