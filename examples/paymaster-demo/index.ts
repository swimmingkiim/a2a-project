
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
    // The SDK handles the fee transfer internally for validation.
    // NOTE: The validatin require a transfer to Treasury, but for a general demo,
    // we want to see if the SDK auto-handles the fee or checks balance.
    // The current Paymaster policy STRICTLY requires the userOp to contain the fee transfer.
    // Let's verify if the SDK adds this transfer automatically or if we must add it.
    // *Correction*: The SDK's `PaymasterManager` usually handles the logic or the `SmartAccountManager`
    // appends the fee transfer if configured. 
    // Looking at `PAYMASTER_USAGE.md`, it says "SDK automatically requests gas sponsorship".
    // However, our Paymaster REQUIRES an explicit USDC transfer call in the UserOp.
    // If the SDK doesn't inject it, we must add it manually in the batch.

    // Let's manually add the fee transfer to be safe and compatible with our Paymaster.
    const REQUIRED_FEE_USDC = 600000n; // 0.6 USDC

    console.log(`\nPreparing transaction with ${formatUnits(REQUIRED_FEE_USDC, 6)} USDC fee...`);

    try {
        // Execute Batch: [USDC Fee Transfer] + [Actual Action]
        // Example Action: Send 0 ETH to self (just a ping)
        const txHash = await smartAccountManager.executeBatch([
            {
                to: USDC_ADDRESS,
                value: 0n,
                data: encodeERC20Transfer(TREASURY_ADDRESS, REQUIRED_FEE_USDC)
            },
            {
                to: accountAddress,
                value: 0n,
                data: "0x"
            }
        ]);

        console.log(`\n✅ Transaction Submitted!`);
        console.log(`Tx Hash: https://basescan.org/tx/${txHash}`);

    } catch (error: any) {
        console.error("\n❌ Transaction Failed:", error.message || error);
        if (error.cause) console.error("Cause:", error.cause);
    }
}

// Helper to encode ERC20 transfer
import { encodeFunctionData, parseAbi } from 'viem';

function encodeERC20Transfer(to: string, amount: bigint) {
    return encodeFunctionData({
        abi: parseAbi(['function transfer(address to, uint256 amount)']),
        functionName: 'transfer',
        args: [to as `0x${string}`, amount]
    });
}

main().catch(console.error);
