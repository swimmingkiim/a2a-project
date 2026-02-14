import { ITokenPriceOracle } from './ITokenPriceOracle';

/**
 * MockTokenPriceOracle
 * 
 * Simple configurable price oracle for testing and development.
 * Uses static USD prices to calculate token ratios.
 * 
 * ⚠️ NOT FOR PRODUCTION - Use Chainlink or Uniswap TWAP in production
 */
export class MockTokenPriceOracle implements ITokenPriceOracle {
    private daimPriceUSD: number;
    private ethPriceUSD: number;

    /**
     * @param daimPriceUSD - Price of 1 DAIM in USD (e.g., 0.10)
     * @param ethPriceUSD - Price of 1 ETH in USD (e.g., 2500)
     */
    constructor(daimPriceUSD: number, ethPriceUSD: number) {
        if (daimPriceUSD <= 0 || ethPriceUSD <= 0) {
            throw new Error('Prices must be positive');
        }

        this.daimPriceUSD = daimPriceUSD;
        this.ethPriceUSD = ethPriceUSD;
    }

    /**
     * Calculate how many DAIM tokens equal 1 ETH
     * 
     * Example:
     * - ETH = $2500, DAIM = $0.10
     * - 1 ETH = 2500 / 0.10 = 25,000 DAIM
     * - Returns: 25000 * 10^18 (in DAIM's 18 decimals)
     */
    async getDAIMPerETH(): Promise<bigint> {
        const ratio = this.ethPriceUSD / this.daimPriceUSD;

        // Convert to bigint with 18 decimals
        // Use integer math to avoid floating point precision issues
        const ratioInteger = Math.floor(ratio);

        return BigInt(ratioInteger) * 10n ** 18n;
    }

    /**
     * Calculate how many USDC (6 decimals) equals 1 DAIM (18 decimals)
     * 
     * Example:
     * - DAIM = $0.10 USD
     * - Returns: 100000 (0.10 with 6 decimals)
     */
    async getUSDCPerDAIM(): Promise<bigint> {
        // USDC has 6 decimals
        const usdcUnits = Math.floor(this.daimPriceUSD * 1_000_000);

        return BigInt(usdcUnits);
    }

    /**
     * Update prices dynamically (for testing)
     */
    updatePrices(daimPriceUSD: number, ethPriceUSD: number): void {
        if (daimPriceUSD <= 0 || ethPriceUSD <= 0) {
            throw new Error('Prices must be positive');
        }

        this.daimPriceUSD = daimPriceUSD;
        this.ethPriceUSD = ethPriceUSD;
    }

    /**
     * Get current configured prices (for debugging)
     */
    getCurrentPrices(): { daimPriceUSD: number; ethPriceUSD: number } {
        return {
            daimPriceUSD: this.daimPriceUSD,
            ethPriceUSD: this.ethPriceUSD,
        };
    }
}
