import { describe, it, expect, beforeEach } from "@jest/globals";
import { MockTokenPriceOracle } from "../src/oracle/MockTokenPriceOracle";

describe("MockTokenPriceOracle", () => {
  let oracle: MockTokenPriceOracle;

  beforeEach(() => {
    // Default: ETH = $2500, DAIM = $0.10
    oracle = new MockTokenPriceOracle(0.1, 2500);
  });

  describe("getDAIMPerETH", () => {
    it("should return correct DAIM per ETH ratio", async () => {
      // Given: ETH = $2500, DAIM = $0.10
      // Expected: 1 ETH = 25,000 DAIM

      const result = await oracle.getDAIMPerETH();

      // Should return 25000 * 10^18 (in DAIM decimals)
      expect(result).toBe(25000n * 10n ** 18n);
    });

    it("should handle different price ratios correctly", async () => {
      // Given: ETH = $3000, DAIM = $0.15
      // Expected: 1 ETH = 20,000 DAIM

      const oracle2 = new MockTokenPriceOracle(0.15, 3000);
      const result = await oracle2.getDAIMPerETH();

      expect(result).toBe(20000n * 10n ** 18n);
    });

    it("should handle price updates dynamically", async () => {
      // Initial: 1 ETH = 25,000 DAIM
      let result = await oracle.getDAIMPerETH();
      expect(result).toBe(25000n * 10n ** 18n);

      // Update prices: ETH = $5000, DAIM = $0.25
      // New ratio: 1 ETH = 20,000 DAIM
      oracle.updatePrices(0.25, 5000);

      result = await oracle.getDAIMPerETH();
      expect(result).toBe(20000n * 10n ** 18n);
    });

    it("should handle high ETH to low DAIM ratio", async () => {
      // Edge case: Very cheap DAIM
      // ETH = $2500, DAIM = $0.01
      // Expected: 1 ETH = 250,000 DAIM

      const oracle2 = new MockTokenPriceOracle(0.01, 2500);
      const result = await oracle2.getDAIMPerETH();

      expect(result).toBe(250000n * 10n ** 18n);
    });
  });

  describe("getUSDCPerDAIM", () => {
    it("should return correct USDC per DAIM conversion", async () => {
      // Given: DAIM = $0.10 USD
      // Expected: 100,000 USDC units (6 decimals)

      const result = await oracle.getUSDCPerDAIM();

      expect(result).toBe(100000n);
    });

    it("should handle different DAIM prices", async () => {
      // Given: DAIM = $0.50 USD
      // Expected: 500,000 USDC units

      const oracle2 = new MockTokenPriceOracle(0.5, 2500);
      const result = await oracle2.getUSDCPerDAIM();

      expect(result).toBe(500000n);
    });

    it("should handle fractional USDC amounts correctly", async () => {
      // Given: DAIM = $0.123456 USD
      // Expected: 123,456 USDC units (truncated to 6 decimals)

      const oracle2 = new MockTokenPriceOracle(0.123456, 2500);
      const result = await oracle2.getUSDCPerDAIM();

      expect(result).toBe(123456n);
    });

    it("should handle very small DAIM prices", async () => {
      // Given: DAIM = $0.001 USD
      // Expected: 1,000 USDC units

      const oracle2 = new MockTokenPriceOracle(0.001, 2500);
      const result = await oracle2.getUSDCPerDAIM();

      expect(result).toBe(1000n);
    });
  });

  describe("Price validation", () => {
    it("should throw error for zero DAIM price", () => {
      expect(() => {
        new MockTokenPriceOracle(0, 2500);
      }).toThrow("Prices must be positive");
    });

    it("should throw error for negative ETH price", () => {
      expect(() => {
        new MockTokenPriceOracle(0.1, -2500);
      }).toThrow("Prices must be positive");
    });

    it("should throw error when updating to zero price", () => {
      expect(() => {
        oracle.updatePrices(0, 2500);
      }).toThrow("Prices must be positive");
    });
  });

  // getCurrentPrices returns private fields exposed via getter, assumed to be renamed?
  // Checking MockTokenPriceOracle source: it has getCurrentPrices() returning { daimPriceUSD, ethPriceUSD }
  describe("getCurrentPrices", () => {
    it("should return current configured prices", () => {
      const prices = oracle.getCurrentPrices();

      expect(prices.daimPriceUSD).toBe(0.1);
      expect(prices.ethPriceUSD).toBe(2500);
    });

    it("should reflect updated prices", () => {
      oracle.updatePrices(0.2, 3000);

      const prices = oracle.getCurrentPrices();

      expect(prices.daimPriceUSD).toBe(0.2);
      expect(prices.ethPriceUSD).toBe(3000);
    });
  });

  describe("Real-world scenarios", () => {
    it("should calculate fees correctly for typical transaction", async () => {
      // Scenario: Transaction costs 0.001 ETH in gas
      // ETH = $2500, DAIM = $0.10
      // Gas cost in USD: 0.001 * 2500 = $2.50
      // Required DAIM: 2.50 / 0.10 = 25 DAIM

      const gasCostWei = 10n ** 15n; //  0.001 ETH
      const daimPerWei = await oracle.getDAIMPerETH();

      // Calculate required DAIM for gas
      const requiredDAIM = (gasCostWei * daimPerWei) / 10n ** 18n;

      expect(requiredDAIM).toBe(25n * 10n ** 18n); // 25 DAIM
    });

    it("should handle very expensive transaction", async () => {
      // Scenario: Complex transaction costs 0.1 ETH
      // Expected: 2,500 DAIM

      const gasCostWei = 10n ** 17n; // 0.1 ETH
      const daimPerWei = await oracle.getDAIMPerETH();

      const requiredDAIM = (gasCostWei * daimPerWei) / 10n ** 18n;

      expect(requiredDAIM).toBe(2500n * 10n ** 18n); // 2,500 DAIM
    });
  });
});
