import { PaymasterManager } from '../packages/pay-sdk/src';
import { createPublicClient, http, encodeFunctionData, parseAbi } from 'viem';
import { base } from 'viem/chains';
import { createSmartAccountClient } from 'permissionless';
import { privateKeyToAccount } from 'viem/accounts';
import { toSafeSmartAccount } from 'permissionless/accounts';

// --- CONFIGURATION ---
const RPC_URL = process.env.RPC_URL || 'https://mainnet.base.org';
const PAYMASTER_URL = process.env.PAYMASTER_URL || 'https://paymaster.a10m.work/v1/paymaster';
const PRIVATE_KEY = process.env.PRIVATE_KEY as `0x${string}` || '0xYOUR_PRIVATE_KEY';
const API_KEY = process.env.API_KEY || 'YOUR_API_KEY';
const TREASURY_ADDRESS = '0xYourTreasuryAddress'; // Set your treasury here

const ERC20_ABI = parseAbi(['function transfer(address to, uint256 amount) returns (bool)']);
const USDC_ADDR = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';

async function main() {
    console.log("🚀 Starting Agent Scenario...");

    // 1. Setup Clients
    const publicClient = createPublicClient({ chain: base, transport: http(RPC_URL) });
    const signer = privateKeyToAccount(PRIVATE_KEY);

    // 2. Setup Smart Account (Safe)
    const safeAccount = await toSafeSmartAccount({
        client: publicClient,
        owners: [signer],
        version: '1.4.1',
        entryPoint: { address: "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789", version: "0.6" },
    });

    const smartAccountClient = createSmartAccountClient({
        account: safeAccount,
        chain: base,
        bundlerTransport: http(RPC_URL), // Use Paymaster as Bundler Proxy if configured
        middleware: {
            sponsorUserOperation: async (args) => {
                // Use our Custom Paymaster Manager
                const pm = new PaymasterManager(PAYMASTER_URL, API_KEY);
                return pm.getStubPaymasterData(args.userOperation);
            }
        }
    });

    console.log(`🤖 Agent Address: ${safeAccount.address}`);

    // 3. Define the Agent's original intent (e.g., Swap, Transfer)
    const originalCalls = [
        {
            to: USDC_ADDR,
            value: 0n,
            data: encodeFunctionData({
                abi: ERC20_ABI,
                functionName: 'transfer',
                args: ['0xRecipient', 1000000n] // Transfer 1 USDC
            })
        }
    ];

    // 4. [CRITICAL] Append the Fee Transaction
    // This adds the "Transaction-Embedded Fee" transfer to the batch.
    const callsWithFee = PaymasterManager.appendFeeToCalls(originalCalls, {
        treasury: TREASURY_ADDRESS,
        amount: 100000n, // 0.1 USDC fee
        token: USDC_ADDR
    });

    console.log(`📦 Prepared ${callsWithFee.length} calls (Original + Fee)`);

    // 5. Build and Send UserOperation
    // The middleware above will call our Paymaster, which checks for the fee.
    try {
        const txHash = await smartAccountClient.sendTransaction({
            calls: callsWithFee.map(call => ({
                to: call.to as `0x${string}`,
                value: call.value,
                data: call.data as `0x${string}`
            }))
        });

        console.log(`✅ Transaction Sent! Hash: ${txHash}`);
        console.log(`💰 Fee of 0.1 USDC sent to Treasury.`);
    } catch (error: any) {
        console.error("❌ Transaction Failed:", error);

        if (error.message.includes('Missing Treasury Fee')) {
            console.error("👉 CAUSE: The Paymaster rejected the request because the fee transfer was missing or insufficient.");
        }
    }
}

// Run if called directly
if (require.main === module) {
    main().catch(console.error);
}
