#!/usr/bin/env python3
"""Send the email message on standard input (headers, a blank line, the body).

With ALERT_SMTP_HOST set, the message goes to that SMTP server over TLS, logged in as ALERT_SMTP_USER
with ALERT_SMTP_PASSWORD: for example Gmail (smtp.gmail.com, port 587, an app password). Without it,
the message is handed to a sendmail-compatible program (SENDMAIL, default /usr/sbin/sendmail), for
example msmtp-mta. Used by scripts/send_alert.sh; standard library only.

    ALERT_SMTP_HOST      e.g. smtp.gmail.com
    ALERT_SMTP_PORT      587 (STARTTLS, the default) or 465 (TLS from the start)
    ALERT_SMTP_USER      the account, e.g. the Gmail address
    ALERT_SMTP_PASSWORD  its password; for Gmail an app password (the 16 letters, spaces optional)
    ALERT_SMTP_DEBUG     true: print the conversation with the server (not the login) to stderr, for
                         the journal of hysite-alert@test.service
"""
import email
import os
import smtplib
import ssl
import subprocess
import sys


def main() -> None:
    message = email.message_from_string(sys.stdin.read())
    host = os.environ.get("ALERT_SMTP_HOST", "").strip()
    if not host:
        sendmail = os.environ.get("SENDMAIL", "/usr/sbin/sendmail")
        subprocess.run([sendmail, "-t"], input=message.as_bytes(), check=True)
        return
    port = int(os.environ.get("ALERT_SMTP_PORT", "587"))
    user = os.environ.get("ALERT_SMTP_USER", "")
    password = os.environ.get("ALERT_SMTP_PASSWORD", "").replace(" ", "")
    debug = os.environ.get("ALERT_SMTP_DEBUG", "").lower() in ("true", "1", "yes")
    context = ssl.create_default_context()
    if port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=60, context=context)
        server.set_debuglevel(debug)
    else:
        server = smtplib.SMTP(host, port, timeout=60)
        server.set_debuglevel(debug)
        server.ehlo()
        if server.has_extn("starttls"):
            server.starttls(context=context)
            server.ehlo()
        elif user:
            sys.exit(f"{host}:{port} does not offer STARTTLS; the password would be sent in the clear")
    with server:
        if user:
            server.set_debuglevel(0)  # never print the credentials
            server.login(user, password)
            server.set_debuglevel(debug)
        server.send_message(message)


if __name__ == "__main__":
    try:
        main()
    except (OSError, smtplib.SMTPException) as error:
        sys.exit(f"Could not send the email ({os.environ.get('ALERT_SMTP_HOST') or 'sendmail'}): {error}")
