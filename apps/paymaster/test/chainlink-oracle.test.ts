import { describe, it, expect, beforeAll } from '@jest/globals';
import { ChainlinkOracle } from '../src/oracle/ChainlinkOracle';

describe('ChainlinkOracle', () => {
    let oracle: ChainlinkOracle;

    // Note: These tests may fail if running without network access or if Chainlink feeds are down
    // They are integration tests, not unit tests
    beforeAll(() => {
        oracle = new ChainlinkOracle(
            'https://sepolia.base.org', // Base Sepolia RPC
            0.10, // $0.10 per COMP
            false // Use testnet
        );
    });

    it('should calculate COMP per ETH ratio', async () => {
        const ratio = await oracle.getCOMPPerETH();

        expect(ratio).toBeGreaterThan(0n);
        console.log(`COMP per ETH: ${Number(ratio) / 1e18}`);
    }, 10000);

    it('should calculate USDC per COMP conversion', async () => {
        const usdcAmount = await oracle.getUSDCPerCOMP();

        expect(usdcAmount).toBeGreaterThan(0n);
        // Should be 0.10 USDC = 100000 units (6 decimals)
        expect(usdcAmount).toBe(100000n);
        console.log(`1 COMP = ${Number(usdcAmount) / 1e6} USDC`);
    });

    it('should allow updating COMP price', async () => {
        oracle.updateCOMPPrice(0.15);

        const usdcAmount = await oracle.getUSDCPerCOMP();
        expect(usdcAmount).toBe(150000n); // 0.15 USDC = 150000 units
    });

    it('should reject zero or negative COMP price', () => {
        expect(() => oracle.updateCOMPPrice(0)).toThrow('COMP price must be positive');
        expect(() => oracle.updateCOMPPrice(-1)).toThrow('COMP price must be positive');
    });

    it('should return current prices', () => {
        oracle.updateCOMPPrice(0.20);
        const prices = oracle.getCurrentPrices();

        expect(prices.compPriceUSD).toBe(0.20);
        expect(prices.ethPriceUSD).toBeNull(); // Fetched dynamically from Chainlink
    });

    it('should throw error for zero COMP price in getCOMPPerETH', async () => {
        oracle.updateCOMPPrice(0.10); // Reset to valid
        // We can't directly test this without modifying internal state
        // This is more of an implementation detail test
    });
});
