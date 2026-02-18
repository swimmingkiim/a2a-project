import { createPublicClient, http, PublicClient, parseAbi } from "viem";
import { base, baseSepolia } from "viem/chains";
import { ITokenPriceOracle } from "./ITokenPriceOracle";

/**
 * Chainlink Price Feed Oracle for Base/Base Sepolia
 *
 * Uses Chainlink's battle-tested price feeds for accurate ETH/USD pricing.
 * DAIM price is currently calculated via manual configuration until DAIM/USD feed exists.
 */
export class ChainlinkOracle implements ITokenPriceOracle {
  private client: PublicClient;
  private daimPriceUSD: number;

  // Chainlink Price Feed Addresses
  private static readonly PRICE_FEEDS = {
    // Base Mainnet
    base: {
      ETH_USD: "0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70" as const,
    },
    // Base Sepolia
    baseSepolia: {
      ETH_USD: "0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1" as const,
    },
  };

  private static readonly CHAINLINK_ABI = parseAbi([
    "function latestRoundData() external view returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound)",
    "function decimals() external view returns (uint8)",
  ]);

  constructor(rpcUrl: string, daimPriceUSD: number, isMainnet: boolean = false) {
    this.client = createPublicClient({
      chain: isMainnet ? base : baseSepolia,
      transport: http(rpcUrl),
    }) as PublicClient;
    this.daimPriceUSD = daimPriceUSD;
  }

  /**
   * Calculate how many DAIM tokens equal 1 ETH
   * Uses Chainlink for ETH/USD, configured price for DAIM/USD
   */
  async getDAIMPerETH(): Promise<bigint> {
    const ethPriceUSD = await this.getETHPriceFromChainlink();

    if (this.daimPriceUSD === 0) {
      throw new Error("DAIM price cannot be zero");
    }

    const ratio = ethPriceUSD / this.daimPriceUSD;
    return BigInt(Math.floor(ratio)) * 10n ** 18n;
  }

  /**
   * Calculate how many USDC equals 1 DAIM
   */
  async getUSDCPerDAIM(): Promise<bigint> {
    const usdcUnits = Math.floor(this.daimPriceUSD * 1_000_000);
    return BigInt(usdcUnits);
  }

  /**
   * Get ETH price in USD from Chainlink Oracle
   * Private helper method
   */
  private async getETHPriceFromChainlink(): Promise<number> {
    const chain = this.client.chain?.id === base.id ? "base" : "baseSepolia";
    const feedAddress = ChainlinkOracle.PRICE_FEEDS[chain].ETH_USD;

    try {
      // Get latest round data
      const [roundId, answer, , updatedAt, answeredInRound] = (await this.client.readContract({
        address: feedAddress,
        abi: ChainlinkOracle.CHAINLINK_ABI,
        functionName: "latestRoundData",
      })) as [bigint, bigint, bigint, bigint, bigint];

      // Get decimals (Chainlink USD pairs use 8 decimals)
      const decimals = (await this.client.readContract({
        address: feedAddress,
        abi: ChainlinkOracle.CHAINLINK_ABI,
        functionName: "decimals",
      })) as number;

      // Validate data freshness (should be updated within last hour)
      const now = BigInt(Math.floor(Date.now() / 1000));
      const stalePeriod = 3600n; // 1 hour

      if (now - updatedAt > stalePeriod) {
        console.warn(`[ChainlinkOracle] Stale price data. Last update: ${updatedAt}, now: ${now}`);
      }

      // Validate round completion
      if (answeredInRound < roundId) {
        console.warn(
          `[ChainlinkOracle] Round not complete. RoundId: ${roundId}, AnsweredInRound: ${answeredInRound}`,
        );
      }

      // Convert to USD (handle decimals)
      const price = Number(answer) / Math.pow(10, decimals);

      console.log(
        `[ChainlinkOracle] ETH/USD: $${price.toFixed(2)} (updated: ${new Date(Number(updatedAt) * 1000).toISOString()})`,
      );

      return price;
    } catch (error) {
      console.error("[ChainlinkOracle] Failed to fetch ETH price:", error);
      throw new Error(`Chainlink ETH/USD feed error: ${error}`);
    }
  }

  /**
   * Update DAIM price (for manual configuration)
   */
  updateDAIMPrice(newPrice: number): void {
    if (newPrice <= 0) {
      throw new Error("DAIM price must be positive");
    }

    console.log(`[ChainlinkOracle] Updating DAIM price: $${this.daimPriceUSD} → $${newPrice}`);
    this.daimPriceUSD = newPrice;
  }

  /**
   * Get current configured prices (for debugging)
   */
  getCurrentPrices(): { daimPriceUSD: number; ethPriceUSD: number | null } {
    return {
      daimPriceUSD: this.daimPriceUSD,
      ethPriceUSD: null, // Will be fetched from Chainlink dynamically
    };
  }
}
