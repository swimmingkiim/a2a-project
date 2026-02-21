# Build Stage
FROM node:20-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y python3 make g++ git

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /app
COPY . .
ENV CI=true
RUN pnpm install
# Build workspace packages first (in dependency order)
RUN npm install -g typescript@5.7.3
RUN tsc --version
RUN cd packages/api-sdk && tsc
# Debug output: Check API-SDK BEFORE other builds fail
RUN ls -R /app/packages/api-sdk/dist
RUN cd packages/trust-sdk && tsc
RUN cd packages/pay-sdk && tsc
# Then build the application
RUN cd apps/agent-node && tsc
RUN ls -R /app/apps/agent-node/dist || echo "MISSING AGENT DIST"

# Runner Stage
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

# Install ClamAV and update virus signatures
RUN apt-get update && apt-get install -y clamav clamav-daemon wget && \
    freshclam && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy built application and dependencies
COPY --from=builder /app /app

# Expose port
EXPOSE 8080

# Add startup debug output. We also need to start the clamav daemon in the background
CMD ["sh", "-c", "service clamav-daemon start & node apps/agent-node/dist/src/index.js"]
