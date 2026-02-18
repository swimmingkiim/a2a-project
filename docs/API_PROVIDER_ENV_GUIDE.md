# API Provider Environment Variables Guide

This guide covers all environment variables needed to run an API service with A2A's pay-per-use (payment verification) model.

## Required Environment Variables

### 1. Blockchain & Payment Configuration

#### `RPC_URL` (Required)
- **Purpose**: RPC endpoint to verify on-chain transactions
- **Example**: `https://base-mainnet.g.alchemy.com/v2/YOUR_API_KEY`
- **Networks**: 
  - Base Mainnet: `https://mainnet.base.org`
  - Base Sepolia (testnet): `https://sepolia.base.org`
- **Provider Options**: Alchemy, Infura, QuickNode, or public RPCs

#### `TREASURY_ADDRESS` (Required)
- **Purpose**: Your wallet address to receive USDC payments
- **Example**: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb`
- **Security**: 
  - Can be a hot wallet (payments go here)
  - No private key needed on the server
  - Bot transfers funds TO this address
- **Recommendation**: Use a dedicated treasury address, not your main wallet

---

### 2. Paymaster Configuration (Optional - for sponsoring user operations)

If you want to sponsor gas fees for your API users:

#### `PAYMASTER_URL` (Optional)
- **Purpose**: A2A Paymaster service endpoint
- **Example**: `https://paymaster.a10m.work/v1/paymaster`
- **Use Case**: Sponsor gas fees for users calling your API

#### `A2A_PAYMASTER_API_KEY` (Optional)
- **Purpose**: API key for paymaster service
- **How to Get**: Register at paymaster service using `register-signer.ts` script
- **Example**: `a2a_sk_live_abc123...`

#### `PRIVATE_KEY` (Required if using Paymaster)
- **Purpose**: Private key for signing paymaster requests
- **Format**: `0x...` (64 hex characters)
- **Security**: ⚠️ NEVER commit to git, use secrets management
- **Recommendation**: Use a dedicated key, not your treasury key

---

### 3. Application Configuration

#### `PORT` (Optional)
- **Purpose**: Port for your API server
- **Default**: `3000`
- **Example**: `8080`

---

## Complete .env Example

### Basic Payment Verification Only
```bash
# Blockchain Configuration
RPC_URL=https://mainnet.base.org
TREASURY_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

# Server Configuration
PORT=3000
```

### With Paymaster Support
```bash
# Blockchain Configuration
RPC_URL=https://mainnet.base.org
TREASURY_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

# Paymaster Configuration (Optional)
PAYMASTER_URL=https://paymaster.a10m.work/v1/paymaster
A2A_PAYMASTER_API_KEY=a2a_sk_live_abc123...
PRIVATE_KEY=0xYourPrivateKeyForPaymasterSigning

# Server Configuration
PORT=3000
```

---

## What You DON'T Need

### ❌ Treasury Private Key
- You only need the **address**, not the private key
- Payments come TO your address
- No signing needed on the server side

### ❌ User Wallet Information
- Users manage their own wallets
- Your API only verifies transactions

### ❌ API Keys to Expose
- Don't expose `PRIVATE_KEY` or `A2A_PAYMASTER_API_KEY`
- These are server-side secrets only

---

## Security Best Practices

### 1. Separate Keys for Different Purposes

| Purpose | Key Type | Can Reuse? |
|---------|----------|------------|
| **Treasury** (receive payments) | Public Address | ✅ Can share via API endpoint |
| **Paymaster Signing** | Private Key | ❌ Keep secret, dedicated key |
| **Main Wallet** (personal assets) | Private Key | ❌ Never use for services |

### 2. Environment Variable Management

**Local Development:**
```bash
# .env file (add to .gitignore)
cp .env.example .env
# Edit .env with your actual values
```

**Production (Cloud Run, Vercel, etc.):**
- Use platform's secrets management
- Never commit actual values to git
- Rotate keys periodically

**Example - Cloud Run:**
```bash
gcloud run deploy my-api \
  --update-env-vars="RPC_URL=https://mainnet.base.org" \
  --update-secrets="TREASURY_ADDRESS=treasury-addr:latest" \
  --update-secrets="PRIVATE_KEY=paymaster-key:latest"
```

### 3. .gitignore Setup

```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Never commit
**/*.key
**/private-keys/
```

---

## Getting Started Checklist

- [ ] 1. Create treasury wallet address
  - Generate new address or use existing
  - Save address for `TREASURY_ADDRESS`
  
- [ ] 2. Get RPC endpoint
  - Sign up for Alchemy/Infura (free tier available)
  - Or use public RPC (may be slower)
  
- [ ] 3. (Optional) Register with Paymaster
  - Run `apps/paymaster/register-signer.ts`
  - Save API key as `A2A_PAYMASTER_API_KEY`
  
- [ ] 4. Create .env file
  - Copy `.env.example` to `.env`
  - Fill in all required values
  
- [ ] 5. Verify configuration
  - Start server locally
  - Test payment verification endpoint
  - Check RPC connectivity

---

## Example: Minimal API Setup

```typescript
import express from 'express';
import { PaymentVerifier } from '@swimmingkiim/pay-sdk';
import { base } from 'viem/chains';

const app = express();
app.use(express.json());

// Initialize PaymentVerifier
const paymentVerifier = new PaymentVerifier({
  rpcUrl: process.env.RPC_URL!,
  chain: base,
  tokenAddress: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913' // USDC on Base
});

// Payment info endpoint
app.get('/api/payment-info', (req, res) => {
  res.json({
    treasuryAddress: process.env.TREASURY_ADDRESS,
    pricePerCall: '1000000', // 1 USDC (6 decimals)
    acceptedTokens: ['USDC'],
    chain: 'base'
  });
});

// Protected API endpoint
app.post('/api/protected-endpoint', async (req, res) => {
  const paymentTx = req.headers['x-payment-tx'] as string;
  
  if (!paymentTx) {
    return res.status(400).json({ error: 'Payment required' });
  }
  
  // Verify payment
  const verification = await paymentVerifier.verifyUSDCPayment(
    paymentTx as `0x${string}`,
    req.body.from as `0x${string}`,
    process.env.TREASURY_ADDRESS as `0x${string}`,
    1000000n // 1 USDC minimum
  );
  
  if (!verification.isValid) {
    return res.status(402).json({ 
      error: 'Invalid payment',
      details: verification.error 
    });
  }
  
  // Process request
  res.json({ result: 'Success!' });
});

app.listen(process.env.PORT || 3000);
```

---

## FAQ

**Q: Do I need to expose my treasury address publicly?**  
A: No, provide it via the `/api/payment-info` endpoint, not on your landing page.

**Q: Can I use the same address for treasury and paymaster signing?**  
A: Technically yes, but not recommended for security. Use separate addresses.

**Q: What if I don't want to sponsor gas fees?**  
A: Skip the paymaster configuration entirely. Users will pay their own gas.

**Q: How do I rotate my private key?**  
A: 
1. Generate new key
2. Register new key with paymaster
3. Update `PRIVATE_KEY` env var
4. Redeploy service

**Q: Can I use testnet for development?**  
A: Yes! Use Base Sepolia:
- RPC: `https://sepolia.base.org`
- USDC Testnet: Get from faucet
- Paymaster: May have separate testnet URL
