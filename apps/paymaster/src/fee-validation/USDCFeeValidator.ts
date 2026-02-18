import { IFeeValidator } from "./IFeeValidator";
import { PublicClient, Hex, decodeFunctionData, parseAbi, isAddressEqual } from "viem";

const ERC20_ABI = parseAbi(["function transfer(address to, uint256 amount) returns (bool)"]);
const BATCH_EXECUTE_ABI = parseAbi([
  "function executeBatch(address[] dest, uint256[] value, bytes[] func)",
]);
const EXECUTE_ABI = parseAbi([
  "function execute(address target, uint256 value, bytes calldata data)",
]);
const SAFE_EXEC_ABI = parseAbi([
  "function execTransaction(address to, uint256 value, bytes data, uint8 operation, uint256 safeTxGas, uint256 baseGas, uint256 gasPrice, address gasToken, address refundReceiver, bytes signatures)",
]);
const SAFE_4337_EXEC_ABI = parseAbi([
  "function executeUserOp(address to, uint256 value, bytes data, uint8 operation)",
  "function executeUserOpWithErrorString(address to, uint256 value, bytes data, uint8 operation)",
]);

const ORACLE_ABI = parseAbi(["function getL1Fee(bytes) view returns (uint256)"]);
const ORACLE_ADDR = "0x420000000000000000000000000000000000000F";

interface USDCFeeConfig {
  treasuryAddress: string;
  usdcTokenAddress: string;
  floorFeeAmount: string; // In USDC units (6 decimals)
  ethPriceUSD: string;
  markupRate: number;
}

/**
 * USDCFeeValidator
 *
 * Validates that UserOperations include proper USDC fee payments.
 * Extracted from original validateFeeIncluded logic.
 */
export class USDCFeeValidator implements IFeeValidator {
  private config: USDCFeeConfig;

  constructor(config: USDCFeeConfig) {
    this.config = config;
  }

  async validateFeeIncluded(userOp: any, client: PublicClient): Promise<boolean> {
    console.log(`[USDC Validator] Checking for embedded USDC fee...`);

    // 1. Calculate Required Fee (Dynamic)
    // This will now throw if L1 fee calculation fails (Security Requirement)
    const requiredFeeUsdc = await this.calculateRequiredFee(userOp, client);

    console.log(`[USDC Validator] Required fee: ${requiredFeeUsdc} USDC`);

    // 2. Check callData for fee transfer
    const callData = userOp.callData as Hex;

    // Try different account execution patterns
    if (await this.checkExecuteBatch(callData, requiredFeeUsdc)) {
      return await this.verifySenderBalance(userOp.sender, requiredFeeUsdc, client);
    }
    if (await this.checkExecute(callData, requiredFeeUsdc)) {
      return await this.verifySenderBalance(userOp.sender, requiredFeeUsdc, client);
    }
    if (await this.checkSafeExecTransaction(callData, requiredFeeUsdc)) {
      return await this.verifySenderBalance(userOp.sender, requiredFeeUsdc, client);
    }
    if (await this.checkSafe4337ExecuteUserOp(callData, requiredFeeUsdc)) {
      return await this.verifySenderBalance(userOp.sender, requiredFeeUsdc, client);
    }

    console.warn(`[USDC Validator] ❌ No valid USDC fee transfer found.`);
    return false;
  }

  private async calculateRequiredFee(userOp: any, client: PublicClient): Promise<bigint> {
    let requiredFeeUsdc = BigInt(this.config.floorFeeAmount); // Default floor

    try {
      // Calculate Total Gas
      const preVerificationGas = BigInt(userOp.preVerificationGas || 0);
      const verificationGasLimit = BigInt(userOp.verificationGasLimit || 0);
      const callGasLimit = BigInt(userOp.callGasLimit || 0);
      const maxFeePerGas = BigInt(userOp.maxFeePerGas || userOp.maxPriorityFeePerGas || 0);

      if (maxFeePerGas > 0n && preVerificationGas + verificationGasLimit + callGasLimit > 0n) {
        const totalGas = preVerificationGas + verificationGasLimit + callGasLimit;

        // Calculate L1 Fee (Oracle) - CRITICAL for Base L2
        let l1Fee = 0n;
        if (userOp.callData) {
          try {
            const l1FeeResult = await client.readContract({
              address: ORACLE_ADDR,
              abi: ORACLE_ABI,
              functionName: "getL1Fee",
              args: [userOp.callData as Hex],
            });
            l1Fee = BigInt(l1FeeResult || 0);
          } catch (e) {
            // [SECURITY FIX] Do NOT ignore L1 calc failure.
            // If we can't calculate L1 fee, we risk under-collecting significantly on L2.
            console.error(`[USDC Validator] ❌ L1 Fee calculation failed:`, e);
            throw new Error("Failed to calculate L1 fee - cannot determine accurate costs");
          }
        }

        const totalCostEthWei = totalGas * maxFeePerGas + l1Fee;

        // Convert to USD (USDC 6 decimals)
        const ethPrice = parseFloat(this.config.ethPriceUSD);
        const ethPriceBig = BigInt(Math.floor(ethPrice * 100)); // 2 decimals precision

        const costUsdc = (totalCostEthWei * ethPriceBig * 1000000n) / 100000000000000000000n;

        // Apply Markup
        const markupBps = BigInt(Math.floor(this.config.markupRate * 10000));
        requiredFeeUsdc = (costUsdc * (10000n + markupBps)) / 10000n;

        // Ensure it doesn't go below floor
        if (requiredFeeUsdc < BigInt(this.config.floorFeeAmount)) {
          requiredFeeUsdc = BigInt(this.config.floorFeeAmount);
        }

        console.log(
          `[USDC Validator] Calculated Cost: ${costUsdc} USDC, Required (w/ Markup): ${requiredFeeUsdc} USDC`,
        );
      }
    } catch (e) {
      console.warn(`[USDC Validator] Failed to calculate dynamic fee:`, e);
      throw e; // Re-throw to prevent "free" transactions if calculation fails
    }

    return requiredFeeUsdc;
  }

  private async checkExecuteBatch(callData: Hex, requiredFeeUsdc: bigint): Promise<boolean> {
    try {
      const decodedBatch = decodeFunctionData({
        abi: BATCH_EXECUTE_ABI,
        data: callData,
      });

      if (decodedBatch.functionName === "executeBatch") {
        const [dests, , funcs] = decodedBatch.args;

        for (let i = 0; i < dests.length; i++) {
          const target = dests[i];
          const data = funcs[i];

          if (isAddressEqual(target, this.config.usdcTokenAddress as Hex)) {
            try {
              const decodedTransfer = decodeFunctionData({
                abi: ERC20_ABI,
                data: data,
              });

              if (decodedTransfer.functionName === "transfer") {
                const [to, amount] = decodedTransfer.args;
                if (
                  isAddressEqual(to, this.config.treasuryAddress as Hex) &&
                  amount >= requiredFeeUsdc
                ) {
                  return true;
                }
              }
            } catch (innerE) {
              // Ignore decoding errors for individual batch items
            }
          }
        }
      }
    } catch (e) {
      // Ignore decoding errors
    }

    return false;
  }

  private async checkExecute(callData: Hex, requiredFeeUsdc: bigint): Promise<boolean> {
    try {
      const decodedExecute = decodeFunctionData({
        abi: EXECUTE_ABI,
        data: callData,
      });

      if (decodedExecute.functionName === "execute") {
        const [target, , data] = decodedExecute.args;

        if (isAddressEqual(target, this.config.usdcTokenAddress as Hex)) {
          const decodedTransfer = decodeFunctionData({
            abi: ERC20_ABI,
            data: data,
          });

          if (decodedTransfer.functionName === "transfer") {
            const [to, amount] = decodedTransfer.args;
            if (
              isAddressEqual(to, this.config.treasuryAddress as Hex) &&
              amount >= requiredFeeUsdc
            ) {
              console.log(`[USDC Validator] ✅ Found valid fee transfer: ${amount.toString()}`);
              return true;
            }
          }
        }
      }
    } catch (e) {
      // Ignore
    }

    return false;
  }

  private async checkSafeExecTransaction(callData: Hex, requiredFeeUsdc: bigint): Promise<boolean> {
    try {
      const decodedSafe = decodeFunctionData({
        abi: SAFE_EXEC_ABI,
        data: callData,
      });

      if (decodedSafe.functionName === "execTransaction") {
        const [toAddress, , data] = decodedSafe.args;

        if (isAddressEqual(toAddress, this.config.usdcTokenAddress as Hex)) {
          const decodedTransfer = decodeFunctionData({
            abi: ERC20_ABI,
            data: data,
          });

          if (decodedTransfer.functionName === "transfer") {
            const [recipient, amount] = decodedTransfer.args;
            if (
              isAddressEqual(recipient, this.config.treasuryAddress as Hex) &&
              amount >= requiredFeeUsdc
            ) {
              console.log(
                `[USDC Validator] ✅ Found valid fee transfer (Safe): ${amount.toString()}`,
              );
              return true;
            }
          }
        }
      }
    } catch (e) {
      // Ignore
    }

    return false;
  }

  private async checkSafe4337ExecuteUserOp(
    callData: Hex,
    requiredFeeUsdc: bigint,
  ): Promise<boolean> {
    try {
      const decoded4337 = decodeFunctionData({
        abi: SAFE_4337_EXEC_ABI,
        data: callData,
      });

      if (
        decoded4337.functionName === "executeUserOp" ||
        decoded4337.functionName === "executeUserOpWithErrorString"
      ) {
        const [toAddress, , data] = decoded4337.args;

        if (isAddressEqual(toAddress, this.config.usdcTokenAddress as Hex)) {
          const decodedTransfer = decodeFunctionData({
            abi: ERC20_ABI,
            data: data,
          });

          if (decodedTransfer.functionName === "transfer") {
            const [recipient, amount] = decodedTransfer.args;
            if (
              isAddressEqual(recipient, this.config.treasuryAddress as Hex) &&
              amount >= requiredFeeUsdc
            ) {
              console.log(
                `[USDC Validator] ✅ Found valid fee transfer (Safe 4337): ${amount.toString()}`,
              );
              return true;
            }
          }
        }
      }
    } catch (e) {
      // Ignore
    }

    return false;
  }

  /**
   * CRITICAL SECURITY: Verify sender has sufficient USDC balance
   *
   * @param sender Address of the UserOp sender (Smart Account)
   * @param requiredAmount Required USDC amount for the fee
   * @param client PublicClient for blockchain queries
   * @returns true if sender has sufficient balance, false otherwise
   */
  private async verifySenderBalance(
    sender: string | undefined,
    requiredAmount: bigint,
    client: PublicClient,
  ): Promise<boolean> {
    // Skip balance check in test mode
    if (process.env.CI === "true") {
      console.log(`[USDC Validator] ⚠️  Skipping balance check in CI/test mode`);
      return true;
    }

    if (!sender) {
      console.warn(`[USDC Validator] ❌ Cannot verify balance: sender is undefined`);
      return false;
    }

    try {
      console.log(`[USDC Validator] 🔍 Checking balance for ${sender}...`);

      const balanceResult = await client.readContract({
        address: this.config.usdcTokenAddress as Hex,
        abi: ERC20_ABI,
        functionName: "balanceOf",
        args: [sender as Hex],
      });

      const balance = BigInt(balanceResult || 0);

      console.log(
        `[USDC Validator] Balance: ${balance.toString()}, Required: ${requiredAmount.toString()}`,
      );

      if (balance < requiredAmount) {
        console.warn(
          `[USDC Validator] ❌ INSUFFICIENT BALANCE!\n` +
            `  Sender: ${sender}\n` +
            `  Has: ${balance} USDC\n` +
            `  Needs: ${requiredAmount} USDC\n` +
            `  This prevents "Empty Wallet" attack!`,
        );
        return false;
      }

      console.log(`[USDC Validator] ✅ Balance sufficient`);
      return true;
    } catch (e) {
      console.error(`[USDC Validator] ❌ Balance check failed:`, e);
      // Fail-safe: reject if we can't verify balance
      return false;
    }
  }
}
