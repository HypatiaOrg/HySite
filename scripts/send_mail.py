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
    ALERT_SMTP_DEBUG     true: print the conversation with the server to stderr (the journal of
                         hysite-alert@test.service); what the client sends at login is masked
    ALERT_SMTP_IPV4      true: connect to the name's IPv4 address only
"""
import email
import email.message
import os
import smtplib
import socket
import ssl
import subprocess
import sys


def connect_ipv4(self, host, port, timeout):
    """smtplib's socket, but to the name's IPv4 address; the name itself still goes into EHLO and TLS."""
    family, kind, proto, _, address = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)[0]
    sock = socket.socket(family, kind, proto)
    sock.settimeout(timeout)
    sock.connect(address)
    return sock


def print_debug_masked(self, *args):
    """smtplib's debug output, with the credentials masked: the line the client sends at login."""
    text = " ".join(str(arg) for arg in args)
    if self.in_login and text.startswith("send:"):
        text = "send: (login, hidden)"
    print(text, file=sys.stderr)


def send(message: email.message.Message) -> None:
    """Send one message with the ALERT_SMTP_* account, or sendmail without one."""
    host = os.environ.get("ALERT_SMTP_HOST", "").strip()
    if not host:
        sendmail = os.environ.get("SENDMAIL", "/usr/sbin/sendmail")
        subprocess.run([sendmail, "-t"], input=message.as_bytes(), check=True)
        return
    port = int(os.environ.get("ALERT_SMTP_PORT", "587"))
    user = os.environ.get("ALERT_SMTP_USER", "")
    password = os.environ.get("ALERT_SMTP_PASSWORD", "").replace(" ", "")
    debug = os.environ.get("ALERT_SMTP_DEBUG", "").lower() in ("true", "1", "yes")
    ipv4 = os.environ.get("ALERT_SMTP_IPV4", "").lower() in ("true", "1", "yes")
    context = ssl.create_default_context()
    if port == 465:
        class client(smtplib.SMTP_SSL):
            in_login = False
            _print_debug = print_debug_masked
            if ipv4:
                def _get_socket(self, host, port, timeout):
                    return context.wrap_socket(connect_ipv4(self, host, port, timeout), server_hostname=host)
        server = client(host, port, timeout=60, context=context)
        server.set_debuglevel(debug)
    else:
        class client(smtplib.SMTP):
            in_login = False
            _print_debug = print_debug_masked
            if ipv4:
                _get_socket = connect_ipv4
        server = client(host, port, timeout=60)
        server.set_debuglevel(debug)
        server.ehlo()
        if server.has_extn("starttls"):
            server.starttls(context=context)
            server.ehlo()
        elif user:
            sys.exit(f"{host}:{port} does not offer STARTTLS; the password would be sent in the clear")
    with server:
        if user:
            server.in_login = True
            # one AUTH PLAIN, not smtplib's login(): that one retries with another method after a
            # rejection, and a server that hangs up after rejecting (Gmail) then hides its reply
            server.user, server.password = user, password
            server.auth("PLAIN", server.auth_plain, initial_response_ok=True)
            server.in_login = False
        server.send_message(message)


def main() -> None:
    send(email.message_from_string(sys.stdin.read()))


if __name__ == "__main__":
    try:
        main()
    except (OSError, smtplib.SMTPException) as error:
        sys.exit(f"Could not send the email ({os.environ.get('ALERT_SMTP_HOST') or 'sendmail'}): {error}")
