/**
 * Example: Using PaymentVerifier for Pay-Per-Use API Access
 * 
 * This is a commented example showing how to add payment verification
 * to the /api/sponsor endpoint in server.ts
 * 
 * To enable this feature:
 * 1. Add TREASURY_ADDRESS to your .env file
 * 2. Uncomment the code below in server.ts
 * 3. Update client to send x-payment-tx header
 */

import { PaymentVerifier } from '@swimmingkiim/pay-sdk';
import { base } from 'viem/chains';

// Inside /api/sponsor endpoint, before sponsorship:

const paymentTxHash = req.headers['x-payment-tx'] as `0x${string}`;
const RPC_URL = process.env.RPC_URL || 'https://mainnet.base.org';
const TREASURY_ADDRESS = process.env.TREASURY_ADDRESS as `0x${string}`;

if (!paymentTxHash) {
    return res.status(402).json({
        error: 'Payment required',
        message: 'Please send payment and include transaction hash in x-payment-tx header'
    });
}

// Initialize payment verifier
const paymentVerifier = new PaymentVerifier({
    rpcUrl: RPC_URL,
    chain: base,
    // tokenAddress: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913' // USDC (default)
});

// Verify payment (0.1 USDC = 100000n base units)
const verification = await paymentVerifier.verifyUSDCPayment(
    paymentTxHash,
    userOperation.sender,  // Payment must come from the UserOp sender
    TREASURY_ADDRESS,      // Payment must go to your treasury
    100000n                // Minimum 0.1 USDC
);

if (!verification.isValid) {
    return res.status(402).json({
        error: 'Payment verification failed',
        details: verification.error
    });
}

console.log(`✅ Payment verified: ${verification.amount} USDC from ${verification.from}`);

// Optional: Store payment hash in Redis/DB to prevent reuse
// await redis.set(`payment:${paymentTxHash}`, 'used', 'EX', 3600);

// Continue with sponsorship...
