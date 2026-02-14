#!/usr/bin/env tsx

/**
 * Grant MINTER_ROLE to a specific address
 * Used for E2E testing
 */

import { createPublicClient, createWalletClient, http, parseAbi } from 'viem';
import { base } from 'viem/chains';
import { privateKeyToAccount } from 'viem/accounts';
import { config } from 'dotenv';
import { z } from 'zod';

config();

const DAIM_TOKEN_ADDRESS = '0x1F478c3F6a09c3820baBd3f6DCD8bEA4eE5dc806'; // Base Mainnet
const ADMIN_PRIVATE_KEY = process.env.DEPLOYER_PRIVATE_KEY as `0x${string}`;
const RECIPIENT_ADDRESS = process.env.PAYMASTER_ADDRESS as `0x${string}`; // Target Paymaster Address
const RPC_URL = process.env.BASE_MAINNET_RPC_URL || 'https://mainnet.base.org';

const DAIM_ABI = parseAbi([
    'function grantRole(bytes32 role, address account) public',
    'function hasRole(bytes32 role, address account) view returns (bool)',
    'function MINTER_ROLE() view returns (bytes32)',
    'function DEFAULT_ADMIN_ROLE() view returns (bytes32)'
]);

async function grantMinterRole() {
    console.log('🔑 Granting MINTER_ROLE for Base Mainnet\n');

    if (!ADMIN_PRIVATE_KEY) throw new Error("DEPLOYER_PRIVATE_KEY is missing");
    if (!RECIPIENT_ADDRESS) throw new Error("PAYMASTER_ADDRESS is missing (Target to grant role)");

    const account = privateKeyToAccount(ADMIN_PRIVATE_KEY);

    const publicClient = createPublicClient({
        chain: base,
        transport: http(RPC_URL)
    });

    const walletClient = createWalletClient({
        account,
        chain: base,
        transport: http(RPC_URL)
    });

    console.log(`Admin: ${account.address}`);
    console.log(`Recipient: ${RECIPIENT_ADDRESS}`);
    console.log(`DAIM Token: ${DAIM_TOKEN_ADDRESS}\n`);

    // Get MINTER_ROLE
    const minterRole = await publicClient.readContract({
        address: DAIM_TOKEN_ADDRESS,
        abi: DAIM_ABI,
        functionName: 'MINTER_ROLE'
    }) as `0x${string}`;

    console.log(`MINTER_ROLE: ${minterRole}`);

    // Check if already has role
    const hasRole = await publicClient.readContract({
        address: DAIM_TOKEN_ADDRESS,
        abi: DAIM_ABI,
        functionName: 'hasRole',
        args: [minterRole, RECIPIENT_ADDRESS]
    }) as boolean;

    if (hasRole) {
        console.log(`\n✅ ${RECIPIENT_ADDRESS} already has MINTER_ROLE`);
        return;
    }

    // Grant role
    console.log(`\n📝 Granting MINTER_ROLE...`);
    const hash = await walletClient.writeContract({
        address: DAIM_TOKEN_ADDRESS,
        abi: DAIM_ABI,
        functionName: 'grantRole',
        args: [minterRole, RECIPIENT_ADDRESS]
    });

    console.log(`Transaction: ${hash}`);

    const receipt = await publicClient.waitForTransactionReceipt({ hash });
    console.log(`✅ Role granted in block ${receipt.blockNumber}`);

    // Verify
    const hasRoleNow = await publicClient.readContract({
        address: DAIM_TOKEN_ADDRESS,
        abi: DAIM_ABI,
        functionName: 'hasRole',
        args: [minterRole, RECIPIENT_ADDRESS]
    }) as boolean;

    if (hasRoleNow) {
        console.log(`\n✅ Verified: ${RECIPIENT_ADDRESS} now has MINTER_ROLE`);
    } else {
        console.log(`\n❌ Role grant failed`);
    }
}

grantMinterRole()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
