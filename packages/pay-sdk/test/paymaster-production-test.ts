/**
 * Production Paymaster Test
 * 
 * Tests the deployed Paymaster service on Base Mainnet with a real transaction.
 * 
 * Prerequisites:
 * 1. EOA wallet with ETH for initial setup
 * 2. EOA wallet with USDC (minimum 0.5 USDC)
 * 3. PAYMASTER_API_KEY from paymaster.a10m.work
 * 
 * Usage:
 * PRIVATE_KEY=0x... A2A_PAYMASTER_API_KEY=... npx tsx test/paymaster-production-test.ts
 */

import { PaymasterManager, SmartAccountManager } from '../src';
import { createWalletClient, createPublicClient, http, parseUnits, formatUnits } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { base } from 'viem/chains';

// Configuration
const PAYMASTER_URL = 'https://paymaster.a10m.work/v1/paymaster';
const RPC_URL = 'https://mainnet.base.org';
const USDC_ADDRESS = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';
const COMP_ADDRESS = '0x1F478c3F6a09c3820baBd3f6DCD8bEA4eE5dc806';

// ERC20 ABI (minimal)
const ERC20_ABI = [
    {
        inputs: [{ name: 'account', type: 'address' }],
        name: 'balanceOf',
        outputs: [{ name: '', type: 'uint256' }],
        stateMutability: 'view',
        type: 'function'
    },
    {
        inputs: [
            { name: 'to', type: 'address' },
            { name: 'amount', type: 'uint256' }
        ],
        name: 'transfer',
        outputs: [{ name: '', type: 'bool' }],
        stateMutability: 'nonpayable',
        type: 'function'
    }
] as const;

async function main() {
    console.log('🚀 Production Paymaster Test\n');
    console.log('='.repeat(60));

    // Validate environment
    if (!process.env.PRIVATE_KEY) {
        throw new Error('PRIVATE_KEY not set in .env');
    }
    if (!process.env.A2A_PAYMASTER_API_KEY) {
        console.warn('⚠️  A2A_PAYMASTER_API_KEY not set - proceeding without API key');
    }

    // Setup
    const account = privateKeyToAccount(process.env.PRIVATE_KEY as `0x${string}`);

    const walletClient = createWalletClient({
        account,
        chain: base,
        transport: http(RPC_URL)
    });

    const publicClient = createPublicClient({
        chain: base,
        transport: http(RPC_URL)
    });

    console.log('\n📍 Step 1: Account Setup');
    console.log(`   EOA Address: ${account.address}`);

    // Check EOA balances
    const eoaEthBalance = await publicClient.getBalance({ address: account.address });
    const eoaUsdcBalance = await publicClient.readContract({
        address: USDC_ADDRESS,
        abi: ERC20_ABI,
        functionName: 'balanceOf',
        args: [account.address]
    });

    console.log(`   EOA ETH: ${formatUnits(eoaEthBalance, 18)} ETH`);
    console.log(`   EOA USDC: ${formatUnits(eoaUsdcBalance, 6)} USDC`);

    if (eoaEthBalance < parseUnits('0.001', 18)) {
        throw new Error('❌ Insufficient ETH in EOA (need at least 0.001 ETH for setup)');
    }
    if (eoaUsdcBalance < parseUnits('0.5', 6)) {
        throw new Error('❌ Insufficient USDC in EOA (need at least 0.5 USDC for test)');
    }

    // Initialize Paymaster
    console.log('\n📍 Step 2: Initialize Paymaster');
    const paymasterManager = new PaymasterManager(
        PAYMASTER_URL,
        process.env.A2A_PAYMASTER_API_KEY
    );
    console.log(`   Paymaster URL: ${PAYMASTER_URL}`);
    console.log(`   API Key: ${process.env.A2A_PAYMASTER_API_KEY ? '✅ Set' : '❌ Not set'}`);

    // Create Smart Account
    console.log('\n📍 Step 3: Create Smart Account');
    const smartAccount = new SmartAccountManager(
        walletClient,
        publicClient,
        RPC_URL,
        paymasterManager
    );

    const saAddress = await smartAccount.createSafeAccount();
    console.log(`   Smart Account: ${saAddress}`);

    // Check Smart Account balances
    const saEthBalance = await publicClient.getBalance({ address: saAddress });
    const saUsdcBalance = await publicClient.readContract({
        address: USDC_ADDRESS,
        abi: ERC20_ABI,
        functionName: 'balanceOf',
        args: [saAddress]
    });

    console.log(`   SA ETH: ${formatUnits(saEthBalance, 18)} ETH`);
    console.log(`   SA USDC: ${formatUnits(saUsdcBalance, 6)} USDC`);

    // Transfer USDC to Smart Account if needed
    if (saUsdcBalance < parseUnits('0.2', 6)) {
        console.log('\n📍 Step 4: Fund Smart Account with USDC');
        console.log('   Transferring 0.3 USDC from EOA to Smart Account...');

        const transferAmount = parseUnits('0.3', 6);
        const hash = await walletClient.writeContract({
            address: USDC_ADDRESS,
            abi: ERC20_ABI,
            functionName: 'transfer',
            args: [saAddress, transferAmount]
        });

        console.log(`   TX Hash: ${hash}`);
        console.log('   Waiting for confirmation...');

        const receipt = await publicClient.waitForTransactionReceipt({ hash });
        console.log(`   ✅ Confirmed in block ${receipt.blockNumber}`);

        // Re-check balance
        const newSaUsdcBalance = await publicClient.readContract({
            address: USDC_ADDRESS,
            abi: ERC20_ABI,
            functionName: 'balanceOf',
            args: [saAddress]
        });
        console.log(`   New SA USDC: ${formatUnits(newSaUsdcBalance, 6)} USDC`);
    } else {
        console.log('\n📍 Step 4: Smart Account Funding');
        console.log('   ✅ Smart Account has sufficient USDC');
    }

    // Execute test transaction via Paymaster
    console.log('\n📍 Step 5: Execute Transaction via Paymaster');
    console.log('   Sending 0.01 USDC to test recipient...');

    const testRecipient = '0x0000000000000000000000000000000000000001'; // Burn address
    const testAmount = parseUnits('0.01', 6);

    try {
        const txHash = await smartAccount.executeBatch([
            {
                to: USDC_ADDRESS,
                value: 0n,
                data: walletClient.encodeFunctionData({
                    abi: ERC20_ABI,
                    functionName: 'transfer',
                    args: [testRecipient as `0x${string}`, testAmount]
                }) as `0x${string}`
            }
        ]);

        console.log(`   ✅ Transaction successful!`);
        console.log(`   TX Hash: ${txHash}`);

        // Wait for confirmation
        console.log('   Waiting for confirmation...');
        const receipt = await publicClient.waitForTransactionReceipt({
            hash: txHash as `0x${string}`
        });
        console.log(`   ✅ Confirmed in block ${receipt.blockNumber}`);

        // Verify balances after transaction
        const finalSaUsdcBalance = await publicClient.readContract({
            address: USDC_ADDRESS,
            abi: ERC20_ABI,
            functionName: 'balanceOf',
            args: [saAddress]
        });

        console.log('\n📊 Final Balances:');
        console.log(`   SA USDC: ${formatUnits(finalSaUsdcBalance, 6)} USDC`);
        console.log(`   Fee paid: ~${formatUnits(saUsdcBalance - finalSaUsdcBalance - testAmount, 6)} USDC`);

    } catch (error) {
        console.error('\n❌ Transaction failed:', error);
        throw error;
    }

    console.log('\n' + '='.repeat(60));
    console.log('✅ Production Paymaster Test Complete!');
    console.log('\nPaymaster is working correctly on Base Mainnet 🎉');
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error('\n❌ Test failed:', error);
        process.exit(1);
    });
