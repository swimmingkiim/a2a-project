import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { USDCFeeValidator } from '../src/fee-validation/USDCFeeValidator';
import { COMPFeeValidator } from '../src/fee-validation/COMPFeeValidator';
import { MockTokenPriceOracle } from '../src/oracle/MockTokenPriceOracle';
import { encodeFunctionData, parseAbi, createPublicClient, http } from 'viem';

const ERC20_ABI = parseAbi(['function transfer(address to, uint256 amount) returns (bool)']);
const BATCH_EXECUTE_ABI = parseAbi(['function executeBatch(address[] dest, uint256[] value, bytes[] func)']);

describe('Fee Validators', () => {
    const TREASURY_ADDR = '0x1234567890123456789012345678901234567890';
    const USDC_TOKEN_ADDR = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';
    const COMP_TOKEN_ADDR = '0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3';

    // Mock client
    const mockClient: any = {
        readContract: jest.fn().mockResolvedValue(0n), // L1 fee = 0 for simplicity
    };

    describe('USDCFeeValidator', () => {
        let validator: USDCFeeValidator;

        beforeEach(() => {
            validator = new USDCFeeValidator({
                treasuryAddress: TREASURY_ADDR,
                usdcTokenAddress: USDC_TOKEN_ADDR,
                floorFeeAmount: '100000', // 0.1 USDC
                ethPriceUSD: '2500',
                markupRate: 0.1, // 10% markup
            });
        });

        it('should validate correct USDC fee in executeBatch', async () => {
            // Create a UserOp with executeBatch calling USDC transfer
            // Transfer 100000 USDC (floor fee) - gas will be low enough to use floor
            const transferCallData = encodeFunctionData({
                abi: ERC20_ABI,
                functionName: 'transfer',
                args: [TREASURY_ADDR, 100000n], // 0.1 USDC (floor)
            });

            const batchCallData = encodeFunctionData({
                abi: BATCH_EXECUTE_ABI,
                functionName: 'executeBatch',
                args: [
                    [USDC_TOKEN_ADDR], // destinations
                    [0n], // values
                    [transferCallData], // function calls
                ],
            });

            // Use minimal gas settings to trigger floor fee (100,000 USDC)
            const userOp = {
                sender: '0xSender123',
                callData: batchCallData,
                preVerificationGas: '1000', // Very low to trigger floor fee
                verificationGasLimit: '1000',
                callGasLimit: '1000',
                maxFeePerGas: '1000000000', // 1 gwei
            };

            const result = await validator.validateFeeIncluded(userOp, mockClient);

            expect(result).toBe(true);
        });

        it('should reject insufficient USDC fee', async () => {
            // Transfer only 50000 USDC units (0.05 USDC) - below floor
            const transferCallData = encodeFunctionData({
                abi: ERC20_ABI,
                functionName: 'transfer',
                args: [TREASURY_ADDR, 50000n],
            });

            const batchCallData = encodeFunctionData({
                abi: BATCH_EXECUTE_ABI,
                functionName: 'executeBatch',
                args: [[USDC_TOKEN_ADDR], [0n], [transferCallData]],
            });

            const userOp = {
                sender: '0xSender123',
                callData: batchCallData,
                preVerificationGas: '50000',
                verificationGasLimit: '100000',
                callGasLimit: '50000',
                maxFeePerGas: '1000000000',
            };

            const result = await validator.validateFeeIncluded(userOp, mockClient);

            expect(result).toBe(false);
        });

        it('should reject fee to wrong recipient', async () => {
            const WRONG_ADDR = '0x9999999999999999999999999999999999999999';

            const transferCallData = encodeFunctionData({
                abi: ERC20_ABI,
                functionName: 'transfer',
                args: [WRONG_ADDR, 100000n], // Correct amount, wrong recipient
            });

            const batchCallData = encodeFunctionData({
                abi: BATCH_EXECUTE_ABI,
                functionName: 'executeBatch',
                args: [[USDC_TOKEN_ADDR], [0n], [transferCallData]],
            });

            const userOp = {
                sender: '0xSender123',
                callData: batchCallData,
                preVerificationGas: '50000',
                verificationGasLimit: '100000',
                callGasLimit: '50000',
                maxFeePerGas: '1000000000',
            };

            const result = await validator.validateFeeIncluded(userOp, mockClient);

            expect(result).toBe(false);
        });
    });

    describe('COMPFeeValidator', () => {
        let validator: COMPFeeValidator;
        let oracle: MockTokenPriceOracle;

        beforeEach(() => {
            // ETH = $2500, COMP = $0.10 → 1 ETH = 25,000 COMP
            oracle = new MockTokenPriceOracle(0.10, 2500);

            validator = new COMPFeeValidator(
                {
                    treasuryAddress: TREASURY_ADDR,
                    compTokenAddress: COMP_TOKEN_ADDR,
                    markupRate: 0.1, // 10% markup
                },
                oracle
            );
        });

        it('should validate correct COMP fee based on oracle price', async () => {
            // Scenario: Gas cost = 0.001 ETH
            // At 1 ETH = 25,000 COMP → 0.001 ETH = 25 COMP
            // With 10% markup → 27.5 COMP

            const expectedCOMP = 28n * 10n ** 18n; // Round up for safety

            const transferCallData = encodeFunctionData({
                abi: ERC20_ABI,
                functionName: 'transfer',
                args: [TREASURY_ADDR, expectedCOMP],
            });

            const batchCallData = encodeFunctionData({
                abi: BATCH_EXECUTE_ABI,
                functionName: 'executeBatch',
                args: [[COMP_TOKEN_ADDR], [0n], [transferCallData]],
            });

            const userOp = {
                sender: '0xSender123',
                callData: batchCallData,
                preVerificationGas: '100000',
                verificationGasLimit: '200000',
                callGasLimit: '100000',
                maxFeePerGas: '2500000000', // 2.5 gwei → ~0.001 ETH total
            };

            const result = await validator.validateFeeIncluded(userOp, mockClient);

            expect(result).toBe(true);
        });

        it('should reject insufficient COMP fee', async () => {
            // Only send 10 COMP when ~28 COMP required
            const insufficientCOMP = 10n * 10n ** 18n;

            const transferCallData = encodeFunctionData({
                abi: ERC20_ABI,
                functionName: 'transfer',
                args: [TREASURY_ADDR, insufficientCOMP],
            });

            const batchCallData = encodeFunctionData({
                abi: BATCH_EXECUTE_ABI,
                functionName: 'executeBatch',
                args: [[COMP_TOKEN_ADDR], [0n], [transferCallData]],
            });

            const userOp = {
                sender: '0xSender123',
                callData: batchCallData,
                preVerificationGas: '100000',
                verificationGasLimit: '200000',
                callGasLimit: '100000',
                maxFeePerGas: '2500000000',
            };

            const result = await validator.validateFeeIncluded(userOp, mockClient);

            expect(result).toBe(false);
        });

        it('should recalculate when oracle price changes', async () => {
            // Initial: 1 ETH = 25,000 COMP
            // After update: 1 ETH = 20,000 COMP (COMP price increased to $0.125)

            oracle.updatePrices(0.125, 2500);

            // Now for 0.001 ETH → 20 COMP (base) → 22 COMP (with 10% markup)
            const newExpectedCOMP = 23n * 10n ** 18n;

            const transferCallData = encodeFunctionData({
                abi: ERC20_ABI,
                functionName: 'transfer',
                args: [TREASURY_ADDR, newExpectedCOMP],
            });

            const batchCallData = encodeFunctionData({
                abi: BATCH_EXECUTE_ABI,
                functionName: 'executeBatch',
                args: [[COMP_TOKEN_ADDR], [0n], [transferCallData]],
            });

            const userOp = {
                sender: '0xSender123',
                callData: batchCallData,
                preVerificationGas: '100000',
                verificationGasLimit: '200000',
                callGasLimit: '100000',
                maxFeePerGas: '2500000000',
            };

            const result = await validator.validateFeeIncluded(userOp, mockClient);

            expect(result).toBe(true);
        });
    });

    describe('Backward Compatibility', () => {
        it('should preserve existing USDC validation behavior', async () => {
            // This test ensures refactoring didn't break existing logic
            const validator = new USDCFeeValidator({
                treasuryAddress: TREASURY_ADDR,
                usdcTokenAddress: USDC_TOKEN_ADDR,
                floorFeeAmount: '100000',
                ethPriceUSD: '2500',
                markupRate: 0.1,
            });

            const transferCallData = encodeFunctionData({
                abi: ERC20_ABI,
                functionName: 'transfer',
                args: [TREASURY_ADDR, 100000n],
            });

            const batchCallData = encodeFunctionData({
                abi: BATCH_EXECUTE_ABI,
                functionName: 'executeBatch',
                args: [[USDC_TOKEN_ADDR], [0n], [transferCallData]],
            });

            // Use minimal gas settings to trigger floor fee behavior
            const userOp = {
                sender: '0xSender123',
                callData: batchCallData,
                preVerificationGas: '1000',
                verificationGasLimit: '1000',
                callGasLimit: '1000',
                maxFeePerGas: '1000000000',
            };

            const result = await validator.validateFeeIncluded(userOp, mockClient);

            // Should pass exactly as before refactoring
            expect(result).toBe(true);
        });
    });
});
