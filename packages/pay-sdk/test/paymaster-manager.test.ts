import { describe, it, expect, beforeEach } from 'vitest';
import { PaymasterManager, FeeConfig } from '../src/paymaster/paymaster';
import { encodeFunctionData, parseAbi } from 'viem';

describe('PaymasterManager.appendFeeToCalls', () => {
    it('should append USDC fee call correctly', () => {
        const calls: any[] = [];
        const feeConfig: FeeConfig = {
            treasury: '0x1234567890123456789012345678901234567890',
            amount: 100000n, // 0.1 USDC
            tokenType: 'USDC'
        };

        const result = PaymasterManager.appendFeeToCalls(calls, feeConfig);

        expect(result.length).toBe(1);
        expect(result[0].to).toBe('0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'); // USDC on Base
        expect(result[0].value).toBe(0n);

        // Verify transfer encoding
        const ERC20_ABI = parseAbi(['function transfer(address to, uint256 amount) returns (bool)']);
        const expectedData = encodeFunctionData({
            abi: ERC20_ABI,
            functionName: 'transfer',
            args: [feeConfig.treasury, feeConfig.amount]
        });

        expect(result[0].data).toBe(expectedData);
    });

    it('should append COMP fee call correctly', () => {
        const calls: any[] = [];
        const feeConfig: FeeConfig = {
            treasury: '0x1234567890123456789012345678901234567890',
            amount: 25n * 10n ** 18n, // 25 COMP
            tokenType: 'COMP'
        };

        const result = PaymasterManager.appendFeeToCalls(calls, feeConfig);

        expect(result.length).toBe(1);
        expect(result[0].to).toBe('0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3'); // COMP on Base Sepolia
        expect(result[0].value).toBe(0n);
    });

    it('should support custom token address override', () => {
        const customTokenAddress = '0x9999999999999999999999999999999999999999';
        const calls: any[] = [];
        const feeConfig: FeeConfig = {
            treasury: '0x1234567890123456789012345678901234567890',
            amount: 100000n,
            tokenType: 'USDC',
            tokenAddress: customTokenAddress
        };

        const result = PaymasterManager.appendFeeToCalls(calls, feeConfig);

        expect(result.length).toBe(1);
        expect(result[0].to).toBe(customTokenAddress);
    });

    it('should preserve existing calls', () => {
        const existingCall = {
            to: '0xabcd...',
            value: 0n,
            data: '0x1234'
        };

        const calls = [existingCall];

        const feeConfig: FeeConfig = {
            treasury: '0x1234567890123456789012345678901234567890',
            amount: 100000n,
            tokenType: 'USDC'
        };

        const result = PaymasterManager.appendFeeToCalls(calls, feeConfig);

        expect(result.length).toBe(2);
        expect(result[0]).toBe(existingCall); // Original call preserved
        expect(result[1].to).toBe('0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'); // Fee call appended
    });
});
