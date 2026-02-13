/**
 * ITokenPriceOracle
 * 
 * Standard interface for token price oracles.
 * Enables swappable implementations: Mock → Chainlink → Uniswap TWAP
 */
export interface ITokenPriceOracle {
    /**
     * Returns how many COMP tokens equal 1 Wei of ETH
     * 
     * Example: If 1 COMP = 0.01 ETH
     * Then 1 ETH = 100 COMP
     * Returns: 100 * 10^18 (in COMP decimals)
     * 
     * @returns COMP amount per 1 Wei ETH (18 decimals)
     */
    getCOMPPerETH(): Promise<bigint>;

    /**
     * Returns USDC (6 decimals) per COMP (18 decimals)
     * For display and conversion purposes
     * 
     * Example: If 1 COMP = $0.10 USD
     * Returns: 100000 (0.10 USD in USDC 6 decimals)
     * 
     * @returns USDC amount per 1 COMP (6 decimals)
     */
    getUSDCPerCOMP(): Promise<bigint>;
}
