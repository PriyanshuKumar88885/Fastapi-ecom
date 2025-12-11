#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Starting Keycloak from $ROOT_DIR"

docker compose -f "$ROOT_DIR/docker-compose.yml" up -d

echo "Waiting for Keycloak to become available on http://localhost:8080 ..."
for i in {1..30}; do
	if curl -fsS http://localhost:8080/ > /dev/null 2>&1; then
		echo "Keycloak is up"
		break
	fi
	sleep 2
done

echo "Realm import directory: $ROOT_DIR/realm-import"
echo "Admin console: http://localhost:8080/ (user: admin password: admin)"
echo "Example realm imported: ecom"
echo "JWKS URL: http://localhost:8080/realms/ecom/protocol/openid-connect/certs"

exit 0
