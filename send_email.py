import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
FILE_PATH = "content.txt"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Retrieve secrets from environment variables
sender_email = os.environ.get("EMAIL_USER")
password = os.environ.get("EMAIL_PASS")
recipient_email = os.environ.get("RECIPIENT_EMAIL")

# 1. Validate environment variables
if not all([sender_email, password, recipient_email]):
    print("Error: Missing required environment variables (EMAIL_USER, EMAIL_PASS, RECIPIENT_EMAIL).")
    sys.exit(1)

# 2. Validate and read the text file
if not os.path.exists(FILE_PATH):
    print(f"Error: File '{FILE_PATH}' does not exist.")
    sys.exit(1)

try:
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        file_content = f.read().strip()
    
    if not file_content:
        print(f"Warning: '{FILE_PATH}' is empty. Proceeding with empty body.")
except Exception as e:
    print(f"Error reading file '{FILE_PATH}': {e}")
    sys.exit(1)

# 3. Construct the email
msg = MIMEMultipart()
msg["From"] = sender_email
msg["To"] = recipient_email
msg["Subject"] = "Automated Email: Repository File Content"

msg.attach(MIMEText(file_content, "plain", "utf-8"))

# 4. Connect to SMTP server and send email
try:
    print("Connecting to SMTP server...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    
    print("Logging in...")
    server.login(sender_email, password)
    
    print("Sending email...")
    server.sendmail(sender_email, recipient_email, msg.as_string())
    server.quit()
    
    print("Success: Email delivered successfully!")
except Exception as e:
    print(f"Error sending email: {e}")
    sys.exit(1)
