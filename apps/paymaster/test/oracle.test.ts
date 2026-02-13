import { describe, it, expect, beforeEach } from '@jest/globals';
import { MockTokenPriceOracle } from '../src/oracle/MockTokenPriceOracle';

describe('MockTokenPriceOracle', () => {
    let oracle: MockTokenPriceOracle;

    beforeEach(() => {
        // Default: ETH = $2500, COMP = $0.10
        oracle = new MockTokenPriceOracle(0.10, 2500);
    });

    describe('getCOMPPerETH', () => {
        it('should return correct COMP per ETH ratio', async () => {
            // Given: ETH = $2500, COMP = $0.10
            // Expected: 1 ETH = 25,000 COMP

            const result = await oracle.getCOMPPerETH();

            // Should return 25000 * 10^18 (in COMP decimals)
            expect(result).toBe(25000n * 10n ** 18n);
        });

        it('should handle different price ratios correctly', async () => {
            // Given: ETH = $3000, COMP = $0.15
            // Expected: 1 ETH = 20,000 COMP

            const oracle2 = new MockTokenPriceOracle(0.15, 3000);
            const result = await oracle2.getCOMPPerETH();

            expect(result).toBe(20000n * 10n ** 18n);
        });

        it('should handle price updates dynamically', async () => {
            // Initial: 1 ETH = 25,000 COMP
            let result = await oracle.getCOMPPerETH();
            expect(result).toBe(25000n * 10n ** 18n);

            // Update prices: ETH = $5000, COMP = $0.25
            // New ratio: 1 ETH = 20,000 COMP
            oracle.updatePrices(0.25, 5000);

            result = await oracle.getCOMPPerETH();
            expect(result).toBe(20000n * 10n ** 18n);
        });

        it('should handle high ETH to low COMP ratio', async () => {
            // Edge case: Very cheap COMP
            // ETH = $2500, COMP = $0.01
            // Expected: 1 ETH = 250,000 COMP

            const oracle2 = new MockTokenPriceOracle(0.01, 2500);
            const result = await oracle2.getCOMPPerETH();

            expect(result).toBe(250000n * 10n ** 18n);
        });
    });

    describe('getUSDCPerCOMP', () => {
        it('should return correct USDC per COMP conversion', async () => {
            // Given: COMP = $0.10 USD
            // Expected: 100,000 USDC units (6 decimals)

            const result = await oracle.getUSDCPerCOMP();

            expect(result).toBe(100000n);
        });

        it('should handle different COMP prices', async () => {
            // Given: COMP = $0.50 USD
            // Expected: 500,000 USDC units

            const oracle2 = new MockTokenPriceOracle(0.50, 2500);
            const result = await oracle2.getUSDCPerCOMP();

            expect(result).toBe(500000n);
        });

        it('should handle fractional USDC amounts correctly', async () => {
            // Given: COMP = $0.123456 USD
            // Expected: 123,456 USDC units (truncated to 6 decimals)

            const oracle2 = new MockTokenPriceOracle(0.123456, 2500);
            const result = await oracle2.getUSDCPerCOMP();

            expect(result).toBe(123456n);
        });

        it('should handle very small COMP prices', async () => {
            // Given: COMP = $0.001 USD
            // Expected: 1,000 USDC units

            const oracle2 = new MockTokenPriceOracle(0.001, 2500);
            const result = await oracle2.getUSDCPerCOMP();

            expect(result).toBe(1000n);
        });
    });

    describe('Price validation', () => {
        it('should throw error for zero COMP price', () => {
            expect(() => {
                new MockTokenPriceOracle(0, 2500);
            }).toThrow('Prices must be positive');
        });

        it('should throw error for negative ETH price', () => {
            expect(() => {
                new MockTokenPriceOracle(0.10, -2500);
            }).toThrow('Prices must be positive');
        });

        it('should throw error when updating to zero price', () => {
            expect(() => {
                oracle.updatePrices(0, 2500);
            }).toThrow('Prices must be positive');
        });
    });

    describe('getCurrentPrices', () => {
        it('should return current configured prices', () => {
            const prices = oracle.getCurrentPrices();

            expect(prices.compPriceUSD).toBe(0.10);
            expect(prices.ethPriceUSD).toBe(2500);
        });

        it('should reflect updated prices', () => {
            oracle.updatePrices(0.20, 3000);

            const prices = oracle.getCurrentPrices();

            expect(prices.compPriceUSD).toBe(0.20);
            expect(prices.ethPriceUSD).toBe(3000);
        });
    });

    describe('Real-world scenarios', () => {
        it('should calculate fees correctly for typical transaction', async () => {
            // Scenario: Transaction costs 0.001 ETH in gas
            // ETH = $2500, COMP = $0.10
            // Gas cost in USD: 0.001 * 2500 = $2.50
            // Required COMP: 2.50 / 0.10 = 25 COMP

            const gasCostWei = 10n ** 15n; //  0.001 ETH
            const compPerWei = await oracle.getCOMPPerETH();

            // Calculate required COMP for gas
            const requiredCOMP = (gasCostWei * compPerWei) / 10n ** 18n;

            expect(requiredCOMP).toBe(25n * 10n ** 18n); // 25 COMP
        });

        it('should handle very expensive transaction', async () => {
            // Scenario: Complex transaction costs 0.1 ETH
            // Expected: 2,500 COMP

            const gasCostWei = 10n ** 17n; // 0.1 ETH
            const compPerWei = await oracle.getCOMPPerETH();

            const requiredCOMP = (gasCostWei * compPerWei) / 10n ** 18n;

            expect(requiredCOMP).toBe(2500n * 10n ** 18n); // 2,500 COMP
        });
    });
});
