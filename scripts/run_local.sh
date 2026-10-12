#!/bin/bash
# Run the whole app locally: DynamoDB Local in Docker, the tables, and Flask.
#
# Usage, from the repository root: scripts/run_local.sh
# Press Ctrl+C to stop the app; DynamoDB Local stops too if this script started it.
# Data is kept in db/, so it survives restarts.

set -euo pipefail

CONTAINER=volunteer-signup-dynamodb
PYTHON=.venv/bin/python

cd "$(dirname "$0")/.."

if [ ! -x "$PYTHON" ]; then
    echo "Missing .venv. Set it up first (see docs/development.md)." >&2
    exit 1
fi

if [ ! -f .env ]; then
    cp config/example.env .env
    echo "Created .env from config/example.env"
fi

# Reuse DynamoDB Local if it is already running (for example, the JAR).
if curl -s -o /dev/null http://127.0.0.1:8000; then
    echo "Using the DynamoDB Local already running on port 8000"
else
    mkdir -p db
    docker run -d --rm --name "$CONTAINER" -p 127.0.0.1:8000:8000 \
        -v "$PWD/db:/home/dynamodblocal/db" \
        amazon/dynamodb-local -jar DynamoDBLocal.jar -sharedDb -dbPath ./db >/dev/null
    trap 'docker stop "$CONTAINER" >/dev/null' EXIT
    echo "Started DynamoDB Local in Docker"
fi

"$PYTHON" scripts/wait_for_dynamodb.py
"$PYTHON" scripts/create_tables.py

echo "App: http://127.0.0.1:5000"
"$PYTHON" -m volunteer_signup.app
