/**
 * ITokenPriceOracle
 *
 * Standard interface for token price oracles.
 * Enables swappable implementations: Mock → Chainlink → Uniswap TWAP
 */
export interface ITokenPriceOracle {
  /**
   * Returns how many DAIM tokens equal 1 Wei of ETH
   *
   * Example: If 1 DAIM = 0.01 ETH
   * Then 1 ETH = 100 DAIM
   * Returns: 100 * 10^18 (in DAIM decimals)
   *
   * @returns DAIM amount per 1 Wei ETH (18 decimals)
   */
  getDAIMPerETH(): Promise<bigint>;

  /**
   * Returns USDC (6 decimals) per DAIM (18 decimals)
   * For display and conversion purposes
   *
   * Example: If 1 DAIM = $0.10 USD
   * Returns: 100000 (0.10 USD in USDC 6 decimals)
   *
   * @returns USDC amount per 1 DAIM (6 decimals)
   */
  getUSDCPerDAIM(): Promise<bigint>;
}
