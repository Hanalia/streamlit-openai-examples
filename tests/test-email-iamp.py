from dotenv import load_dotenv
import os
import imaplib
import email
from email.header import decode_header

load_dotenv()


# Fetch credentials from environment variables
email_id = os.getenv("NAVER_EMAIL")
email_password = os.getenv("NAVER_PASSWORD")


def decode_mime_words(encoded_string):
    decoded_words = decode_header(encoded_string)
    decoded_string = ""
    for content, charset in decoded_words:
        if charset:
            decoded_string += content.decode(charset)
        else:
            decoded_string += content
    return decoded_string


try:
    # Connect to the mail server
    mail = imaplib.IMAP4_SSL("imap.naver.com")
    mail.login(email_id, email_password)
    mail.select("inbox")  # Select the inbox folder

    # Search for all emails in the inbox
    result, data = mail.search(None, "ALL")
    mail_ids = data[0].split()

    # Loop over each email ID to fetch the email
    for mail_id in mail_ids:
        result, data = mail.fetch(mail_id, "(RFC822)")  # Fetch the email data
        raw_email = data[0][1]  # Extract the email bytes
        msg = email.message_from_bytes(
            raw_email
        )  # Parse the email bytes into a message object

        # Decode the MIME-encoded parts of the headers
        from_ = decode_mime_words(msg.get("From"))
        to = decode_mime_words(msg.get("To"))
        subject = decode_mime_words(msg.get("Subject"))
        date = msg.get("Date")

        # Extract and decode the email body
        if msg.is_multipart():
            body = []
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body.append(part.get_payload(decode=True).decode())
            body = "\n".join(body)
        else:
            body = msg.get_payload(decode=True).decode()

        # Print the email details
        print(f"From: {from_}")
        print(f"To: {to}")
        print(f"Subject: {subject}")
        print(f"Date: {date}")
        print(f"Body: {body[:500]}")  # Print the first 500 characters of the body
        print("\n---\n")
except Exception as e:
    print(e)
import smtplib
from email.message import EmailMessage
import imaplib
import email


def connect_imap(server, username, password, mailbox="INBOX"):
    """Connect to an IMAP server and select a mailbox."""
    imap = imaplib.IMAP4_SSL(server)
    imap.login(username, password)
    imap.select(mailbox)
    return imap


def search_emails(imap, subject):
    """Search for emails by subject."""
    result, data = imap.search(None, "SUBJECT", subject)
    return data[0].split()


def fetch_email(imap, email_id):
    """Fetch an email by its ID."""
    result, data = imap.fetch(email_id, "(RFC822)")
    return email.message_from_bytes(data[0][1])


def create_reply(original_email, from_addr, reply_message):
    """Create a reply email message."""
    reply = EmailMessage()
    reply["From"] = from_addr
    reply["To"] = original_email["From"]
    reply["Subject"] = "Re: " + original_email["Subject"]
    reply["In-Reply-To"] = original_email["Message-ID"]
    reply["References"] = original_email["Message-ID"]
    reply.set_content(reply_message)
    return reply


def send_email(smtp_server, port, username, password, message):
    """Send an email using SMTP."""
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(message)
        print("Reply sent successfully")


# Configuration
imap_server = "imap.gmail.com"
smtp_server = "smtp.gmail.com"
port = 587
