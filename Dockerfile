# agaveis/easy2257-mcp: a stdio bridge to the hosted Easy2257 MCP server.
#
# The MCP server itself runs at https://easy2257.com/api/mcp and is operated
# by Easy2257. This image contains no server code: it runs the official
# mcp-remote package, which speaks MCP over stdio to the client and forwards
# every request to the hosted endpoint with the account's key as a bearer
# token. Use it from MCP clients that cannot send a header on their own.
#
# node:22-alpine, read 2026-10-11: Node v22.23.3, npm 10.9.9, Alpine 3.24.2.
# Pinned by the multi-arch index digest so every build is the same image.
FROM node:22-alpine@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402

WORKDIR /app

# package-lock.json pins mcp-remote 0.14.3 and every transitive package;
# npm ci refuses to drift from it. --ignore-scripts: nothing here needs a
# lifecycle script, so none runs.
COPY bridge/package.json bridge/package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund \
    && npm cache clean --force

COPY bridge/entrypoint.sh /app/entrypoint.sh
RUN chmod 0755 /app/entrypoint.sh

# mcp-remote keeps its own small state under $HOME/.mcp-auth. The node user
# owns its home directory, so no root is needed at run time.
USER node
ENV HOME=/home/node

LABEL org.opencontainers.image.title="easy2257-mcp" \
      org.opencontainers.image.description="stdio bridge to the hosted Easy2257 MCP server (read-only 18 U.S.C. 2257 compliance records)" \
      org.opencontainers.image.url="https://easy2257.com/ai-assistant" \
      org.opencontainers.image.source="https://github.com/Agaveis/easy2257-mcp" \
      org.opencontainers.image.vendor="AgaveIS" \
      org.opencontainers.image.licenses="MIT"

ENTRYPOINT ["/app/entrypoint.sh"]
