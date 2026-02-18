
import { createWalletClient, createPublicClient, http, parseAbi } from 'viem';
import { privateKeyToAccount, generatePrivateKey } from 'viem/accounts';
import { base } from 'viem/chains';
import * as dotenv from 'dotenv';
dotenv.config();

const VERIFIER_ADDRESS = "0xc173A512b3394f6897F9B20c7A411B5247BCeD19";
const ADMIN_KEY = process.env.DEPLOYER_PRIVATE_KEY as `0x${string}`;

async function main() {
    if (!ADMIN_KEY) {
        throw new Error("DEPLOYER_PRIVATE_KEY not found in .env");
    }

    const admin = privateKeyToAccount(ADMIN_KEY);
    const client = createWalletClient({
        account: admin,
        chain: base,
        transport: http("https://mainnet.base.org")
    });
    const publicClient = createPublicClient({ chain: base, transport: http("https://mainnet.base.org") });

    // 1. Generate New Voucher Key
    const newPrivateKey = generatePrivateKey();
    const newAccount = privateKeyToAccount(newPrivateKey);
    console.log("\n🔑 New Bootstrap Voucher Generated:");
    console.log(`Address: ${newAccount.address}`);
    console.log(`Private Key: ${newPrivateKey}`);
    console.log("⚠️  SAVE THIS PRIVATE KEY TO GCP SECRET [VOUCHER_PRIVATE_KEY] IMMEDIATELY! ⚠️\n");

    // 2. Update Contract
    console.log(`Updating CredentialVerifier (${VERIFIER_ADDRESS}) with new voucher...`);
    const hash = await client.writeContract({
        address: VERIFIER_ADDRESS,
        abi: parseAbi(['function setBootstrapVoucher(address) external']),
        functionName: 'setBootstrapVoucher',
        args: [newAccount.address]
    });

    console.log(`✅ Transaction Sent: ${hash}`);
    await publicClient.waitForTransactionReceipt({ hash });
    console.log("✅ Contract Updated Successfully!");
}

main().catch(console.error);
