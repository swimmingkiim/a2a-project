import { ITokenPriceOracle } from './ITokenPriceOracle';
import { ChainlinkOracle } from './ChainlinkOracle';
import { MockTokenPriceOracle } from './MockTokenPriceOracle';

/**
 * Hybrid Oracle with Chainlink primary + Mock fallback
 * 
 * Attempts to use Chainlink for production accuracy,
 * falls back to Mock oracle if Chainlink fails.
 */
export class HybridOracle implements ITokenPriceOracle {
    private failoverCount = 0;
    private lastFailoverTime = 0;

    constructor(
        private chainlinkOracle: ChainlinkOracle,
        private mockOracle: MockTokenPriceOracle,
        private maxFailoversPerHour: number = 10
    ) { }

    async getCOMPPerETH(): Promise<bigint> {
        try {
            const ratio = await this.chainlinkOracle.getCOMPPerETH();
            this.resetFailoverCount();
            return ratio;
        } catch (error) {
            return this.handleFailover('getCOMPPerETH', async () => {
                return await this.mockOracle.getCOMPPerETH();
            }, error);
        }
    }

    async getUSDCPerCOMP(): Promise<bigint> {
        try {
            const usdc = await this.chainlinkOracle.getUSDCPerCOMP();
            this.resetFailoverCount();
            return usdc;
        } catch (error) {
            return this.handleFailover('getUSDCPerCOMP', async () => {
                return await this.mockOracle.getUSDCPerCOMP();
            }, error);
        }
    }

    private async handleFailover<T>(
        method: string,
        fallbackFn: () => Promise<T>,
        error: any
    ): Promise<T> {
        const now = Date.now();
        if (now - this.lastFailoverTime > 3600000) {
            this.failoverCount = 0;
        }

        this.failoverCount++;
        this.lastFailoverTime = now;

        if (this.failoverCount > this.maxFailoversPerHour) {
            console.error(`[HybridOracle] Too many failovers (${this.failoverCount}). System unstable.`);
            throw new Error(`Oracle failover limit exceeded: ${error}`);
        }

        console.warn(`[HybridOracle] Chainlink failed for ${method}, using Mock fallback (${this.failoverCount}/${this.maxFailoversPerHour}):`, error.message);

        return await fallbackFn();
    }

    private resetFailoverCount(): void {
        if (this.failoverCount > 0) {
            console.log(`[HybridOracle] Chainlink recovered. Resetting failover count.`);
            this.failoverCount = 0;
        }
    }

    getFailoverStats(): { count: number; maxPerHour: number; lastFailover: number } {
        return {
            count: this.failoverCount,
            maxPerHour: this.maxFailoversPerHour,
            lastFailover: this.lastFailoverTime
        };
    }
}
