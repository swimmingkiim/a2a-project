#!/bin/bash
set -e

echo "🏛️  Project A2A: Genesis Protocol Sequence Initiated"
echo "==================================================="

# 0. Check for directory
if [ ! -d "packages/contracts" ]; then
    echo "❌ Error: Please run this script from the project root."
    exit 1
fi

cd packages/contracts

# 1. Install Dependencies
echo "\n📦 Installing Dependencies..."
pnpm install

# 2. Compile Contracts
echo "\n🔨 Compiling Contracts..."
npx hardhat compile

# 3. Run Security Tests
echo "\n🧪 Running Governance Security Tests..."
npx hardhat test test/Governance.test.ts

# 4. Deploy Genesis (Localhost for demo, change network flag for production)
echo "\n🚀 Starting Genesis Deployment..."
# Check if genesis-keys already exist to warn user
if [ -d "../../genesis-keys" ]; then
    echo "⚠️  Warning: 'genesis-keys' directory already exists. Keys may be overwritten."
    # sleep 2
fi

npx hardhat run scripts/deploy-genesis.ts --network localhost

echo "\n✅ Genesis Sequence Complete."
echo "PLEASE BACKUP 'genesis-keys' TO PHYSICAL USB DRIVES IMMEDIATELY."
echo "==================================================="
