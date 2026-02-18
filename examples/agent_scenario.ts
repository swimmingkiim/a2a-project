import { PaymasterManager, SmartAccountManager } from '@swimmingkiim/pay-sdk';
import { createPublicClient, createWalletClient, http, encodeFunctionData, parseAbi } from 'viem';
import { base } from 'viem/chains';
import { privateKeyToAccount } from 'viem/accounts';

// --- CONFIGURATION ---
const RPC_URL = process.env.RPC_URL || 'https://mainnet.base.org';
const PAYMASTER_URL = process.env.PAYMASTER_URL || 'https://paymaster.a10m.work/v1/paymaster';
const PRIVATE_KEY = process.env.PRIVATE_KEY as `0x${string}` || '0xYOUR_PRIVATE_KEY';
const API_KEY = process.env.API_KEY || 'YOUR_API_KEY';
const TREASURY_ADDRESS = '0xYourTreasuryAddress'; // Set your treasury here

const USDC_ADDR = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';

async function main() {
    console.log("🚀 Starting Agent Scenario...");

    // 1. Setup Clients
    const signer = privateKeyToAccount(PRIVATE_KEY);
    const walletClient = createWalletClient({
        account: signer,
        chain: base,
        transport: http(RPC_URL)
    });
    const publicClient = createPublicClient({ chain: base, transport: http(RPC_URL) });

    // 2. Setup Paymaster Manager
    const paymasterManager = new PaymasterManager(PAYMASTER_URL, API_KEY);

    // 3. Setup Smart Account Manager (uses Safe ERC-7579)
    const smartAccountManager = new SmartAccountManager(
        walletClient,
        publicClient,
        PAYMASTER_URL,
        paymasterManager
    );

    // 4. Create/Connect Smart Account
    const accountAddress = await smartAccountManager.createSafeAccount();
    console.log(`🤖 Agent Address: ${accountAddress}`);

    // 5. Define the Agent's original intent (e.g., Swap, Transfer)
    const originalCalls = [
        {
            to: USDC_ADDR as `0x${string}`,
            value: 0n,
            data: encodeFunctionData({
                abi: parseAbi(['function transfer(address to, uint256 amount) returns (bool)']),
                functionName: 'transfer',
                args: ['0xRecipientAddress' as `0x${string}`, 1000000n] // Transfer 1 USDC
            })
        }
    ];

    // 6. [CRITICAL] Append the Fee Transaction using FeeConfig
    // This adds the "Transaction-Embedded Fee" transfer to the batch.
    const callsWithFee = PaymasterManager.appendFeeToCalls(originalCalls, {
        treasury: TREASURY_ADDRESS,
        amount: 100000n,   // 0.1 USDC fee
        tokenType: 'USDC'  // Use 'DAIM' for DAIM token fees
    });

    console.log(`📦 Prepared ${callsWithFee.length} calls (Original + Fee)`);

    // 7. Execute via SmartAccountManager
    // The SDK handles: balance check → auto-deposit → paymaster sponsorship → submit
    try {
        const txHash = await smartAccountManager.executeBatch(
            callsWithFee.map(call => ({
                to: call.to as `0x${string}`,
                value: call.value,
                data: call.data as `0x${string}`
            }))
        );

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
