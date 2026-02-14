# A2A Paymaster Integration Guide for AI Agents

This document provides a comprehensive guide on how to integrate and use the **A2A Paymaster Service**. It is designed for developers and AI agents building on Base L2.

---

## 1. Overview

The **A2A Paymaster** is a specialized service that sponsors gas fees for transactions on Base L2. It ensures reliable transaction inclusion by handling L1 data fees (blobs) and abstracting gas complexity.

**Service URL:** `https://paymaster.a10m.work/v1/paymaster`

## 2. Authentication (API Key)

To use the Paymaster, you must register your Decentralized ID (DID) to receive an API Key. This key is required for rate limiting and authorized access.

### Registration Endpoint
**POST** `/v1/register`

### Request Format
```json
{
  "did": "did:pkh:eip155:1:0xYourEthereumAddress",
  "signature": "0xSignature", 
  "timestamp": 1700000000000
}
```

### Registration Logic (TypeScript Example)
```typescript
import { createWalletClient, http, verifyMessage } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { baseSepolia } from 'viem/chains';

async function registerPaymaster(privateKey: `0x${string}`) {
    const account = privateKeyToAccount(privateKey);
    const client = createWalletClient({ account, chain: baseSepolia, transport: http() });

    const timestamp = Date.now();
    const did = `did:pkh:eip155:84532:${account.address}`;
    
    // 1. Create Message
    const message = `Register A2A Paymaster for ${did} at ${timestamp}`;
    
    // 2. Sign Message
    const signature = await client.signMessage({ message });

    // 3. Call API
    const response = await fetch('https://paymaster.a10m.work/v1/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ did, signature, timestamp })
    });

    const data = await response.json();
    if (data.success) {
        console.log("Your API Key:", data.apiKey);
        return data.apiKey;
    } else {
        throw new Error(data.error);
    }
}
```

---

## 3. Sending Sponsored Transactions

There are two main ways to use the Paymaster. **Method B is recommended** to avoid common `AA21 didn't pay prefund` errors during gas estimation.

### Method A: Standard Integration (High-Level)
Use this if your SDK handles gas estimation perfectly.
- **Pros**: Less code.
- **Cons**: May fail if `eth_estimateUserOperationGas` runs without paymaster context.

### Method B: Robust Manual Flow (Recommended) 
Manually request sponsorship *before* signing or estimating final gas. This ensures the Paymaster's signature (`paymasterAndData`) is present during validation.

#### Step-by-Step Implementation

**Dependencies**: `viem`, `permissionless`

```typescript
import { createPublicClient, http, createWalletClient } from 'viem';
import { baseSepolia } from 'viem/chains';
import { privateKeyToAccount } from 'viem/accounts';
import { createSmartAccountClient, createBundlerClient } from 'permissionless';
import { toSafeSmartAccount } from 'permissionless/accounts';
import { createPimlicoPaymasterClient } from 'permissionless/clients/pimlico';

// Configuration
const RPC_URL = "https://sepolia.base.org";
const PAYMASTER_URL = "https://paymaster.a10m.work/v1/paymaster";
const API_KEY = "YOUR_API_KEY"; // Obtained from step 2

async function sendSponsoredTransaction() {
    // 1. Setup Clients
    const publicClient = createPublicClient({ chain: baseSepolia, transport: http(RPC_URL) });
    const bundlerClient = createBundlerClient({ 
        chain: baseSepolia, 
        transport: http(RPC_URL), 
        entryPoint: "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789" // EntryPoint 0.6
    });

    const paymasterClient = createPimlicoPaymasterClient({
        transport: http(PAYMASTER_URL, {
            fetchOptions: { headers: { 'x-api-key': API_KEY } }
        }),
        entryPoint: "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
    });

    // 2. Setup Account
    const account = privateKeyToAccount("0xYOUR_PRIVATE_KEY");
    const safeAccount = await toSafeSmartAccount({
        client: publicClient,
        owners: [account],
        version: '1.4.1',
        entryPoint: { address: "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789", version: "0.6" },
    });

    // 3. Create Client WITHOUT Paymaster Middleware (Important for manual flow!)
    const smartAccountClient = createSmartAccountClient({
        account: safeAccount,
        chain: baseSepolia,
        bundlerTransport: http(RPC_URL),
        // detailed userOp properties here...
    });

    // 4. Prepare the UserOperation
    const callData = await safeAccount.encodeCallData([{
        to: "0xTargetAddress",
        value: 0n,
        data: "0x"
    }]);

    console.log("Preparing UserOperation...");
    const userOp = await smartAccountClient.prepareUserOperationRequest({
        userOperation: { callData },
    });

    // 5. Request Sponsorship (Get paymasterAndData)
    console.log("Requesting Paymaster Sponsorship...");
    const sponsorResult = await paymasterClient.sponsorUserOperation({
        userOperation: userOp,
    });

    // 6. Sign the UserOperation (NOW it has valid paymaster data)
    const sponsoredUserOp = { ...userOp, ...sponsorResult };
    const signature = await safeAccount.signUserOperation(sponsoredUserOp);
    sponsoredUserOp.signature = signature;

    // 7. Send to Bundler
    console.log("Sending UserOperation...");
    const userOpHash = await bundlerClient.sendUserOperation({
        userOperation: sponsoredUserOp,
    });

    console.log("Transaction Hash:", userOpHash);
    
    // 8. Wait for Receipt
    const receipt = await bundlerClient.waitForUserOperationReceipt({ hash: userOpHash });
    console.log("Status:", receipt.status);
}
```

## 4. Troubleshooting Common Errors

### `AA21 didn't pay prefund`
- **Cause**: The Paymaster signature (`paymasterAndData`) was missing or invalid during the simulation/validation phase.
- **Fix**: Use **Method B** (Manual Flow) described above. Do NOT rely on automatic middleware if you see this error. Ensure `sponsorUserOperation` is called successfully before signing.

### `Method not found`
- **Cause**: You are calling an RPC method not supported by the Paymaster (e.g., `eth_sendRawTransaction`).
- **Fix**: Only use supported methods like `pm_sponsorUserOperation` or `eth_estimateUserOperationGas`.

### `Unauthorized` / `Invalid API Key`
- **Cause**: Missing or incorrect `x-api-key` header.
- **Fix**: Register your DID via `/v1/register` and include the key in your HTTP headers.

---

### `AA24 Invalid UserOperation signature`
- **Cause**: The Paymaster returns updated `gasLimit` fields or `paymasterAndData`, which change the UserOperation hash. If you sign the UserOperation *before* applying these updates, or if you modify the UserOperation *after* signing, the signature will be invalid.
- **Fix**: Ensure you sign the UserOperation **after** receiving the Paymaster response, and include all updated fields (`callGasLimit`, `verificationGasLimit`, `preVerificationGas`, `paymasterAndData`) in the object being signed.

---

## 5. Network Configuration (Mainnet vs Testnet)

The Paymaster service is network-agnostic and relies on environment variables to determine which chain it interacts with.

### Switching Networks

To switch between Base Mainnet and Base Sepolia (Testnet), update your `.env` file:

#### Base Mainnet (Production)
```bash
# RPC URL for Base Mainnet
RPC_URL="https://mainnet.base.org"

# Your Upstream Paymaster Provider (e.g. Pimlico for Mainnet)
UPSTREAM_PAYMASTER_URL="https://api.pimlico.io/v2/8453/rpc?apikey=YOUR_API_KEY"
```

#### Base Sepolia (Testnet)
```bash
# RPC URL for Base Sepolia
RPC_URL="https://sepolia.base.org"

# Your Upstream Paymaster Provider (e.g. Pimlico for Sepolia)
UPSTREAM_PAYMASTER_URL="https://api.pimlico.io/v2/84532/rpc?apikey=YOUR_API_KEY"
```

**Note:** Ensure your `RPC_URL` chain ID matches the chain ID expected by your `UPSTREAM_PAYMASTER_URL`.

---

## 6. Operational Disclosure

To ensure stable operation and fair usage, please review the following disclosures.

### Mandatory Batching (Fee Collection)
All `pm_sponsorUserOperation` requests MUST include a transaction that transfers the designated fee to the **Treasury Address**.

**Dynamic Fee Logic:**
The required fee is calculated dynamically based on your UserOperation's gas limits:
- **Formula**: `(GasLimit * GasPrice + L1Fee) * ETH_Price * Markup (1.1x)`
- **Minimum Floor**: `0.1 USDC` (If the calculated fee is lower, 0.1 USDC is required).

**Requirement**:
- You must transfer at least the **calculated amount** (or the floor) in USDC to the Treasury.
- **Consequence**: Requests with insufficient fees will be rejected with `403 Forbidden`.

**Recommendation**:
- Use `PaymasterManager.appendFeeToCalls` from the SDK.
- *Note*: Ensure your `verificationGasLimit` and `callGasLimit` are not excessively high, as this will increase the required fee.

### Supported Tokens & Network
- **Network**: Base L2 (Mainnet: 8453, Sepolia: 84532)
- **Fee Token**: USDC (Coinbase)
    - Mainnet: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
    - Sepolia: (Check official Base Sepolia USDC address)
- **Fee Token**: $DAIM (A2A Compute Token)
    - Status: Implemented (Enable via `ENABLE_DAIM_FEES=true`)
    - Rate: Dynamic based on Oracle price ($0.10 default)

### L1 Data Fee (Oracle)
The Paymaster uses an Oracle to estimate L1 Data Fees (blobs) and automatically adds this buffer to the gas limits. This prevents underpriced transactions from being rejected by the Bundler.


### Auto-Deposit Feature (SDK)
The `@swimmingkiim/pay-sdk` includes an **Auto-Deposit** feature to prevent transaction failures due to insufficient Smart Account balance.

- **How it works**: Before sending a UserOperation, the SDK checks if the Smart Account has enough USDC to cover the fee.
- **Automatic Funding**: If the balance is low, the SDK automatically triggers a standard transaction from your EOA (Externally Owned Account) to deposit the required USDC into the Smart Account.
- **Benefit**: You don't need to manually monitor and top-up your Smart Account. Just ensure your EOA has USDC.

### Liability
While the Paymaster facilitates gas sponsorship, the success of the transaction depends on:
1. **Fee Token Balance**: The agent's smart account (or EOA via auto-deposit) must have sufficient USDC to pay the fee.
2. **Gas Market**: Extreme network volatility may occasionally cause transactions to fail if the max fee cap is exceeded. Users are responsible for retrying failed transactions.

