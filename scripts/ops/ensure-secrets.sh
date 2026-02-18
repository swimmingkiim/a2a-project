#!/bin/bash
set -e

# ============================================================
# ensure-secrets.sh
# Creates any Google Secret Manager secrets that do not yet exist.
# This script is IDEMPOTENT — safe to run multiple times.
# It never overwrites existing secret values.
# ============================================================

echo "🔐 Ensuring all required secrets exist in Google Secret Manager..."

# List of secrets required by the A2A project.
# Format: SECRET_NAME|DESCRIPTION
REQUIRED_SECRETS=(
  "A2A_PAYMASTER_API_KEY|Paymaster static API key"
  "UPSTREAM_PAYMASTER_URL|Pimlico upstream paymaster URL"
  "PIMLICO_POLICY_ID|Pimlico sponsorship policy ID"
  "TREASURY_ADDRESS|Treasury wallet address for fee collection"
  "PAYMASTER_SIGNER_PRIVATE_KEY|Paymaster signer hot wallet private key"
  "DB_PASSWORD|PostgreSQL database password"
  "GRANT_PRIVATE_KEY|Agent node grant service private key"
  "BASESCAN_API_KEY|Basescan API key for contract verification"
)

created=0
existing=0

for entry in "${REQUIRED_SECRETS[@]}"; do
  IFS='|' read -r secret_name description <<< "$entry"

  if gcloud secrets describe "$secret_name" &>/dev/null; then
    echo "  ✅ $secret_name — already exists"
    ((existing++))
  else
    echo "  🆕 Creating $secret_name ($description)..."
    gcloud secrets create "$secret_name" \
      --replication-policy="automatic" \
      --labels="managed-by=ensure-secrets"

    echo "  ⚠️  $secret_name created but has NO VALUE. Add a version:"
    echo "     echo -n 'YOUR_VALUE' | gcloud secrets versions add $secret_name --data-file=-"
    ((created++))
  fi
done

echo ""
echo "📊 Summary: $existing existing, $created newly created"

if [ "$created" -gt 0 ]; then
  echo ""
  echo "⚠️  WARNING: $created secret(s) were created without values."
  echo "   You must add values before deploying. Example:"
  echo "   echo -n 'your-secret-value' | gcloud secrets versions add SECRET_NAME --data-file=-"
fi

echo "✅ Done."
