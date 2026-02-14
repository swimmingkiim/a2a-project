#!/bin/bash
set -e

# Configuration
SECRET_NAME="PAYMASTER_SIGNER_PRIVATE_KEY"
SECRET_TREASURY="TREASURY_ADDRESS"

echo "🔄 Rotating Paymaster Credentials..."

# 1. Check Prerequisites
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ node check failed. Please ensure Node.js is installed."
    exit 1
fi

# 2. Generate New Private Key (Locally)
echo "🔐 Generating new Paymaster Signer Key (Hot Wallet)..."
# Use Node.js to generate a random wallet securely
# We run inside apps/paymaster to access 'viem' or 'ethers'
CURRENT_DIR=$(pwd)
cd apps/paymaster

read -r NEW_PRIVATE_KEY NEW_ADDRESS <<< $(node -e "
    try {
        const { generatePrivateKey, privateKeyToAccount } = require('viem/accounts');
        const pk = generatePrivateKey();
        const account = privateKeyToAccount(pk);
        console.log(pk + ' ' + account.address);
    } catch (e) {
        try {
            const { Wallet } = require('ethers');
            const wallet = Wallet.createRandom();
            console.log(wallet.privateKey + ' ' + wallet.address);
        } catch (e2) {
            console.error('❌ Could not find viem or ethers');
            process.exit(1);
        }
    }
")
cd "$CURRENT_DIR"

if [ -z "$NEW_PRIVATE_KEY" ]; then
    echo "❌ Failed to generate key. Ensure dependencies are installed in apps/paymaster."
    exit 1
fi

echo "✅ New Signer Address: $NEW_ADDRESS"
echo "⚠️  IMPORTANT: This new key is being generated LOCALLY and will be pushed directly to Secret Manager."
echo "   It will NOT be saved to any file on disk."

# 3. Update PAYMASTER_SIGNER_PRIVATE_KEY in Secret Manager
echo "📤 Updating Google Cloud Secret: $SECRET_NAME..."
echo -n "$NEW_PRIVATE_KEY" | gcloud secrets versions add $SECRET_NAME --data-file=-
echo "✅ Secret updated."

# 4. Prompt for Treasury Address (Cold Wallet)
echo ""
echo "💰 Treasury Address (Admin/Cold Wallet)"
echo "   Current Secret: $SECRET_TREASURY"
echo "   This should be your Ledger/Safe address that collects fees."
read -p "Enter Treasury Address (leave empty to keep existing): " TREASURY_INPUT

if [ -n "$TREASURY_INPUT" ]; then
    echo -n "$TREASURY_INPUT" | gcloud secrets versions add $SECRET_TREASURY --data-file=-
    echo "✅ Treasury Secret updated."
else
    echo "   Skipping Treasury update."
fi

# 5. Summary & Instructions
echo ""
echo "========================================================"
echo "🎉 Rotation Complete!"
echo "========================================================"
echo "1. New Signer Address: $NEW_ADDRESS"
echo "   -> [ACTION REQUIRED] Fund this address with 0.05 ETH on Base Mainnet."
echo "   -> [ACTION REQUIRED] If you have a custom Paymaster Contract, register this address as a Valid Signer."
echo ""
echo "2. Treasury Address: ${TREASURY_INPUT:-"(Unchanged)"}"
echo ""
echo "3. Next Steps:"
echo "   Run './scripts/deploy_paymaster.sh' to redeploy the service with new secrets."
echo "========================================================"
