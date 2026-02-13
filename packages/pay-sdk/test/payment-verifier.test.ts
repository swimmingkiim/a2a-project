import { describe, it, expect, beforeAll, vi } from 'vitest';
import { PaymentVerifier } from '../src/payment/payment-verifier.js';
import { base } from 'viem/chains';

describe('PaymentVerifier', () => {
    const RPC_URL = 'https://mainnet.base.org';
    const USDC_ADDRESS = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';

    let verifier: PaymentVerifier;

    beforeAll(() => {
        verifier = new PaymentVerifier({
            rpcUrl: RPC_URL,
            chain: base,
            tokenAddress: USDC_ADDRESS
        });
    });

    describe('Constructor', () => {
        it('should initialize with custom token address', () => {
            const customVerifier = new PaymentVerifier({
                rpcUrl: RPC_URL,
                chain: base,
                tokenAddress: '0x1234567890123456789012345678901234567890'
            });
            expect(customVerifier).toBeDefined();
        });

        it('should use default USDC address if not specified', () => {
            const defaultVerifier = new PaymentVerifier({
                rpcUrl: RPC_URL,
                chain: base
            });
            expect(defaultVerifier).toBeDefined();
        });
    });

    describe('verifyPayment', () => {
        it('should return error for non-existent transaction', async () => {
            const result = await verifier.verifyPayment(
                '0x0000000000000000000000000000000000000000000000000000000000000000',
                '0x1111111111111111111111111111111111111111',
                '0x2222222222222222222222222222222222222222',
                100000n
            );

            expect(result.isValid).toBe(false);
            expect(result.error).toBeDefined();
        });

        // Note: Real on-chain tests would require actual transaction hashes
        // These are examples of how the tests should be structured

        it.skip('should verify valid USDC transfer (real tx)', async () => {
            // This would use a real transaction hash from Base mainnet
            const result = await verifier.verifyPayment(
                '0xREAL_TX_HASH_HERE',
                '0xSENDER_ADDRESS',
                '0xRECEIVER_ADDRESS',
                100000n
            );

            expect(result.isValid).toBe(true);
            expect(result.txHash).toBeDefined();
            expect(result.from).toBeDefined();
            expect(result.to).toBeDefined();
            expect(result.amount).toBeGreaterThanOrEqual(100000n);
        });

        it.skip('should reject transfer with insufficient amount (real tx)', async () => {
            const result = await verifier.verifyPayment(
                '0xREAL_TX_HASH_WITH_LOW_AMOUNT',
                '0xSENDER_ADDRESS',
                '0xRECEIVER_ADDRESS',
                1000000n  // Require more than tx has
            );

            expect(result.isValid).toBe(false);
            expect(result.error).toContain('No matching transfer');
        });

        it.skip('should reject transfer with wrong sender (real tx)', async () => {
            const result = await verifier.verifyPayment(
                '0xREAL_TX_HASH',
                '0xWRONG_SENDER_ADDRESS',
                '0xRECEIVER_ADDRESS',
                100000n
            );

            expect(result.isValid).toBe(false);
            expect(result.error).toContain('No matching transfer');
        });

        it.skip('should reject transfer with wrong receiver (real tx)', async () => {
            const result = await verifier.verifyPayment(
                '0xREAL_TX_HASH',
                '0xSENDER_ADDRESS',
                '0xWRONG_RECEIVER_ADDRESS',
                100000n
            );

            expect(result.isValid).toBe(false);
            expect(result.error).toContain('No matching transfer');
        });
    });

    describe('verifyUSDCPayment', () => {
        it('should call verifyPayment internally', async () => {
            const spy = vi.spyOn(verifier, 'verifyPayment');

            await verifier.verifyUSDCPayment(
                '0x0000000000000000000000000000000000000000000000000000000000000000',
                '0x1111111111111111111111111111111111111111',
                '0x2222222222222222222222222222222222222222',
                100000n
            );

            expect(spy).toHaveBeenCalledWith(
                '0x0000000000000000000000000000000000000000000000000000000000000000',
                '0x1111111111111111111111111111111111111111',
                '0x2222222222222222222222222222222222222222',
                100000n
            );
        });
    });

    describe('Error Handling', () => {
        it('should handle RPC errors gracefully', async () => {
            const badVerifier = new PaymentVerifier({
                rpcUrl: 'https://invalid-rpc-endpoint.invalid',
                chain: base
            });

            const result = await badVerifier.verifyPayment(
                '0x0000000000000000000000000000000000000000000000000000000000000000',
                '0x1111111111111111111111111111111111111111',
                '0x2222222222222222222222222222222222222222',
                100000n
            );

            expect(result.isValid).toBe(false);
            expect(result.error).toBeDefined();
        });
    });
});

// Integration test with real transaction (commented out by default)
describe.skip('PaymentVerifier Integration Tests', () => {
    it('should verify a real USDC transfer on Base', async () => {
        // This test requires a real transaction hash from Base mainnet
        // Example: Use a transaction from BaseScan
        const verifier = new PaymentVerifier({
            rpcUrl: 'https://mainnet.base.org',
            chain: base
        });

        // Replace with actual values from a real transaction
        const TX_HASH = '0xfbb560ca2441fc18b70220d90cc509832ebbfac09e1588a592a198deb73e4f73';
        const FROM = '0x7e2cdF0364Ced06032Ed91738f9827f61F14Fd25';
        const TO = '0xb6AF245cB3f8F85b1b4d62BD3f1C93f9cC48b88c';
        const AMOUNT = 600000n; // 0.6 USDC

        const result = await verifier.verifyUSDCPayment(
            TX_HASH as `0x${string}`,
            FROM as `0x${string}`,
            TO as `0x${string}`,
            AMOUNT
        );

        console.log('Verification result:', result);

        expect(result.isValid).toBe(true);
        expect(result.amount).toBeGreaterThanOrEqual(AMOUNT);
        expect(result.from?.toLowerCase()).toBe(FROM.toLowerCase());
        expect(result.to?.toLowerCase()).toBe(TO.toLowerCase());
    });
});
