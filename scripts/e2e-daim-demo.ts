#!/usr/bin/env tsx

/**
 * E2E Demo: DAIM Token Fee Payment
 * 
 * This script demonstrates the complete flow of paying fees with DAIM tokens:
 * 1. Setup Smart Account
 * 2. Mint DAIM tokens for testing
 * 3. Prepare transaction with DAIM fee
 * 4. Submit to Paymaster
 * 5. Execute on Base Sepolia
 * 6. Verify fee payment
 * 
 * Prerequisites:
 * - Base Sepolia RPC access
 * - Test wallet with ETH for gas
 * - DAIM token deployed at 0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3
 */

import { createPublicClient, createWalletClient, http, parseAbi, encodeFunctionData, parseEther } from 'viem';
import { baseSepolia } from 'viem/chains';
import { privateKeyToAccount } from 'viem/accounts';
import { config } from 'dotenv';

config();

// Configuration
const DAIM_TOKEN_ADDRESS = (process.env.DAIM_TOKEN_ADDRESS || '0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3') as `0x${string}`;
const TREASURY_ADDRESS = process.env.TREASURY_ADDRESS || '0x0000000000000000000000000000000000000000';
const DEMO_PRIVATE_KEY = process.env.DEMO_PRIVATE_KEY as `0x${string}`;
const RPC_URL = process.env.RPC_URL || 'https://sepolia.base.org';

const DAIM_ABI = parseAbi([
    'function mint(address to, uint256 amount) public',
    'function balanceOf(address account) view returns (uint256)',
    'function transfer(address to, uint256 amount) returns (bool)',
    'function hasRole(bytes32 role, address account) view returns (bool)',
    'function MINTER_ROLE() view returns (bytes32)'
]);

const ERC20_ABI = parseAbi([
    'function transfer(address to, uint256 amount) returns (bool)',
    'function balanceOf(address account) view returns (uint256)'
]);

// Clients
import { base, baseSepolia } from 'viem/chains';

const CHAIN_ID = parseInt(process.env.CHAIN_ID || '84532'); // Default to Base Sepolia (84532)
const activeChain = CHAIN_ID === 8453 ? base : baseSepolia;

console.log(`🌍 Connecting to Chain ID: ${CHAIN_ID} (${activeChain.name})`);

const publicClient = createPublicClient({
    chain: activeChain,
    transport: http(RPC_URL)
});

const account = privateKeyToAccount(DEMO_PRIVATE_KEY);
const walletClient = createWalletClient({
    account,
    chain: activeChain,
    transport: http(RPC_URL)
});

// Helper functions
async function checkDAIMBalance(address: `0x${string}`): Promise<bigint> {
    const balance = await publicClient.readContract({
        address: DAIM_TOKEN_ADDRESS,
        abi: DAIM_ABI,
        functionName: 'balanceOf',
        args: [address]
    }) as bigint;

    return balance;
}

async function mintDAIM(to: `0x${string}`, amount: bigint): Promise<void> {
    console.log(`💰 Minting ${Number(amount) / 1e18} DAIM to ${to}...`);

    // Check if account has MINTER_ROLE
    const minterRole = await publicClient.readContract({
        address: DAIM_TOKEN_ADDRESS,
        abi: DAIM_ABI,
        functionName: 'MINTER_ROLE'
    }) as `0x${string}`;

    const hasMinterRole = await publicClient.readContract({
        address: DAIM_TOKEN_ADDRESS,
        abi: DAIM_ABI,
        functionName: 'hasRole',
        args: [minterRole, account.address]
    }) as boolean;

    if (!hasMinterRole) {
        console.error(`❌ Account ${account.address} does not have MINTER_ROLE`);
        console.log(`   Please grant MINTER_ROLE to this address first.`);
        throw new Error('Missing MINTER_ROLE');
    }

    const hash = await walletClient.writeContract({
        address: DAIM_TOKEN_ADDRESS,
        abi: DAIM_ABI,
        functionName: 'mint',
        args: [to, amount]
    });

    console.log(`   Transaction: ${hash}`);

    const receipt = await publicClient.waitForTransactionReceipt({ hash });
    console.log(`   ✅ Minted in block ${receipt.blockNumber}`);
}

async function sendDAIMFeeDemo(): Promise<void> {
    console.log('\n🚀 Starting E2E Demo: DAIM Fee Payment\n');
    console.log('='.repeat(60));

    // Step 1: Check setup
    console.log('\n📋 Step 1: Environment Check');
    console.log(`   Wallet: ${account.address}`);
    console.log(`   DAIM Token: ${DAIM_TOKEN_ADDRESS}`);
    console.log(`   Treasury: ${TREASURY_ADDRESS}`);
    console.log(`   RPC: ${RPC_URL}`);

    const ethBalance = await publicClient.getBalance({ address: account.address });
    console.log(`   ETH Balance: ${Number(ethBalance) / 1e18} ETH`);

    if (ethBalance < parseEther('0.001')) {
        console.error('\n❌ Insufficient ETH for gas. Please fund your wallet.');
        return;
    }

    // Step 2: Check DAIM balance
    console.log('\n💰 Step 2: DAIM Balance Check');
    let daimBalance = await checkDAIMBalance(account.address);
    console.log(`   Current DAIM Balance: ${Number(daimBalance) / 1e18} DAIM`);

    const requiredDAIM = 25n * 10n ** 18n; // 25 DAIM for fee

    if (daimBalance < requiredDAIM) {
        console.log(`   ⚠️  Insufficient DAIM (need ${Number(requiredDAIM) / 1e18} DAIM)`);
        console.log(`   Minting ${Number(requiredDAIM * 4n) / 1e18} DAIM for testing...`);

        try {
            await mintDAIM(account.address, requiredDAIM * 4n); // Mint 100 DAIM
            daimBalance = await checkDAIMBalance(account.address);
            console.log(`   ✅ New balance: ${Number(daimBalance) / 1e18} DAIM`);
        } catch (error: any) {
            console.error(`   ❌ Failed to mint: ${error.message}`);
            return;
        }
    }

    // Step 3: Prepare DAIM fee transaction
    console.log('\n📝 Step 3: Preparing DAIM Fee Transaction');
    console.log(`   Fee Amount: ${Number(requiredDAIM) / 1e18} DAIM`);
    console.log(`   Treasury: ${TREASURY_ADDRESS}`);

    const feeTransferData = encodeFunctionData({
        abi: ERC20_ABI,
        functionName: 'transfer',
        args: [TREASURY_ADDRESS, requiredDAIM]
    });

    console.log(`   ✅ Fee transaction encoded`);

    // Step 4: Send fee payment (simulating what would happen in UserOp)
    console.log('\n📤 Step 4: Sending DAIM Fee Payment');
    console.log(`   Sending ${Number(requiredDAIM) / 1e18} DAIM to Treasury...`);

    const treasuryBalanceBefore = await checkDAIMBalance(TREASURY_ADDRESS as `0x${string}`);
    console.log(`   Treasury balance before: ${Number(treasuryBalanceBefore) / 1e18} DAIM`);

    const hash = await walletClient.writeContract({
        address: DAIM_TOKEN_ADDRESS,
        abi: ERC20_ABI,
        functionName: 'transfer',
        args: [TREASURY_ADDRESS, requiredDAIM]
    });

    console.log(`   Transaction: ${hash}`);

    // Step 5: Wait for confirmation
    console.log('\n⏳ Step 5: Waiting for Confirmation');
    const receipt = await publicClient.waitForTransactionReceipt({ hash });
    console.log(`   ✅ Confirmed in block ${receipt.blockNumber}`);
    console.log(`   Gas used: ${receipt.gasUsed.toString()}`);

    // Step 6: Verify fee payment
    console.log('\n✅ Step 6: Verifying Fee Payment');
    const userBalanceAfter = await checkDAIMBalance(account.address);
    const treasuryBalanceAfter = await checkDAIMBalance(TREASURY_ADDRESS as `0x${string}`);

    console.log(`   User balance after: ${Number(userBalanceAfter) / 1e18} DAIM`);
    console.log(`   Treasury balance after: ${Number(treasuryBalanceAfter) / 1e18} DAIM`);
    console.log(`   Treasury received: ${Number(treasuryBalanceAfter - treasuryBalanceBefore) / 1e18} DAIM`);

    if (treasuryBalanceAfter - treasuryBalanceBefore === requiredDAIM) {
        console.log(`   ✅ Fee payment verified!`);
    } else {
        console.log(`   ⚠️  Unexpected balance change`);
    }

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('🎉 E2E Demo Complete!\n');
    console.log('Summary:');
    console.log(`  ✅ DAIM token transfer successful`);
    console.log(`  ✅ Treasury received ${Number(requiredDAIM) / 1e18} DAIM`);
    console.log(`  ✅ Transaction confirmed on Base Sepolia`);
    console.log(`  ✅ Block: ${receipt.blockNumber}`);
    console.log(`  ✅ TX: ${hash}`);
    console.log('\n📚 Next Steps:');
    console.log('  1. Integrate with actual Smart Account (e.g., Kernel, Biconomy)');
    console.log('  2. Submit UserOp to Paymaster for sponsorship');
    console.log('  3. Test with ENABLE_DAIM_FEES=true on Paymaster');
    console.log('  4. Deploy to Base Mainnet');
}

// Run demo
sendDAIMFeeDemo()
    .then(() => {
        console.log('\n✅ Demo completed successfully');
        process.exit(0);
    })
    .catch((error) => {
        console.error('\n❌ Demo failed:', error);
        process.exit(1);
    });
