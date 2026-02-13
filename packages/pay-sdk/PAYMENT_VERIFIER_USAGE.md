# PaymentVerifier Usage Guide

## Overview
`PaymentVerifier` is a utility class in `@swimmingkiim/pay-sdk` that verifies on-chain ERC20 token transfers. It's designed for implementing "pay-per-use" API patterns.

## Installation

The class is already included in `@swimmingkiim/pay-sdk`:

```typescript
import { PaymentVerifier } from '@swimmingkiim/pay-sdk';
```

## Basic Usage

### 1. Initialize PaymentVerifier

```typescript
import { PaymentVerifier } from '@swimmingkiim/pay-sdk';
import { base } from 'viem/chains';

const verifier = new PaymentVerifier({
    rpcUrl: 'https://mainnet.base.org',
    chain: base,
    tokenAddress: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913' // Optional: USDC (default)
});
```

### 2. Verify a Payment

```typescript
const result = await verifier.verifyUSDCPayment(
    '0x123...', // Transaction hash
    '0xabc...', // Expected sender
    '0xdef...', // Expected receiver (your treasury)
    100000n     // Minimum amount (0.1 USDC)
);

if (result.isValid) {
    console.log(`Payment verified: ${result.amount} tokens`);
} else {
    console.error(`Verification failed: ${result.error}`);
}
```

## API Reference

### `PaymentVerifier`

#### Constructor

```typescript
new PaymentVerifier(config: PaymentVerifierConfig)
```

**Config:**
- `rpcUrl`: Blockchain RPC endpoint
- `chain`: viem Chain object (e.g., `base`, `mainnet`)
- `tokenAddress?`: ERC20 token address (defaults to USDC on Base)

#### Methods

##### `verifyPayment()`

```typescript
async verifyPayment(
    txHash: `0x${string}`,
    expectedFrom: `0x${string}`,
    expectedTo: `0x${string}`,
    minimumAmount: bigint
): Promise<PaymentVerificationResult>
```

Verifies an ERC20 transfer transaction.

**Returns:**
```typescript
{
    isValid: boolean;
    error?: string;
    txHash?: `0x${string}`;
    from?: `0x${string}`;
    to?: `0x${string}`;
    amount?: bigint;
}
```

##### `verifyUSDCPayment()`

Convenience method with the same signature as `verifyPayment()` but optimized for USDC verification.

## Real-World Example: Paymaster Proxy Server

```typescript
import express from 'express';
import { PaymentVerifier, PaymasterManager } from '@swimmingkiim/pay-sdk';
import { base } from 'viem/chains';

const app = express();
app.use(express.json());

const TREASURY = process.env.TREASURY_ADDRESS as `0x${string}`;
const verifier = new PaymentVerifier({
    rpcUrl: process.env.RPC_URL!,
    chain: base
});

app.post('/api/sponsor', async (req, res) => {
    const paymentTx = req.headers['x-payment-tx'] as `0x${string}`;
    
    if (!paymentTx) {
        return res.status(402).json({ error: 'Payment required' });
    }
    
    // Verify payment
    const verification = await verifier.verifyUSDCPayment(
        paymentTx,
        req.body.userOperation.sender,
        TREASURY,
        100000n // 0.1 USDC
    );
    
    if (!verification.isValid) {
        return res.status(402).json({ 
            error: 'Invalid payment',
            details: verification.error
        });
    }
    
    // Payment verified → provide service
    const sponsorship = await paymasterManager.getStubPaymasterData(
        req.body.userOperation
    );
    
    res.json(sponsorship);
});
```

## Best Practices

### 1. Prevent Payment Reuse

Store verified transaction hashes to prevent reuse:

```typescript
import Redis from 'ioredis';
const redis = new Redis();

// After verification:
if (verification.isValid) {
    // Check if already used
    const exists = await redis.exists(`payment:${txHash}`);
    if (exists) {
        return { error: 'Payment already used' };
    }
    
    // Mark as used (expires in 1 hour)
    await redis.set(`payment:${txHash}`, 'used', 'EX', 3600);
}
```

### 2. Time-Based Expiration

Only accept recent payments:

```typescript
const receipt = await publicClient.getTransactionReceipt({ hash: txHash });
const block = await publicClient.getBlock({ blockNumber: receipt.blockNumber });
const txTime = Number(block.timestamp) * 1000;
const now = Date.now();

if (now - txTime > 5 * 60 * 1000) { // 5 minutes
    return { error: 'Payment expired' };
}
```

### 3. Credit System

Allow overpayment for credits:

```typescript
const PRICE_PER_REQUEST = 100000n; // 0.1 USDC

if (verification.amount > PRICE_PER_REQUEST) {
    const credits = verification.amount / PRICE_PER_REQUEST;
    await db.addCredits(userAddress, Number(credits));
}
```

## Error Handling

Common errors returned in `PaymentVerificationResult.error`:

- `"Transaction not found"`: Invalid transaction hash
- `"Transaction failed"`: Transaction reverted on-chain
- `"No transfer events found for this token"`: Wrong token or no transfer occurred
- `"No matching transfer found in transaction"`: Transfer exists but doesn't match criteria (wrong sender/receiver/amount)

## Chain Support

Works on any EVM-compatible chain. Examples:

```typescript
import { mainnet, base, arbitrum, optimism } from 'viem/chains';

// Ethereum mainnet
const ethVerifier = new PaymentVerifier({
    rpcUrl: 'https://eth.llamarpc.com',
    chain: mainnet,
    tokenAddress: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48' // USDC on Ethereum
});

// Arbitrum
const arbVerifier = new PaymentVerifier({
    rpcUrl: 'https://arb1.arbitrum.io/rpc',
    chain: arbitrum,
    tokenAddress: '0xaf88d065e77c8cC2239327C5EDb3A432268e5831' // USDC on Arbitrum
});
```
