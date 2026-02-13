# E2E Demo Guide: TOKEN Token Fee Payment

This demo validates the complete TOKEN token fee payment flow on Base Sepolia testnet.

## Prerequisites

### 1. Environment Setup

Create `.env` in project root:

```bash
# Base Sepolia RPC
RPC_URL=https://sepolia.base.org

# Demo wallet (must have ETH for gas)
DEMO_PRIVATE_KEY=0x...

# Treasury address (where fees are sent)
TREASURY_ADDRESS=0x...

# Optional: Paymaster URL
PAYMASTER_URL=http://localhost:8080/v1/paymaster
```

### 2. Required Access

- **ETH on Base Sepolia**: For gas fees
  - Get from [Base Sepolia Faucet](https://www.coinbase.com/faucets/base-ethereum-goerli-faucet)
  
- **MINTER_ROLE on TOKEN Token**: To mint test TOKEN
  - Contract: `<TOKEN_ADDRESS>`
  - Grant via: `npx hardhat run scripts/grant-minter-role.ts --network baseSepolia`

### 3. Dependencies

```bash
npm install tsx viem dotenv
```

## Running the Demo

### Basic Demo (Direct Fee Payment)

```bash
cd /Users/kimsooyoung/Developments/projects/a2a-projects
tsx scripts/e2e-comp-demo.ts
```

**What it does:**
1. ✅ Checks wallet ETH balance
2. ✅ Checks TOKEN balance (mints if needed)
3. ✅ Sends 25 TOKEN to treasury
4. ✅ Verifies fee payment
5. ✅ Displays transaction details

### Expected Output

```
🚀 Starting E2E Demo: TOKEN Fee Payment

============================================================

📋 Step 1: Environment Check
   Wallet: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0
   TOKEN Token: <TOKEN_ADDRESS>
   Treasury: 0x1234567890123456789012345678901234567890
   RPC: https://sepolia.base.org
   ETH Balance: 0.05 ETH

💰 Step 2: TOKEN Balance Check
   Current TOKEN Balance: 100 TOKEN
   ✅ Sufficient balance

📝 Step 3: Preparing TOKEN Fee Transaction
   Fee Amount: 25 TOKEN
   Treasury: 0x1234567890123456789012345678901234567890
   ✅ Fee transaction encoded

📤 Step 4: Sending TOKEN Fee Payment
   Sending 25 TOKEN to Treasury...
   Treasury balance before: 150 TOKEN
   Transaction: 0xabc123...

⏳ Step 5: Waiting for Confirmation
   ✅ Confirmed in block 1234567
   Gas used: 52000

✅ Step 6: Verifying Fee Payment
   User balance after: 75 TOKEN
   Treasury balance after: 175 TOKEN
   Treasury received: 25 TOKEN
   ✅ Fee payment verified!

============================================================
🎉 E2E Demo Complete!

Summary:
  ✅ TOKEN token transfer successful
  ✅ Treasury received 25 TOKEN
  ✅ Transaction confirmed on Base Sepolia
  ✅ Block: 1234567
  ✅ TX: 0xabc123...

📚 Next Steps:
  1. Integrate with actual Smart Account
  2. Submit UserOp to Paymaster
  3. Test with ENABLE_TOKEN_FEES=true
  4. Deploy to Base Mainnet
```

## Troubleshooting

### Error: "Insufficient ETH for gas"

**Solution:**
```bash
# Get ETH from faucet
open https://www.coinbase.com/faucets/base-ethereum-goerli-faucet
```

### Error: "Missing MINTER_ROLE"

**Solution:**
```bash
# Grant minter role to your demo wallet
cd packages/contracts
npx hardhat run scripts/grant-role.ts --network baseSepolia
```

### Error: "RPC connection failed"

**Solution:**
```bash
# Use public RPC or your own
RPC_URL=https://sepolia.base.org
# or
RPC_URL=https://base-sepolia.g.alchemy.com/v2/YOUR_KEY
```

## Next: Full UserOp Integration

For complete integration with Smart Accounts and Paymaster:

```typescript
import { PaymasterManager } from '@swimmingkiim/pay-sdk';

// 1. Create calls with TOKEN fee
const calls = PaymasterManager.appendFeeToCalls(baseCalls, {
  treasury: TREASURY_ADDRESS,
  amount: 25n * 10n**18n,
  tokenType: 'TOKEN'
});

// 2. Create UserOp
const userOp = await smartAccount.prepareUserOperation({ calls });

// 3. Get Paymaster sponsorship
const paymaster = new PaymasterManager(PAYMASTER_URL);
const sponsored = await paymaster.sponsorUserOperation(userOp);

// 4. Send transaction
const hash = await smartAccount.sendUserOperation(sponsored);
```

## Verification

Check transaction on Base Sepolia Explorer:
```
https://sepolia.basescan.org/tx/YOUR_TX_HASH
```

Check TOKEN token contract:
```
https://sepolia.basescan.org/address/<TOKEN_ADDRESS>
```

## Success Criteria

✅ Demo wallet has ETH  
✅ TOKEN tokens minted successfully  
✅ Fee transfer completes  
✅ Treasury balance increases  
✅ Transaction confirmed on-chain
