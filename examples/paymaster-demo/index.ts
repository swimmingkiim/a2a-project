
import { PaymasterManager, SmartAccountManager } from '@swimmingkiim/pay-sdk';
import { createWalletClient, http, createPublicClient, formatUnits, parseEther, parseUnits } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { base } from 'viem/chains';
import { config } from 'dotenv';

// Load environment variables
config();

const PRIVATE_KEY = process.env.PRIVATE_KEY as `0x${string}`;
const RPC_URL = process.env.RPC_URL || 'https://mainnet.base.org';
const PAYMASTER_URL = process.env.PAYMASTER_URL || 'https://paymaster.a10m.work/v1/paymaster';
const PAYMASTER_API_KEY = process.env.A2A_PAYMASTER_API_KEY;

// Constants
const USDC_ADDRESS = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';
const TREASURY_ADDRESS = '0xb6AF245cB3f8F85b1b4d62BD3f1C93f9cC48b88c';

async function main() {
    if (!PRIVATE_KEY || !PAYMASTER_API_KEY) {
        console.error("❌ Please set PRIVATE_KEY and A2A_PAYMASTER_API_KEY in .env");
        process.exit(1);
    }

    console.log("--- A2A Paymaster Demo (SDK Version) ---");

    // 1. Initialize Clients
    const account = privateKeyToAccount(PRIVATE_KEY);
    const walletClient = createWalletClient({
        account,
        chain: base,
        transport: http(RPC_URL)
    });
    const publicClient = createPublicClient({
        chain: base,
        transport: http(RPC_URL)
    });

    console.log(`Signer (EOA): ${account.address}`);

    // 2. Initialize Paymaster Manager
    const paymasterManager = new PaymasterManager(PAYMASTER_URL, PAYMASTER_API_KEY);

    // 3. Initialize Smart Account Manager
    const smartAccountManager = new SmartAccountManager(
        walletClient,
        publicClient,
        PAYMASTER_URL, // <--- SDK now injects x-api-key header
        paymasterManager
    );

    // 4. Create/Connect Smart Account
    const accountAddress = await smartAccountManager.createSafeAccount(0n); // 0n salt for deterministic address
    console.log(`Smart Account: ${accountAddress}`);

    // 5. Define Transaction (Self-transfer 0 ETH as a test)
    // The SDK now provides a built-in helper to append the fee transfer automatically.
    const REQUIRED_FEE_USDC = 600000n; // 0.6 USDC

    console.log(`\nPreparing transaction with ${formatUnits(REQUIRED_FEE_USDC, 6)} USDC fee...`);

    const originalCalls = [
        {
            to: accountAddress as `0x${string}`,
            value: 0n,
            data: "0x" as `0x${string}`
        }
    ];

    const callsWithFee = PaymasterManager.appendFeeToCalls(originalCalls, {
        treasury: TREASURY_ADDRESS,
        amount: REQUIRED_FEE_USDC,
        tokenType: 'USDC'
    });

    try {
        // Execute Batch: [USDC Fee Transfer] + [Actual Action]
        const txHash = await smartAccountManager.executeBatch(callsWithFee);

        console.log(`\n✅ Transaction Submitted!`);
        console.log(`Tx Hash: https://basescan.org/tx/${txHash}`);

    } catch (error: any) {
        console.error("\n❌ Transaction Failed:", error.message || error);
        if (error.cause) console.error("Cause:", error.cause);
    }
}

main().catch(console.error);
