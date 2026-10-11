#!/bin/sh
# Bridge MCP over stdio to the hosted Easy2257 server.
#
# The server lives at https://easy2257.com/api/mcp and takes the account's
# MCP key as a bearer token. This container only carries that key from the
# EASY2257_API_KEY environment variable into the Authorization header and
# relays the stdio stream, for MCP clients that cannot set a header
# themselves. Nothing is served from here.
set -eu

if [ -z "${EASY2257_API_KEY:-}" ]; then
  echo "easy2257-mcp: EASY2257_API_KEY is not set. Create a key under Account, then MCP Keys at https://easy2257.com/profile/account/api-keys and pass it with -e EASY2257_API_KEY=..." >&2
  exit 2
fi

case "$EASY2257_API_KEY" in
  ez_mcp_*) ;;
  *) echo "easy2257-mcp: EASY2257_API_KEY does not look like an Easy2257 MCP key (they start with ez_mcp_)." >&2; exit 2 ;;
esac

exec /app/node_modules/.bin/mcp-remote "${EASY2257_MCP_URL:-https://easy2257.com/api/mcp}" \
  --transport http-only \
  --header "Authorization: Bearer ${EASY2257_API_KEY}" \
  "$@"
