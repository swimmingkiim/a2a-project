#!/bin/bash
set -e

SERVICE_NAME="a2a-agent-node"
REGION="asia-northeast1"

echo "🚀 Deploying $SERVICE_NAME..."

# Move to root
cd "$(dirname "$0")/.."

# Build
echo "📦 Building..."
gcloud builds submit --config apps/agent-node/cloudbuild.yaml .

# Deploy
echo "🚀 Deploying to Cloud Run..."
INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe a2a-paymaster-db --format='value(connectionName)' 2>/dev/null || echo "")

# Shared Secrets
# Assuming DB secrets are already set from Paymaster setup
# agent-db-password might be separate or same as paymaster depending on setup.
# Let's use the Paymaster existing infrastructure for now as they share the DB instance in this mono-repo setup usually.
# However, agent-node usually needs its own DB user/pass.
# Based on previous context, we'll try to use existing secrets if possible.

# For now, let's assume we use the same DB instance but maybe different DB name?
# agent-node index.ts checks for DB_HOST or INSTANCE_CONNECTION_NAME.

# We will use the same SQL instance.
# We need to ensure secrets exist.

gcloud run deploy $SERVICE_NAME \
  --image asia-northeast3-docker.pkg.dev/$(gcloud config get-value project)/a2a-repo/a2a-agent-node \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="NODE_ENV=production,INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME,DB_NAME=paymaster_db,DB_USER=paymaster_admin,DID_NETWORK=base,RPC_URL=https://mainnet.base.org" \
  --set-secrets="DB_PASSWORD=DB_PASSWORD:latest,AGENT_SECRET_KEY=agent-secret-key:latest" \
  --add-cloudsql-instances="$INSTANCE_CONNECTION_NAME"

echo "✅ Agent Node Deployed!"
