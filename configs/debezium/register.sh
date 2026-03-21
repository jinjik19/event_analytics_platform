#!/usr/bin/env bash
set -euo pipefail

DEBEZIUM_HOST="${DEBEZIUM_HOST:-localhost}"
DEBEZIUM_PORT="${DEBEZIUM_PORT:-8083}"
CONNECTOR_FILE="$(dirname "$0")/connector-postgres.json"
CONNECTOR_NAME="postgres-cdc"

echo "Waiting for Debezium Connect at http://${DEBEZIUM_HOST}:${DEBEZIUM_PORT} ..."
until curl -sf "http://${DEBEZIUM_HOST}:${DEBEZIUM_PORT}/connectors" > /dev/null; do
  printf '.'
  sleep 3
done
echo ""

HTTP_STATUS=$(curl -so /dev/null -w "%{http_code}" \
  "http://${DEBEZIUM_HOST}:${DEBEZIUM_PORT}/connectors/${CONNECTOR_NAME}")

if [ "${HTTP_STATUS}" = "200" ]; then
  echo "Connector '${CONNECTOR_NAME}' already exists — updating config..."
  curl -sf \
    -X PUT \
    -H "Content-Type: application/json" \
    --data "$(python3 -c "import json,sys; d=json.load(open('${CONNECTOR_FILE}')); print(json.dumps(d['config']))")" \
    "http://${DEBEZIUM_HOST}:${DEBEZIUM_PORT}/connectors/${CONNECTOR_NAME}/config"
else
  echo "Registering connector '${CONNECTOR_NAME}' ..."
  curl -sf \
    -X POST \
    -H "Content-Type: application/json" \
    --data @"${CONNECTOR_FILE}" \
    "http://${DEBEZIUM_HOST}:${DEBEZIUM_PORT}/connectors"
fi

echo ""
echo "Done. Check status:"
echo "  curl -s http://${DEBEZIUM_HOST}:${DEBEZIUM_PORT}/connectors/${CONNECTOR_NAME}/status | python3 -m json.tool"
