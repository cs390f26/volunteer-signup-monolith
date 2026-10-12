#!/bin/bash
# EC2 user-data script for the Volunteer Signup monolith on Amazon Linux 2023.
#
# Installs the packages, application code, configuration, DynamoDB Local, and
# systemd services, then creates the DynamoDB tables. Cloud-init runs it once
# as root on first boot; output goes to /var/log/cloud-init-output.log.

# Exit on error, undefined variable, or failure in a pipeline.
set -euo pipefail

REPO_URL="https://github.com/cs390f26/volunteer-signup-monolith.git"
APP_USER=ec2-user
APP_DIR=/home/$APP_USER/volunteer-signup-monolith
DYNAMODB_ZIP_URL="https://s3.us-west-2.amazonaws.com/dynamodb-local/v2.x/dynamodb_local_latest.zip"

# --- Packages ---------------------------------------------------------------
dnf install -y java-17-amazon-corretto-headless python3.12 git unzip

# --- Application code and configuration --------------------------------------
git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR"

python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .

# DynamoDB Local accepts any credentials, so the example values are enough.
cp config/example.env .env

# --- DynamoDB Local ----------------------------------------------------------
# The JAR and its data file both live in db/, which is gitignored.
mkdir -p db
curl -fsSL -o /tmp/dynamodb_local.zip "$DYNAMODB_ZIP_URL"
unzip -o /tmp/dynamodb_local.zip -d db
rm -f /tmp/dynamodb_local.zip

# Everything above ran as root; the services run as ec2-user.
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# --- Services and tables -----------------------------------------------------
cp deploy/dynamodb-local.service deploy/volunteer-signup.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now dynamodb-local.service

.venv/bin/python scripts/wait_for_dynamodb.py
.venv/bin/python scripts/create_tables.py

systemctl enable --now volunteer-signup.service
