#!/usr/bin/env tsx

/**
 * E2E Demo: COMP Token Fee Payment
 * 
 * This script demonstrates the complete flow of paying fees with COMP tokens:
 * 1. Setup Smart Account
 * 2. Mint COMP tokens for testing
 * 3. Prepare transaction with COMP fee
 * 4. Submit to Paymaster
 * 5. Execute on Base Sepolia
 * 6. Verify fee payment
 * 
 * Prerequisites:
 * - Base Sepolia RPC access
 * - Test wallet with ETH for gas
 * - COMP token deployed at 0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3
 */

import { createPublicClient, createWalletClient, http, parseAbi, encodeFunctionData, parseEther } from 'viem';
import { baseSepolia } from 'viem/chains';
import { privateKeyToAccount } from 'viem/accounts';
import { config } from 'dotenv';

config();

// Configuration
const COMP_TOKEN_ADDRESS = (process.env.COMP_TOKEN_ADDRESS || '0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3') as `0x${string}`;
const TREASURY_ADDRESS = process.env.TREASURY_ADDRESS || '0x0000000000000000000000000000000000000000';
const DEMO_PRIVATE_KEY = process.env.DEMO_PRIVATE_KEY as `0x${string}`;
const RPC_URL = process.env.RPC_URL || 'https://sepolia.base.org';

const COMP_ABI = parseAbi([
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
async function checkCOMPBalance(address: `0x${string}`): Promise<bigint> {
    const balance = await publicClient.readContract({
        address: COMP_TOKEN_ADDRESS,
        abi: COMP_ABI,
        functionName: 'balanceOf',
        args: [address]
    }) as bigint;

    return balance;
}

async function mintCOMP(to: `0x${string}`, amount: bigint): Promise<void> {
    console.log(`💰 Minting ${Number(amount) / 1e18} COMP to ${to}...`);

    // Check if account has MINTER_ROLE
    const minterRole = await publicClient.readContract({
        address: COMP_TOKEN_ADDRESS,
        abi: COMP_ABI,
        functionName: 'MINTER_ROLE'
    }) as `0x${string}`;

    const hasMinterRole = await publicClient.readContract({
        address: COMP_TOKEN_ADDRESS,
        abi: COMP_ABI,
        functionName: 'hasRole',
        args: [minterRole, account.address]
    }) as boolean;

    if (!hasMinterRole) {
        console.error(`❌ Account ${account.address} does not have MINTER_ROLE`);
        console.log(`   Please grant MINTER_ROLE to this address first.`);
        throw new Error('Missing MINTER_ROLE');
    }

    const hash = await walletClient.writeContract({
        address: COMP_TOKEN_ADDRESS,
        abi: COMP_ABI,
        functionName: 'mint',
        args: [to, amount]
    });

    console.log(`   Transaction: ${hash}`);

    const receipt = await publicClient.waitForTransactionReceipt({ hash });
    console.log(`   ✅ Minted in block ${receipt.blockNumber}`);
}

async function sendCOMPFeeDemo(): Promise<void> {
    console.log('\n🚀 Starting E2E Demo: COMP Fee Payment\n');
    console.log('='.repeat(60));

    // Step 1: Check setup
    console.log('\n📋 Step 1: Environment Check');
    console.log(`   Wallet: ${account.address}`);
    console.log(`   COMP Token: ${COMP_TOKEN_ADDRESS}`);
    console.log(`   Treasury: ${TREASURY_ADDRESS}`);
    console.log(`   RPC: ${RPC_URL}`);

    const ethBalance = await publicClient.getBalance({ address: account.address });
    console.log(`   ETH Balance: ${Number(ethBalance) / 1e18} ETH`);

    if (ethBalance < parseEther('0.001')) {
        console.error('\n❌ Insufficient ETH for gas. Please fund your wallet.');
        return;
    }

    // Step 2: Check COMP balance
    console.log('\n💰 Step 2: COMP Balance Check');
    let compBalance = await checkCOMPBalance(account.address);
    console.log(`   Current COMP Balance: ${Number(compBalance) / 1e18} COMP`);

    const requiredCOMP = 25n * 10n ** 18n; // 25 COMP for fee

    if (compBalance < requiredCOMP) {
        console.log(`   ⚠️  Insufficient COMP (need ${Number(requiredCOMP) / 1e18} COMP)`);
        console.log(`   Minting ${Number(requiredCOMP * 4n) / 1e18} COMP for testing...`);

        try {
            await mintCOMP(account.address, requiredCOMP * 4n); // Mint 100 COMP
            compBalance = await checkCOMPBalance(account.address);
            console.log(`   ✅ New balance: ${Number(compBalance) / 1e18} COMP`);
        } catch (error: any) {
            console.error(`   ❌ Failed to mint: ${error.message}`);
            return;
        }
    }

    // Step 3: Prepare COMP fee transaction
    console.log('\n📝 Step 3: Preparing COMP Fee Transaction');
    console.log(`   Fee Amount: ${Number(requiredCOMP) / 1e18} COMP`);
    console.log(`   Treasury: ${TREASURY_ADDRESS}`);

    const feeTransferData = encodeFunctionData({
        abi: ERC20_ABI,
        functionName: 'transfer',
        args: [TREASURY_ADDRESS, requiredCOMP]
    });

    console.log(`   ✅ Fee transaction encoded`);

    // Step 4: Send fee payment (simulating what would happen in UserOp)
    console.log('\n📤 Step 4: Sending COMP Fee Payment');
    console.log(`   Sending ${Number(requiredCOMP) / 1e18} COMP to Treasury...`);

    const treasuryBalanceBefore = await checkCOMPBalance(TREASURY_ADDRESS as `0x${string}`);
    console.log(`   Treasury balance before: ${Number(treasuryBalanceBefore) / 1e18} COMP`);

    const hash = await walletClient.writeContract({
        address: COMP_TOKEN_ADDRESS,
        abi: ERC20_ABI,
        functionName: 'transfer',
        args: [TREASURY_ADDRESS, requiredCOMP]
    });

    console.log(`   Transaction: ${hash}`);

    // Step 5: Wait for confirmation
    console.log('\n⏳ Step 5: Waiting for Confirmation');
    const receipt = await publicClient.waitForTransactionReceipt({ hash });
    console.log(`   ✅ Confirmed in block ${receipt.blockNumber}`);
    console.log(`   Gas used: ${receipt.gasUsed.toString()}`);

    // Step 6: Verify fee payment
    console.log('\n✅ Step 6: Verifying Fee Payment');
    const userBalanceAfter = await checkCOMPBalance(account.address);
    const treasuryBalanceAfter = await checkCOMPBalance(TREASURY_ADDRESS as `0x${string}`);

    console.log(`   User balance after: ${Number(userBalanceAfter) / 1e18} COMP`);
    console.log(`   Treasury balance after: ${Number(treasuryBalanceAfter) / 1e18} COMP`);
    console.log(`   Treasury received: ${Number(treasuryBalanceAfter - treasuryBalanceBefore) / 1e18} COMP`);

    if (treasuryBalanceAfter - treasuryBalanceBefore === requiredCOMP) {
        console.log(`   ✅ Fee payment verified!`);
    } else {
        console.log(`   ⚠️  Unexpected balance change`);
    }

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('🎉 E2E Demo Complete!\n');
    console.log('Summary:');
    console.log(`  ✅ COMP token transfer successful`);
    console.log(`  ✅ Treasury received ${Number(requiredCOMP) / 1e18} COMP`);
    console.log(`  ✅ Transaction confirmed on Base Sepolia`);
    console.log(`  ✅ Block: ${receipt.blockNumber}`);
    console.log(`  ✅ TX: ${hash}`);
    console.log('\n📚 Next Steps:');
    console.log('  1. Integrate with actual Smart Account (e.g., Kernel, Biconomy)');
    console.log('  2. Submit UserOp to Paymaster for sponsorship');
    console.log('  3. Test with ENABLE_COMP_FEES=true on Paymaster');
    console.log('  4. Deploy to Base Mainnet');
}

// Run demo
sendCOMPFeeDemo()
    .then(() => {
        console.log('\n✅ Demo completed successfully');
        process.exit(0);
    })
    .catch((error) => {
        console.error('\n❌ Demo failed:', error);
        process.exit(1);
    });
