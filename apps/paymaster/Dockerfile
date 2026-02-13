FROM node:20-alpine AS builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/paymaster/package.json ./apps/paymaster/

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY apps/paymaster ./apps/paymaster
COPY tsconfig.json ./

# Build the codebase
WORKDIR /app/apps/paymaster
RUN pnpm build

# Deploy the specific package to a separate directory with production dependencies
RUN pnpm --filter paymaster-service --prod deploy /prod/paymaster --legacy

# Final implementation image
FROM node:20-alpine
WORKDIR /app

# Copy the deployed dependencies and package.json
COPY --from=builder /prod/paymaster ./

# Copy the built artifacts (dist) from the builder
COPY --from=builder /app/apps/paymaster/dist ./dist

ENV PORT=8080
EXPOSE 8080

CMD ["node", "dist/index.js"]
