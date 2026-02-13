# E2E Demo Guide: COMP Token Fee Payment

This demo validates the complete COMP token fee payment flow on Base Sepolia testnet.

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
  
- **MINTER_ROLE on COMP Token**: To mint test COMP
  - Contract: `0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3`
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
2. ✅ Checks COMP balance (mints if needed)
3. ✅ Sends 25 COMP to treasury
4. ✅ Verifies fee payment
5. ✅ Displays transaction details

### Expected Output

```
🚀 Starting E2E Demo: COMP Fee Payment

============================================================

📋 Step 1: Environment Check
   Wallet: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0
   COMP Token: 0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3
   Treasury: 0x1234567890123456789012345678901234567890
   RPC: https://sepolia.base.org
   ETH Balance: 0.05 ETH

💰 Step 2: COMP Balance Check
   Current COMP Balance: 100 COMP
   ✅ Sufficient balance

📝 Step 3: Preparing COMP Fee Transaction
   Fee Amount: 25 COMP
   Treasury: 0x1234567890123456789012345678901234567890
   ✅ Fee transaction encoded

📤 Step 4: Sending COMP Fee Payment
   Sending 25 COMP to Treasury...
   Treasury balance before: 150 COMP
   Transaction: 0xabc123...

⏳ Step 5: Waiting for Confirmation
   ✅ Confirmed in block 1234567
   Gas used: 52000

✅ Step 6: Verifying Fee Payment
   User balance after: 75 COMP
   Treasury balance after: 175 COMP
   Treasury received: 25 COMP
   ✅ Fee payment verified!

============================================================
🎉 E2E Demo Complete!

Summary:
  ✅ COMP token transfer successful
  ✅ Treasury received 25 COMP
  ✅ Transaction confirmed on Base Sepolia
  ✅ Block: 1234567
  ✅ TX: 0xabc123...

📚 Next Steps:
  1. Integrate with actual Smart Account
  2. Submit UserOp to Paymaster
  3. Test with ENABLE_COMP_FEES=true
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

// 1. Create calls with COMP fee
const calls = PaymasterManager.appendFeeToCalls(baseCalls, {
  treasury: TREASURY_ADDRESS,
  amount: 25n * 10n**18n,
  tokenType: 'COMP'
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

Check COMP token contract:
```
https://sepolia.basescan.org/address/0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3
```

## Success Criteria

✅ Demo wallet has ETH  
✅ COMP tokens minted successfully  
✅ Fee transfer completes  
✅ Treasury balance increases  
✅ Transaction confirmed on-chain
