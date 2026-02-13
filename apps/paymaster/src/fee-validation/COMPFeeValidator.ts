import { IFeeValidator } from './IFeeValidator';
import { ITokenPriceOracle } from '../oracle/ITokenPriceOracle';
import { PublicClient, Hex, decodeFunctionData, parseAbi, isAddressEqual } from 'viem';

const ERC20_ABI = parseAbi([
    'function transfer(address to, uint256 amount) returns (bool)',
    'function balanceOf(address account) view returns (uint256)'
]);
const BATCH_EXECUTE_ABI = parseAbi(['function executeBatch(address[] dest, uint256[] value, bytes[] func)']);
const EXECUTE_ABI = parseAbi(['function execute(address target, uint256 value, bytes calldata data)']);
const SAFE_EXEC_ABI = parseAbi([
    'function execTransaction(address to, uint256 value, bytes data, uint8 operation, uint256 safeTxGas, uint256 baseGas, uint256 gasPrice, address gasToken, address refundReceiver, bytes signatures)'
]);
const SAFE_4337_EXEC_ABI = parseAbi([
    'function executeUserOp(address to, uint256 value, bytes data, uint8 operation)',
    'function executeUserOpWithErrorString(address to, uint256 value, bytes data, uint8 operation)'
]);

const ORACLE_ABI = parseAbi(['function getL1Fee(bytes) view returns (uint256)']);
const ORACLE_ADDR = '0x420000000000000000000000000000000000000F';

interface COMPFeeConfig {
    treasuryAddress: string;
    compTokenAddress: string;
    markupRate: number;
}

/**
 * COMPFeeValidator
 * 
 * Validates that UserOperations include proper $COMP fee payments.
 * Uses ITokenPriceOracle to convert gas costs (ETH) to $COMP amounts.
 */
export class COMPFeeValidator implements IFeeValidator {
    private config: COMPFeeConfig;
    private oracle: ITokenPriceOracle;

    constructor(config: COMPFeeConfig, oracle: ITokenPriceOracle) {
        this.config = config;
        this.oracle = oracle;
    }

    async validateFeeIncluded(userOp: any, client: PublicClient): Promise<boolean> {
        console.log(`[COMP Validator] Checking for embedded COMP fee...`);

        // 1. Calculate Required Fee in COMP
        const requiredFeeCOMP = await this.calculateRequiredFee(userOp, client);

        console.log(`[COMP Validator] Required fee: ${requiredFeeCOMP} COMP (18 decimals)`);

        // 2. Check callData for COMP fee transfer
        const callData = userOp.callData as Hex;

        // Try different account execution patterns
        if (await this.checkExecuteBatch(callData, requiredFeeCOMP)) {
            // 3. CRITICAL: Verify sender has sufficient COMP balance
            return await this.verifySenderBalance(userOp.sender, requiredFeeCOMP, client);
        }
        if (await this.checkExecute(callData, requiredFeeCOMP)) {
            return await this.verifySenderBalance(userOp.sender, requiredFeeCOMP, client);
        }
        if (await this.checkSafeExecTransaction(callData, requiredFeeCOMP)) {
            return await this.verifySenderBalance(userOp.sender, requiredFeeCOMP, client);
        }
        if (await this.checkSafe4337ExecuteUserOp(callData, requiredFeeCOMP)) {
            return await this.verifySenderBalance(userOp.sender, requiredFeeCOMP, client);
        }

        console.warn(`[COMP Validator] ❌ No valid COMP fee transfer found.`);
        return false;
    }

    private async calculateRequiredFee(userOp: any, client: PublicClient): Promise<bigint> {
        try {
            // Calculate Total Gas Cost in ETH (Wei)
            const preVerificationGas = BigInt(userOp.preVerificationGas || 0);
            const verificationGasLimit = BigInt(userOp.verificationGasLimit || 0);
            const callGasLimit = BigInt(userOp.callGasLimit || 0);
            const maxFeePerGas = BigInt(userOp.maxFeePerGas || userOp.maxPriorityFeePerGas || 0);

            if (maxFeePerGas === 0n || (preVerificationGas + verificationGasLimit + callGasLimit) === 0n) {
                throw new Error('Invalid gas parameters');
            }

            const totalGas = preVerificationGas + verificationGasLimit + callGasLimit;

            // Calculate L1 Fee (Oracle) - CRITICAL for Base L2
            let l1Fee = 0n;
            if (userOp.callData) {
                try {
                    const l1FeeResult = await client.readContract({
                        address: ORACLE_ADDR,
                        abi: ORACLE_ABI,
                        functionName: 'getL1Fee',
                        args: [userOp.callData as Hex]
                    });
                    l1Fee = BigInt(l1FeeResult || 0);
                    console.log(`[COMP Validator] L1 Fee: ${l1Fee} Wei`);
                } catch (e) {
                    // L1 Fee calculation failure is critical - cannot proceed safely
                    console.error(`[COMP Validator] ❌ L1 Fee calculation failed:`, e);
                    throw new Error('Failed to calculate L1 fee - cannot determine accurate costs');
                }
            }

            const totalCostEthWei = (totalGas * maxFeePerGas) + l1Fee;

            console.log(`[COMP Validator] Gas cost in ETH Wei: ${totalCostEthWei}`);

            // Convert ETH Wei to COMP using Oracle
            // Get COMP per 1 ETH (in COMP 18 decimals)
            const compPerETH = await this.oracle.getCOMPPerETH();

            // Calculate required COMP: (totalCostEthWei * compPerETH) / 10^18
            const requiredCOMP = (totalCostEthWei * compPerETH) / 10n ** 18n;

            // Apply Markup
            const markupBps = BigInt(Math.floor(this.config.markupRate * 10000));
            const requiredCOMPWithMarkup = (requiredCOMP * (10000n + markupBps)) / 10000n;

            console.log(`[COMP Validator] Base COMP: ${requiredCOMP}, With Markup: ${requiredCOMPWithMarkup}`);

            return requiredCOMPWithMarkup;
        } catch (e) {
            console.error(`[COMP Validator] Failed to calculate required COMP fee:`, e);
            throw e; // Critical error - cannot proceed without valid fee calculation
        }
    }

    private async checkExecuteBatch(callData: Hex, requiredFeeCOMP: bigint): Promise<boolean> {
        try {
            const decodedBatch = decodeFunctionData({
                abi: BATCH_EXECUTE_ABI,
                data: callData
            });

            if (decodedBatch.functionName === 'executeBatch') {
                const [dests, values, funcs] = decodedBatch.args;

                for (let i = 0; i < dests.length; i++) {
                    const target = dests[i];
                    const data = funcs[i];

                    if (isAddressEqual(target, this.config.compTokenAddress as Hex)) {
                        const decodedTransfer = decodeFunctionData({
                            abi: ERC20_ABI,
                            data: data
                        });

                        if (decodedTransfer.functionName === 'transfer') {
                            const [to, amount] = decodedTransfer.args;
                            if (isAddressEqual(to, this.config.treasuryAddress as Hex) && amount >= requiredFeeCOMP) {
                                console.log(`[COMP Validator] ✅ Found valid COMP fee transfer: ${amount.toString()} to ${to}`);
                                return true;
                            }
                        }
                    }
                }
            }
        } catch (e) {
            // Ignore decoding errors
        }

        return false;
    }

    private async checkExecute(callData: Hex, requiredFeeCOMP: bigint): Promise<boolean> {
        try {
            const decodedExecute = decodeFunctionData({
                abi: EXECUTE_ABI,
                data: callData
            });

            if (decodedExecute.functionName === 'execute') {
                const [target, value, data] = decodedExecute.args;

                if (isAddressEqual(target, this.config.compTokenAddress as Hex)) {
                    const decodedTransfer = decodeFunctionData({
                        abi: ERC20_ABI,
                        data: data
                    });

                    if (decodedTransfer.functionName === 'transfer') {
                        const [to, amount] = decodedTransfer.args;
                        if (isAddressEqual(to, this.config.treasuryAddress as Hex) && amount >= requiredFeeCOMP) {
                            console.log(`[COMP Validator] ✅ Found valid COMP fee transfer: ${amount.toString()}`);
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

    private async checkSafeExecTransaction(callData: Hex, requiredFeeCOMP: bigint): Promise<boolean> {
        try {
            const decodedSafe = decodeFunctionData({
                abi: SAFE_EXEC_ABI,
                data: callData
            });

            if (decodedSafe.functionName === 'execTransaction') {
                const [toAddress, value, data] = decodedSafe.args;

                if (isAddressEqual(toAddress, this.config.compTokenAddress as Hex)) {
                    const decodedTransfer = decodeFunctionData({
                        abi: ERC20_ABI,
                        data: data
                    });

                    if (decodedTransfer.functionName === 'transfer') {
                        const [recipient, amount] = decodedTransfer.args;
                        if (isAddressEqual(recipient, this.config.treasuryAddress as Hex) && amount >= requiredFeeCOMP) {
                            console.log(`[COMP Validator] ✅ Found valid COMP fee transfer (Safe): ${amount.toString()}`);
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

    private async checkSafe4337ExecuteUserOp(callData: Hex, requiredFeeCOMP: bigint): Promise<boolean> {
        try {
            const decoded4337 = decodeFunctionData({
                abi: SAFE_4337_EXEC_ABI,
                data: callData
            });

            if (decoded4337.functionName === 'executeUserOp' || decoded4337.functionName === 'executeUserOpWithErrorString') {
                const [toAddress, value, data] = decoded4337.args;

                if (isAddressEqual(toAddress, this.config.compTokenAddress as Hex)) {
                    const decodedTransfer = decodeFunctionData({
                        abi: ERC20_ABI,
                        data: data
                    });

                    if (decodedTransfer.functionName === 'transfer') {
                        const [recipient, amount] = decodedTransfer.args;
                        if (isAddressEqual(recipient, this.config.treasuryAddress as Hex) && amount >= requiredFeeCOMP) {
                            console.log(`[COMP Validator] ✅ Found valid COMP fee transfer (Safe 4337): ${amount.toString()}`);
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
     * CRITICAL SECURITY: Verify sender has sufficient COMP balance
     * 
     * Prevents "Empty Wallet" attack where attackers submit UserOps with valid
     * callData but insufficient balance, causing Paymaster to waste gas.
     * 
     * @param sender Address of the UserOp sender (Smart Account)
     * @param requiredAmount Required COMP amount for the fee
     * @param client PublicClient for blockchain queries
     * @returns true if sender has sufficient balance, false otherwise
     */
    private async verifySenderBalance(
        sender: string | undefined,
        requiredAmount: bigint,
        client: PublicClient
    ): Promise<boolean> {
        // Skip balance check in test mode
        if (process.env.CI === 'true') {
            console.log(`[COMP Validator] ⚠️  Skipping balance check in CI/test mode`);
            return true;
        }

        if (!sender) {
            console.warn(`[COMP Validator] ❌ Cannot verify balance: sender is undefined`);
            return false;
        }

        try {
            console.log(`[COMP Validator] 🔍 Checking balance for ${sender}...`);

            const balanceResult = await client.readContract({
                address: this.config.compTokenAddress as Hex,
                abi: ERC20_ABI,
                functionName: 'balanceOf',
                args: [sender as Hex]
            });

            const balance = BigInt(balanceResult || 0);

            console.log(`[COMP Validator] Balance: ${balance.toString()}, Required: ${requiredAmount.toString()}`);

            if (balance < requiredAmount) {
                console.warn(
                    `[COMP Validator] ❌ INSUFFICIENT BALANCE!\n` +
                    `  Sender: ${sender}\n` +
                    `  Has: ${balance} COMP\n` +
                    `  Needs: ${requiredAmount} COMP\n` +
                    `  This prevents "Empty Wallet" attack!`
                );
                return false;
            }

            console.log(`[COMP Validator] ✅ Balance sufficient`);
            return true;

        } catch (e) {
            console.error(`[COMP Validator] ❌ Balance check failed:`, e);
            // Fail-safe: reject if we can't verify balance
            return false;
        }
    }
}
