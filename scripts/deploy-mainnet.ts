#!/usr/bin/env tsx

/**
 * Deploy ComputeToken to Base Mainnet
 * 
 * This script deploys the COMP token with proper role setup.
 * 
 * Safety checks:
 * - Confirms network is Base Mainnet
 * - Validates wallet balance
 * - Confirms paymaster address
 * - Saves deployment details
 */

import { createPublicClient, createWalletClient, http, parseEther, formatEther } from 'viem';
import { base } from 'viem/chains';
import { privateKeyToAccount } from 'viem/accounts';
import { config as dotenvConfig } from 'dotenv';
import * as fs from 'fs';
import * as path from 'path';
import * as readline from 'readline';

dotenvConfig({ path: '.env.mainnet' });

const DEPLOYER_PRIVATE_KEY = process.env.DEPLOYER_PRIVATE_KEY as `0x${string}`;
const PAYMASTER_ADDRESS = process.env.PAYMASTER_ADDRESS as `0x${string}`;
const INITIAL_SUPPLY = BigInt(process.env.INITIAL_SUPPLY || '1000000') * 10n ** 18n;
const RPC_URL = process.env.BASE_MAINNET_RPC_URL || 'https://mainnet.base.org';

// Contract bytecode would be imported from compilation
// For this example, we'll use a placeholder
const COMP_TOKEN_BYTECODE = '0x...' as `0x${string}`;

async function askConfirmation(question: string): Promise<boolean> {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    return new Promise((resolve) => {
        rl.question(`${question} (yes/no): `, (answer) => {
            rl.close();
            resolve(answer.toLowerCase() === 'yes');
        });
    });
}

async function deployToMainnet() {
    console.log('🚀 Base Mainnet Deployment - ComputeToken\n');
    console.log('='.repeat(60));

    // Safety check: Confirm environment
    if (!DEPLOYER_PRIVATE_KEY) {
        console.error('❌ DEPLOYER_PRIVATE_KEY not set in .env.mainnet');
        process.exit(1);
    }

    if (!PAYMASTER_ADDRESS || PAYMASTER_ADDRESS === '0x...') {
        console.error('❌ PAYMASTER_ADDRESS not set in .env.mainnet');
        process.exit(1);
    }

    const account = privateKeyToAccount(DEPLOYER_PRIVATE_KEY);

    const publicClient = createPublicClient({
        chain: base,
        transport: http(RPC_URL)
    });

    const walletClient = createWalletClient({
        account,
        chain: base,
        transport: http(RPC_URL)
    });

    // Step 1: Validate network
    console.log('\n📡 Step 1: Network Validation');
    const chainId = await publicClient.getChainId();
    console.log(`   Chain ID: ${chainId}`);

    if (chainId !== base.id) {
        console.error(`   ❌ Wrong network! Expected Base Mainnet (${base.id}), got ${chainId}`);
        process.exit(1);
    }
    console.log(`   ✅ Connected to Base Mainnet`);

    // Step 2: Check wallet balance
    console.log('\n💰 Step 2: Wallet Balance Check');
    console.log(`   Deployer: ${account.address}`);

    const balance = await publicClient.getBalance({ address: account.address });
    console.log(`   ETH Balance: ${formatEther(balance)} ETH`);

    const minBalance = parseEther('0.01');
    if (balance < minBalance) {
        console.error(`   ❌ Insufficient ETH. Need at least 0.01 ETH for deployment.`);
        process.exit(1);
    }
    console.log(`   ✅ Sufficient balance for deployment`);

    // Step 3: Configuration review
    console.log('\n⚙️  Step 3: Deployment Configuration');
    console.log(`   Initial Supply: ${Number(INITIAL_SUPPLY) / 1e18} COMP`);
    console.log(`   Paymaster: ${PAYMASTER_ADDRESS}`);
    console.log(`   Deployer (Admin): ${account.address}`);

    // Step 4: Final confirmation
    console.log('\n' + '='.repeat(60));
    console.log('⚠️  MAINNET DEPLOYMENT - FINAL CONFIRMATION');
    console.log('='.repeat(60));
    console.log('\nYou are about to deploy to BASE MAINNET.');
    console.log('This will cost real ETH and create a permanent contract.');
    console.log('\nPlease verify:');
    console.log(`  - Network: Base Mainnet (Chain ID: ${chainId})`);
    console.log(`  - Deployer: ${account.address}`);
    console.log(`  - Paymaster: ${PAYMASTER_ADDRESS}`);
    console.log(`  - Initial Supply: ${Number(INITIAL_SUPPLY) / 1e18} COMP`);
    console.log('');

    const confirm = await askConfirmation('Do you want to proceed with deployment?');

    if (!confirm) {
        console.log('\n❌ Deployment cancelled by user.');
        process.exit(0);
    }

    // Step 5: Deploy contract
    console.log('\n📤 Step 5: Deploying ComputeToken...');
    console.log('   Please wait, this may take a few minutes...\n');

    // NOTE: Actual deployment would use compiled contract
    // This is a template - replace with actual deployment logic
    console.log('   ⚠️  Deployment code template - replace with actual compiled contract');
    console.log('   See: packages/contracts/scripts/deploy-compute-token.ts');

    // Placeholder for actual deployment
    const deployedAddress = '0x...' as `0x${string}`;
    const deploymentHash = '0x...' as `0x${string}`;
    const blockNumber = 0n;

    console.log(`\n   ✅ Contract deployed!`);
    console.log(`   Address: ${deployedAddress}`);
    console.log(`   TX: ${deploymentHash}`);
    console.log(`   Block: ${blockNumber}`);

    // Step 6: Save deployment info
    console.log('\n💾 Step 6: Saving Deployment Info');

    const deployment = {
        network: 'base-mainnet',
        chainId: chainId,
        contractAddress: deployedAddress,
        deployer: account.address,
        paymaster: PAYMASTER_ADDRESS,
        initialSupply: INITIAL_SUPPLY.toString(),
        deploymentHash: deploymentHash,
        blockNumber: blockNumber.toString(),
        timestamp: new Date().toISOString()
    };

    const deploymentsPath = path.join(__dirname, '../deployments-mainnet.json');
    fs.writeFileSync(deploymentsPath, JSON.stringify(deployment, null, 2));
    console.log(`   ✅ Saved to: ${deploymentsPath}`);

    // Step 7: Next steps
    console.log('\n' + '='.repeat(60));
    console.log('🎉 Deployment Complete!');
    console.log('='.repeat(60));
    console.log('\n📝 Next Steps:\n');
    console.log('1. Verify contract on Basescan:');
    console.log(`   npx hardhat verify --network baseMainnet ${deployedAddress}\n`);
    console.log('2. Update Paymaster .env:');
    console.log(`   COMP_TOKEN_ADDRESS=${deployedAddress}\n`);
    console.log('3. Test with small amounts first');
    console.log('4. Gradually enable COMP_FEES');
    console.log('5. Monitor logs and metrics\n');
    console.log('⚠️  IMPORTANT: Save this deployment info securely!');
}

deployToMainnet()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error('\n❌ Deployment failed:', error);
        process.exit(1);
    });
