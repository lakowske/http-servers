#!/bin/bash
service rsyslog start
service postfix start
service dovecot start
# Create new mail.log if it doesn't exist
touch /var/log/mail.log
tail -f /var/log/mail.log