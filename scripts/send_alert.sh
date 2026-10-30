#!/bin/bash
# Email the recent log of a failed systemd unit. Started by hysite-alert@.service when
# hysite-update.service fails (OnFailure=), with the failed unit's name as $1.
#
# Settings from /etc/hysite/update.env:
#   ALERT_EMAIL        where to send (required); several addresses separated by commas
#   ALERT_FROM         sender address (default: hysite@<hostname>; Gmail replaces it with the account's)
#   ALERT_SMTP_*       the SMTP server and account that sends it (scripts/send_mail.py); without
#                      ALERT_SMTP_HOST, a sendmail program is used (SENDMAIL, default /usr/sbin/sendmail)
#
# To test the settings, start the alert unit with the name "test" and read its log:
#   sudo systemctl start hysite-alert@test.service && journalctl --unit hysite-alert@test.service --invocation 0
set -uo pipefail
unit=${1:?usage: send_alert.sh <unit name>}
: "${ALERT_EMAIL:?ALERT_EMAIL is not set in /etc/hysite/update.env}"
host=$(hostname)
send() { python3 "$(dirname "$0")/send_mail.py"; }
if [ "$unit" = test ]; then
    {
        echo "To: $ALERT_EMAIL"
        echo "From: ${ALERT_FROM:-hysite@$host}"
        echo "Subject: [HySite] test email from $host"
        echo "Content-Type: text/plain; charset=UTF-8"
        echo
        echo "The HySite update job on $host can send email. Sent $(date -u '+%Y-%m-%d %H:%M UTC')."
    } | send && echo "Test email sent to $ALERT_EMAIL"
    exit
fi
status=$(grep -oE 'Status: [a-z_]+ - .*' <(journalctl --unit "$unit" --invocation 0 --no-pager --output cat 2> /dev/null) \
    | tail -n 1)
{
    echo "To: $ALERT_EMAIL"
    echo "From: ${ALERT_FROM:-hysite@$host}"
    echo "Subject: [HySite] $unit failed on $host"
    echo "Content-Type: text/plain; charset=UTF-8"
    echo
    echo "$unit failed on $host at $(date -u '+%Y-%m-%d %H:%M UTC')."
    echo "${status:-See the log below.}"
    echo
    echo "The run is recorded in the hysite_ops.deployments collection. On the server:"
    echo "    systemctl status $unit"
    echo "    journalctl --unit $unit --invocation 0"
    echo
    echo "---- last 150 log lines ----"
    journalctl --unit "$unit" --invocation 0 --no-pager --output short-iso --lines 150
} | send
