import { createWalletClient, http, createPublicClient, formatUnits, parseEther, encodeFunctionData, parseAbi } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { base } from 'viem/chains';
import { SmartAccountManager, PaymasterManager } from '@swimmingkiim/pay-sdk';
import { config } from 'dotenv';
// Load environment variables
config();

const PRIVATE_KEY = process.env.PRIVATE_KEY as `0x${string}`;
const RPC_URL = process.env.RPC_URL || 'https://mainnet.base.org';
const PAYMASTER_URL = process.env.PAYMASTER_URL || 'https://paymaster.a10m.work/v1/paymaster';
const PROXY_URL = 'http://localhost:3000/api/sponsor'; // Local Proxy Server

// Constants
const USDC_ADDRESS = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';
const TREASURY_ADDRESS = '0xb6AF245cB3f8F85b1b4d62BD3f1C93f9cC48b88c';

// No custom Paymaster Manager needed!
// We use the real PaymasterManager from the SDK, but point it to our local proxy.

async function main() {
    if (!PRIVATE_KEY) {
        console.error("❌ Please set PRIVATE_KEY in .env");
        process.exit(1);
    }

    console.log("--- Paymaster Proxy Client Demo ---");

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

    // 2. Initialize Paymaster Manager (pointed at our local proxy server)
    // The proxy server will inject the API key, keeping it secure on the backend
    const paymasterManager = new PaymasterManager(
        "http://localhost:3000/rpc",  // Our backend proxy
        undefined  // No API key needed on client - server handles it
    );

    // 3. Initialize Smart Account Manager
    const smartAccountManager = new SmartAccountManager(
        walletClient,
        publicClient,
        "http://localhost:3000/rpc", // Use our local RPC Proxy as Bundler
        paymasterManager
    );

    // 4. Create/Connect Smart Account
    const accountAddress = await smartAccountManager.createSafeAccount(1n); // Different salt for fun
    console.log(`Smart Account: ${accountAddress}`);

    // 5. Define Transaction (Self-transfer 0 ETH)
    // We add the fee transfer manually as per current Paymaster policy
    const REQUIRED_FEE_USDC = 600000n; // 0.6 USDC

    console.log(`\nPreparing transaction with ${formatUnits(REQUIRED_FEE_USDC, 6)} USDC fee...`);

    try {
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
function encodeERC20Transfer(to: string, amount: bigint) {
    return encodeFunctionData({
        abi: parseAbi(['function transfer(address to, uint256 amount)']),
        functionName: 'transfer',
        args: [to as `0x${string}`, amount]
    });
}

main().catch(console.error);
