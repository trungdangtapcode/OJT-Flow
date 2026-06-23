#!/usr/bin/env bash
# Populate the Keycloak "google" identity provider with the Google OAuth client
# credentials from the environment. Keycloak's realm import does not reliably
# substitute ${env.*} placeholders for IdP secrets, so this idempotent step sets
# them through the Admin REST API after Keycloak is up.
#
# Usage (creds are read from the environment or the repo .env):
#   OJT_GOOGLE_CLIENT_ID=... OJT_GOOGLE_CLIENT_SECRET=... \
#     bash infra/keycloak/configure-google-idp.sh
#
# Also remember to add this redirect URI to the Google OAuth client in Google
# Cloud Console (APIs & Services > Credentials):
#   ${KC_PUBLIC_URL}/realms/${REALM}/broker/google/endpoint
set -euo pipefail

KC_PUBLIC_URL="${OJT_KEYCLOAK_BASE_URL:-http://localhost:18080}"
REALM="${OJT_KEYCLOAK_REALM:-ojtflow}"
ADMIN_USER="${OJT_KEYCLOAK_ADMIN_USERNAME:-admin}"
ADMIN_PASS="${OJT_KEYCLOAK_ADMIN_PASSWORD:-admin}"
CLIENT_ID="${OJT_GOOGLE_CLIENT_ID:-}"
CLIENT_SECRET="${OJT_GOOGLE_CLIENT_SECRET:-}"

# Fall back to repo .env when the variables are not already exported.
ENV_FILE="$(cd "$(dirname "$0")/../.." && pwd)/.env"
if [[ -z "${CLIENT_ID}" && -f "${ENV_FILE}" ]]; then
  CLIENT_ID="$(grep -E '^OJT_GOOGLE_CLIENT_ID=' "${ENV_FILE}" | head -1 | cut -d= -f2-)"
fi
if [[ -z "${CLIENT_SECRET}" && -f "${ENV_FILE}" ]]; then
  CLIENT_SECRET="$(grep -E '^OJT_GOOGLE_CLIENT_SECRET=' "${ENV_FILE}" | head -1 | cut -d= -f2-)"
fi

if [[ -z "${CLIENT_ID}" || -z "${CLIENT_SECRET}" ]]; then
  echo "OJT_GOOGLE_CLIENT_ID / OJT_GOOGLE_CLIENT_SECRET are not set; skipping." >&2
  exit 0
fi

TOKEN="$(curl -fsS -X POST "${KC_PUBLIC_URL}/realms/master/protocol/openid-connect/token" \
  -d grant_type=password -d client_id=admin-cli \
  -d "username=${ADMIN_USER}" -d "password=${ADMIN_PASS}" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')"

curl -fsS -X PUT \
  "${KC_PUBLIC_URL}/admin/realms/${REALM}/identity-provider/instances/google" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$(cat <<JSON
{
  "alias": "google",
  "displayName": "Google",
  "providerId": "google",
  "enabled": true,
  "trustEmail": true,
  "config": {
    "clientId": "${CLIENT_ID}",
    "clientSecret": "${CLIENT_SECRET}",
    "defaultScope": "openid email profile",
    "syncMode": "IMPORT",
    "useJwksUrl": "true"
  }
}
JSON
)"

echo "Configured Google identity provider on realm '${REALM}'."
echo "Ensure this redirect URI is authorized in Google Cloud Console:"
echo "  ${KC_PUBLIC_URL}/realms/${REALM}/broker/google/endpoint"
