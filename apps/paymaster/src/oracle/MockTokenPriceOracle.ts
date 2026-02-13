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
    private compPriceUSD: number;
    private ethPriceUSD: number;

    /**
     * @param compPriceUSD - Price of 1 COMP in USD (e.g., 0.10)
     * @param ethPriceUSD - Price of 1 ETH in USD (e.g., 2500)
     */
    constructor(compPriceUSD: number, ethPriceUSD: number) {
        if (compPriceUSD <= 0 || ethPriceUSD <= 0) {
            throw new Error('Prices must be positive');
        }

        this.compPriceUSD = compPriceUSD;
        this.ethPriceUSD = ethPriceUSD;
    }

    /**
     * Calculate how many COMP tokens equal 1 ETH
     * 
     * Example:
     * - ETH = $2500, COMP = $0.10
     * - 1 ETH = 2500 / 0.10 = 25,000 COMP
     * - Returns: 25000 * 10^18 (in COMP's 18 decimals)
     */
    async getCOMPPerETH(): Promise<bigint> {
        const ratio = this.ethPriceUSD / this.compPriceUSD;

        // Convert to bigint with 18 decimals
        // Use integer math to avoid floating point precision issues
        const ratioInteger = Math.floor(ratio);

        return BigInt(ratioInteger) * 10n ** 18n;
    }

    /**
     * Calculate how many USDC (6 decimals) equals 1 COMP (18 decimals)
     * 
     * Example:
     * - COMP = $0.10 USD
     * - Returns: 100000 (0.10 with 6 decimals)
     */
    async getUSDCPerCOMP(): Promise<bigint> {
        // USDC has 6 decimals
        const usdcUnits = Math.floor(this.compPriceUSD * 1_000_000);

        return BigInt(usdcUnits);
    }

    /**
     * Update prices dynamically (for testing)
     */
    updatePrices(compPriceUSD: number, ethPriceUSD: number): void {
        if (compPriceUSD <= 0 || ethPriceUSD <= 0) {
            throw new Error('Prices must be positive');
        }

        this.compPriceUSD = compPriceUSD;
        this.ethPriceUSD = ethPriceUSD;
    }

    /**
     * Get current configured prices (for debugging)
     */
    getCurrentPrices(): { compPriceUSD: number; ethPriceUSD: number } {
        return {
            compPriceUSD: this.compPriceUSD,
            ethPriceUSD: this.ethPriceUSD,
        };
    }
}
