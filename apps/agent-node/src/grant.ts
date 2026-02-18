import {
  createWalletClient,
  createPublicClient,
  http,
  parseAbi,
  parseEther,
  isAddress,
} from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { baseSepolia } from "viem/chains"; // Default to testnet, configurable

// Environment variables
const PRIVATE_KEY = process.env.GRANT_PRIVATE_KEY || process.env.AIRDROP_PRIVATE_KEY; // Fallback for backward compatibility
const RPC_URL = process.env.RPC_URL || "https://sepolia.base.org";
const GRANT_AMOUNT = process.env.GRANT_AMOUNT || "100"; // 100 Tokens (updated as per previous UI)
const TOKEN_ADDRESS =
  process.env.GRANT_TOKEN_ADDRESS ||
  process.env.AIRDROP_TOKEN_ADDRESS ||
  "0x036CbD53842c5426634e7929541eC2318f3dCF7e"; // Default or Mock

// ERC20 ABI (Minimal)
const ERC20_ABI = parseAbi([
  "function transfer(address to, uint256 amount) returns (bool)",
  "function balanceOf(address account) view returns (uint256)",
  "function decimals() view returns (uint8)",
]);

export class GrantService {
  private walletClient: any;
  private publicClient: any;
  private account: any;
  private enabled: boolean = false;

  constructor() {
    if (!PRIVATE_KEY) {
      console.warn("[Grant] GRANT_PRIVATE_KEY not set. Grant service disabled.");
      return;
    }

    try {
      this.account = privateKeyToAccount(PRIVATE_KEY as `0x${string}`);
      this.publicClient = createPublicClient({
        chain: baseSepolia,
        transport: http(RPC_URL),
      });
      this.walletClient = createWalletClient({
        account: this.account,
        chain: baseSepolia,
        transport: http(RPC_URL),
      });
      this.enabled = true;
      console.log(`[Grant] Service initialized. Wallet: ${this.account.address}`);
    } catch (error) {
      console.error("[Grant] Failed to initialize wallet:", error);
    }
  }

  isEnabled() {
    return this.enabled;
  }

  async sendGrant(to: string) {
    if (!this.enabled) {
      throw new Error("Grant service is disabled (Missing Private Key)");
    }

    if (!isAddress(to)) {
      throw new Error(`Invalid recipient address: ${to}`);
    }

    console.log(`[Grant] Sending ${GRANT_AMOUNT} tokens to ${to}...`);

    // Convert amount based on decimals (assuming 18, but ideally check)
    const amount = parseEther(GRANT_AMOUNT);

    try {
      const hash = await this.walletClient.writeContract({
        address: TOKEN_ADDRESS,
        abi: ERC20_ABI,
        functionName: "transfer",
        args: [to, amount],
      });

      console.log(`[Grant] Tx Sent: ${hash}`);
      return hash;
    } catch (error: any) {
      console.error("[Grant] Transaction Failed:", error);
      throw new Error(`Grant Failed: ${error.message}`);
    }
  }

  async getBalance() {
    if (!this.enabled) return "0";
    try {
      const balance = await this.publicClient.readContract({
        address: TOKEN_ADDRESS,
        abi: ERC20_ABI,
        functionName: "balanceOf",
        args: [this.account.address],
      });
      return balance.toString();
    } catch (error) {
      console.error("[Grant] Failed to fetch balance:", error);
      return "Error";
    }
  }
}

export const grantService = new GrantService();
