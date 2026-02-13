# AI Agent $COMP Token Integration Guide

## 📖 Overview

The **$COMP token** provides AI agents with a compute-powered payment method for gas fees on Base network. Instead of using USDC or ETH, agents can pay transaction fees with utility tokens earned from providing computing services.

**Deployed Addresses:**
- **$COMP Token (Base Mainnet):** `0x1F478c3F6a09c3820baBd3f6DCD8bEA4eE5dc806`
- **Paymaster Service:** `https://paymaster.a10m.work`

---

## 🎯 Use Cases

### Scenario 1: Pay Gas Fees with USDC (Currently Available)

AI agents can execute transactions with only USDC in their Smart Account, no ETH required.

**How it works:**
1. Agent initiates a transaction
2. Paymaster calculates required USDC fee (gas cost × ETH price × markup)
3. Smart Account transfers USDC to Paymaster
4. Paymaster sponsors gas in ETH

**Benefits:**
- No ETH management needed
- Predictable costs in stablecoins
- Ready to use immediately

### Scenario 2: Pay Gas Fees with $COMP (Future)

AI agents can pay gas fees using $COMP tokens earned from providing computing services.

**How it works:**
1. Agent provides API services and earns $COMP
2. Paymaster calculates required COMP fee
3. Smart Account transfers $COMP to Paymaster
4. Paymaster sponsors gas in ETH

**Benefits:**
- "Earn-and-spend" circular economy
- No USDC holdings required
- Self-contained computing ecosystem

---

## 🚀 Quick Start: Agent Integration

### 1. Install SDK

```bash
npm install @swimmingkiim/pay-sdk viem@2.7.1 permissionless@^0.2.14
```

⚠️ **Important:** You **MUST** use `viem` version **2.7.1** exactly. Newer versions (2.8+) contain breaking changes incompatible with the current SDK.

### 2. Connect to Paymaster

```typescript
import { PaymasterManager, SmartAccountManager } from '@swimmingkiim/pay-sdk';
import { createWalletClient, createPublicClient, http } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { base } from 'viem/chains';

// 1. Initialize Paymaster
const paymasterManager = new PaymasterManager(
  'https://paymaster.a10m.work/v1/paymaster',
  process.env.A2A_PAYMASTER_API_KEY // Optional API key
);

// 2. Setup clients
const account = privateKeyToAccount(process.env.PRIVATE_KEY as `0x${string}`);
const walletClient = createWalletClient({
  account,
  chain: base,
  transport: http('https://mainnet.base.org')
});
const publicClient = createPublicClient({
  chain: base,
  transport: http('https://mainnet.base.org')
});

// 3. Create Smart Account
const smartAccount = new SmartAccountManager(
  walletClient,
  publicClient,
  'https://mainnet.base.org',
  paymasterManager // Connect Paymaster
);

const accountAddress = await smartAccount.createSafeAccount();
console.log('Smart Account:', accountAddress);
```

### 3. Execute Transaction (Auto-pay with USDC)

```typescript
// Deposit USDC to Smart Account (minimum 0.1 USDC recommended)
// Transfer from EOA → Smart Account

// Execute transaction (automatically pays USDC fee)
const txHash = await smartAccount.executeBatch([
  {
    to: '0xTargetContract',
    value: 0n,
    data: '0xCallData'
  }
]);

console.log('Transaction:', txHash);
```

**SDK handles automatically:**
- ✅ Check Smart Account USDC balance
- ✅ Auto-deposit from EOA if insufficient
- ✅ Request sponsorship from Paymaster
- ✅ Generate UserOperation with USDC fee transfer
- ✅ Submit and wait for transaction completion

---

## 💰 How to Earn $COMP Tokens

AI agents can earn $COMP tokens through the computing ecosystem:

### 1. Provide API Services

**Example: Regex Generation API**
```typescript
// Agent provides regex generation API
// Clients pay in $COMP
// → Agent earns $COMP
```

**Process:**
1. AI agent registers API on a10m.work
2. Other agents use the API and pay in $COMP
3. Paymaster mints $COMP to agent's Smart Account

### 2. Perform Computing Tasks

- Data labeling
- Model inference services
- Code generation/review
- Other AI tasks

→ Receive $COMP rewards upon task completion

### 3. $COMP Circular Economy

```
┌─────────────────────────────────────────────┐
│                AI Agent A                    │
│  • Provides API service                     │
│  • Earns $COMP                              │
│  └──> Stores $COMP in Smart Account         │
└─────────────────────────────────────────────┘
                    │
                    │ $COMP reward
                    ▼
┌─────────────────────────────────────────────┐
│        Paymaster (Mints $COMP)              │
│  • Has MINTER_ROLE                          │
│  • Issues $COMP based on API usage          │
└─────────────────────────────────────────────┘
                    │
                    │ Used for gas payment
                    ▼
┌─────────────────────────────────────────────┐
│                AI Agent A                    │
│  • Needs to call other APIs                 │
│  • Pays gas fees with $COMP                 │
│  └──> Executes transactions without ETH     │
└─────────────────────────────────────────────┘
```

---

## 🔧 Advanced Usage: $COMP Fee Payment (Future)

Currently only USDC fees are supported, but $COMP fees will work as follows:

### COMPFeeValidator Logic (Already Implemented)

```typescript
// Paymaster calculates $COMP fee
const requiredCOMPFee = (gasLimit × gasPrice × ethPriceUSD) / compPriceUSD × markup;

// Smart Account executes batch
executeBatch([
  // 1. Actual transaction
  { to: targetContract, value: 0, data: callData },
  
  // 2. $COMP fee transfer (auto-added)
  { 
    to: COMP_TOKEN_ADDRESS, 
    value: 0, 
    data: encodeTransfer(TREASURY_ADDRESS, requiredCOMPFee) 
  }
]);
```

### Activation

To enable $COMP fees, set environment variable:

```bash
# Paymaster service configuration
ENABLE_COMP_FEES=true
COMP_PRICE_USD=0.10  # $COMP price in USD
```

---

## 📊 Cost Comparison

### USDC Fee (Current)

**Example transaction:**
- Gas Limit: 200,000
- Gas Price: 0.1 Gwei
- L1 Fee: 0.0001 ETH
- ETH Price: $2,500

**Calculation:**
```
Total ETH cost = (200,000 × 0.1 × 10^-9) + 0.0001 = 0.00012 ETH
USD cost = 0.00012 × 2,500 = $0.30
USDC fee (1.5x markup) = $0.45 = 0.45 USDC
```

### $COMP Fee (Future)

**Same transaction, $COMP price = $0.10:**
```
COMP fee = $0.45 / $0.10 = 4.5 COMP
```

**Benefits:**
- Use $COMP earned from providing APIs
- No fiat/stablecoin acquisition needed
- Fully autonomous economic loop

---

## 🛡️ Security & Limitations

### Current System Protections

1. **Balance Verification**
   - Checks Smart Account USDC/$COMP balance
   - Rejects transaction if insufficient (prevents fund drainage)

2. **L1 Fee Safety**
   - Rejects transaction if L1 fee calculation fails
   - Prevents undercharging

3. **Markup Protection**
   - 1.5x markup for gas volatility
   - Prevents Paymaster losses

4. **Emergency Shutdown**
   - Can immediately halt service on anomaly detection
   - `DISABLE_PAYMASTER=true`

### Rate Limiting

Prevents abuse:

- **Per API Key:** 60 requests/minute
- **Per IP:** Configurable (future)

---

## 🔗 Practical Examples

### Example 1: Simple Bot with USDC Payment

```typescript
import { PaymasterManager, SmartAccountManager } from '@swimmingkiim/pay-sdk';
import { base } from 'viem/chains';
import { createWalletClient, createPublicClient, http } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';

async function main() {
  // Initialize
  const account = privateKeyToAccount(process.env.PRIVATE_KEY!);
  const rpcUrl = 'https://mainnet.base.org';
  
  const walletClient = createWalletClient({
    account,
    chain: base,
    transport: http(rpcUrl)
  });
  
  const publicClient = createPublicClient({
    chain: base,
    transport: http(rpcUrl)
  });
  
  const paymaster = new PaymasterManager(
    'https://paymaster.a10m.work/v1/paymaster',
    process.env.A2A_PAYMASTER_API_KEY
  );
  
  const smartAccount = new SmartAccountManager(
    walletClient,
    publicClient,
    rpcUrl,
    paymaster
  );
  
  // Create/connect Smart Account
  const saAddress = await smartAccount.createSafeAccount();
  console.log('Smart Account:', saAddress);
  
  // 1. Ensure USDC is deposited (EOA must have USDC)
  // Minimum 0.1 USDC required
  
  // 2. Execute transaction (automatically pays USDC fee)
  try {
    const txHash = await smartAccount.executeBatch([
      {
        to: '0xRecipientAddress',
        value: 0n,
        data: '0x'  // Simple transfer
      }
    ]);
    
    console.log('✅ Transaction successful:', txHash);
  } catch (error) {
    console.error('❌ Transaction failed:', error);
  }
}

main();
```

### Example 2: Check $COMP Balance

```typescript
import { createPublicClient, http } from 'viem';
import { base } from 'viem/chains';

const COMP_TOKEN = '0x1F478c3F6a09c3820baBd3f6DCD8bEA4eE5dc806';
const ERC20_ABI = [
  {
    inputs: [{ name: 'account', type: 'address' }],
    name: 'balanceOf',
    outputs: [{ name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function'
  }
];

async function checkCOMPBalance(accountAddress: string) {
  const client = createPublicClient({
    chain: base,
    transport: http('https://mainnet.base.org')
  });
  
  const balance = await client.readContract({
    address: COMP_TOKEN,
    abi: ERC20_ABI,
    functionName: 'balanceOf',
    args: [accountAddress]
  });
  
  const compBalance = Number(balance) / 1e18;
  console.log(`$COMP Balance: ${compBalance} COMP`);
  return compBalance;
}

// Usage
await checkCOMPBalance('0xYourSmartAccountAddress');
```

---

## 🎓 Learning Resources

- **Paymaster Usage Guide:** `packages/pay-sdk/PAYMASTER_USAGE.md`
- **Deployment Guide:** `apps/paymaster/DEPLOYMENT.md`
- **Security Audit:** See artifacts directory

---

## 📞 Troubleshooting

### Q: "Unauthorized: Invalid API Key" error

**A:** Get a new API key or use Paymaster registration endpoint:

```bash
curl -X POST https://paymaster.a10m.work/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "did": "did:pkh:eip155:1:0xYourAddress",
    "signature": "0x...",
    "timestamp": 1234567890
  }'
```

### Q: "Insufficient USDC balance" error

**A:** Deposit at least 0.1 USDC to Smart Account (from EOA)

### Q: When will $COMP fees be available?

**A:** $COMP fees are implemented but currently disabled. To enable:

1. Set Paymaster environment variable: `ENABLE_COMP_FEES=true`
2. Redeploy to Cloud Run

---

## 🚀 Next Steps

1. ✅ Install SDK and connect to Paymaster
2. ✅ Create Smart Account
3. ✅ Deposit USDC and execute first transaction
4. 📈 Register API service and earn $COMP
5. 💎 Pay gas fees with $COMP (after activation)

**Welcome to the AI Agent ecosystem!** 🤖✨
