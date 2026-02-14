#!/bin/bash
set -e

# Configuration
SERVICE_NAME="a2a-paymaster"
REGION="asia-northeast1"
SECRET_API_KEY="A2A_PAYMASTER_API_KEY"
SECRET_UPSTREAM_URL="UPSTREAM_PAYMASTER_URL"

echo "🚀 Starting Deployment for $SERVICE_NAME..."

# Check gcloud
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
    exit 1
fi

# Enable Secret Manager API
echo "🔌 Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

# Function to create or update secret
create_secret() {
    local secret_name=$1
    local prompt_text=$2
    local auto_generate=$3
    
    echo "checking secret $secret_name..."
    local exists=false
    if gcloud secrets describe $secret_name &> /dev/null; then
        exists=true
        echo "✅ Secret $secret_name already exists."
    else
        echo "creating secret $secret_name..."
        gcloud secrets create $secret_name --replication-policy="automatic"
    fi

    # If it exists, we skip the prompt unless user forces it (not implemented here, keeping it simple for automation)
    # To re-set a secret, the user should delete it or we add a --force flag later.
    if [ "$exists" == "true" ]; then
        echo "   Skipping input for existing secret. (To update, delete the secret or run update manually)"
        return
    fi

    echo "$prompt_text"
    echo "Enter value (leave empty to generate/skip if optional):"
    read -s secret_value
    echo "" # Newline after silent input
    # Ensure no echoing of secret value
    if [ -n "$secret_value" ]; then
        echo "   [Input received]"
    fi

    # Auto-generate if requested and input is empty
    if [ -z "$secret_value" ] && [ "$auto_generate" == "true" ]; then
             echo "Generating a strong random API Key..."
             secret_value=$(openssl rand -hex 32)
             echo "🔑 Generated Key: $secret_value"
             echo "PLEASE SAVE THIS KEY NOW!"
    fi

    if [ -n "$secret_value" ]; then
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=-
        echo "✅ Secret $secret_name updated."
    else
        echo "❌ Error: No value provided for new secret $secret_name."
        exit 1
    fi
}

# 1. A2A Paymaster API Key
create_secret $SECRET_API_KEY "Enter A2A_PAYMASTER_API_KEY (leave empty to generate/keep existing)" "true"

# 2. Upstream Paymaster URL (Pimlico)
# User request: "In Pimlico, the RPC URL is available next to the API key. I want to be able to just copy and paste it after selecting Base."
create_secret $SECRET_UPSTREAM_URL "Enter Pimlico Paymaster URL (Copy full URL from Dashboard > Chain > Base)" "false"


# 2b. Pimlico Sponsorship Policy ID (Optional but recommended for Mainnet)
SECRET_PIMLICO_POLICY_ID="PIMLICO_POLICY_ID"
create_secret $SECRET_PIMLICO_POLICY_ID "Enter Pimlico Sponsorship Policy ID (e.g. sp_...) (leave empty if not using policy)" "false"

# 3. RPC URL Configuration
# User request: "And also make it so I can just copy and paste the RPC URLs related to this API key."
echo "🌐 Configuring RPC URL..."
read -p "Enter Base RPC URL (e.g. Alchemy/Infura full URL) (leave empty to keep default/existing): " RPC_INPUT

RPC_URL="https://mainnet.base.org" # Default

if [ -n "$RPC_INPUT" ]; then
    RPC_URL="$RPC_INPUT"
    echo "✅ Using New RPC URL: $RPC_URL"
else
    # If empty, we can't easily know the "existing" one from Cloud Run without querying it.
    # But for a deploy script, "existing" usually implies "don't change env var".
    # However, gcloud run deploy --set-env-vars OVERWRITES.
    # So we must provide a value.
    # Strategy: Warn user that default will be used if they don't provide one, unless we fetch current.
    # For now, let's just stick to the Default Public Node fallback as "Existing" isn't easily stateful here without complex logic.
    echo "⚠️  Input empty. Using Default Public RPC URL: $RPC_URL" 
fi

# 4. Treasury Address (Secret)
SECRET_TREASURY_ADDRESS="TREASURY_ADDRESS"
echo "💰 Configuring Treasury Address..."
create_secret $SECRET_TREASURY_ADDRESS "Enter Treasury Address (Wallet to collect fees) (leave empty to keep existing)" "false"

# 4b. Paymaster Signer Private Key (Secret)
SECRET_PAYMASTER_SIGNER="PAYMASTER_SIGNER_PRIVATE_KEY"
echo "🔐 Configuring Paymaster Signer..."
create_secret $SECRET_PAYMASTER_SIGNER "Enter Paymaster Signer Private Key (leave empty to keep existing)" "false"


# 5. Database Configuration
echo "🗄️  Configuring Database..."
INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe a2a-paymaster-db --format='value(connectionName)' 2>/dev/null || echo "")

if [ -z "$INSTANCE_CONNECTION_NAME" ]; then
    echo "❌ Error: Cloud SQL instance 'a2a-paymaster-db' not found!"
    echo "   The Paymaster service requires a database connection."
    echo "   Please create the database instance first."
    exit 1
else
    echo "✅ Found Cloud SQL Instance: $INSTANCE_CONNECTION_NAME"
    DB_USER="paymaster_admin"
    DB_NAME="paymaster_db"
    
    # Ensure DB_PASSWORD secret exists
    if ! gcloud secrets describe DB_PASSWORD &> /dev/null; then
        echo "❌ Secret DB_PASSWORD not found. Please run setup-cloud-sql.sh first."
        exit 1
    fi

    DB_ENV_VARS=",DB_USER=$DB_USER,DB_NAME=$DB_NAME,DB_HOST=/cloudsql/$INSTANCE_CONNECTION_NAME,INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME"
    DB_SECRET_FLAGS=",DB_PASS=DB_PASSWORD:latest"
    CLOUDSQL_FLAGS="--add-cloudsql-instances=$INSTANCE_CONNECTION_NAME"
fi

# Deploy
echo "🚀 Building Container..."

# Move to root directory
cd "$(dirname "$0")/.."

# Submit build from root context using cloudbuild.yaml
gcloud builds submit --config apps/paymaster/cloudbuild.yaml .

echo "🚀 Deploying to Cloud Run..."

# Production environment variables
DAIM_TOKEN_ADDRESS="0x1F478c3F6a09c3820baBd3f6DCD8bEA4eE5dc806"
USDC_TOKEN_ADDRESS="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # Base Mainnet USDC
FEE_AMOUNT="100000"  # 0.1 USDC
ETH_PRICE_USD="2500"
NODE_ENV="production"

gcloud run deploy $SERVICE_NAME \
  --image asia-northeast3-docker.pkg.dev/$(gcloud config get-value project)/a2a-repo/a2a-paymaster \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="NODE_ENV=$NODE_ENV,RPC_URL=$RPC_URL,MARKUP_RATE=1.5,DAIM_TOKEN_ADDRESS=$DAIM_TOKEN_ADDRESS,FEE_TOKEN_ADDRESS=$USDC_TOKEN_ADDRESS,FEE_AMOUNT=$FEE_AMOUNT,ETH_PRICE_USD=$ETH_PRICE_USD,DISABLE_PAYMASTER=false,MIN_SIGNER_BALANCE_ETH=0.01$DB_ENV_VARS" \
  --set-secrets="$SECRET_API_KEY=$SECRET_API_KEY:latest,$SECRET_UPSTREAM_URL=$SECRET_UPSTREAM_URL:latest,$SECRET_PIMLICO_POLICY_ID=$SECRET_PIMLICO_POLICY_ID:latest,$SECRET_TREASURY_ADDRESS=$SECRET_TREASURY_ADDRESS:latest,$SECRET_PAYMASTER_SIGNER=$SECRET_PAYMASTER_SIGNER:latest$DB_SECRET_FLAGS" \
  $CLOUDSQL_FLAGS


echo "✅ Deployment Complete!"
