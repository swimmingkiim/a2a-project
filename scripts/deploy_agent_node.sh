#!/bin/bash
set -e

SERVICE_NAME="a2a-agent-node"
REGION="asia-northeast1"
AGENT_DB_INSTANCE="a2a-agent-db"

echo "🚀 Deploying $SERVICE_NAME..."

# Move to root
cd "$(dirname "$0")/.."

# Build
echo "📦 Building..."
gcloud builds submit --config apps/agent-node/cloudbuild.yaml .

# Deploy
echo "🚀 Deploying to Cloud Run..."
echo "🔍 Retrieving Cloud SQL Connection Name for $AGENT_DB_INSTANCE..."
INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe $AGENT_DB_INSTANCE --format='value(connectionName)' 2>/dev/null)

if [ -z "$INSTANCE_CONNECTION_NAME" ]; then
  echo "❌ Error: Could not retrieve connection name for '$AGENT_DB_INSTANCE'."
  echo "Please ensure the instance exists and you have permissions."
  exit 1
fi
echo "✅ Connection Name: $INSTANCE_CONNECTION_NAME"

gcloud run deploy $SERVICE_NAME \
  --image asia-northeast3-docker.pkg.dev/$(gcloud config get-value project)/a2a-repo/a2a-agent-node \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="NODE_ENV=production,INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME,DB_NAME=agent_db,DB_USER=agent_user,DID_NETWORK=base,RPC_URL=https://mainnet.base.org,GRANT_TOKEN_ADDRESS=0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2,CREDENTIAL_VERIFIER_ADDRESS=0xc173A512b3394f6897F9B20c7A411B5247BCeD19,CHAIN_ID=8453" \
  --set-secrets="DB_PASSWORD=DB_PASSWORD:latest,GRANT_PRIVATE_KEY=GRANT_PRIVATE_KEY:latest,VOUCHER_PRIVATE_KEY=VOUCHER_PRIVATE_KEY:latest" \
  --add-cloudsql-instances="$INSTANCE_CONNECTION_NAME"

echo "✅ Agent Node Deployed!"
