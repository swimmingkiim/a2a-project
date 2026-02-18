
import { createPublicClient, http, parseAbi } from 'viem';
import { base } from 'viem/chains';

const VERIFIER_ADDRESS = "0xc173A512b3394f6897F9B20c7A411B5247BCeD19";

async function main() {
    const client = createPublicClient({
        chain: base,
        transport: http("https://mainnet.base.org")
    });

    console.log(`Checking CredentialVerifier at ${VERIFIER_ADDRESS}...`);

    const voucher = await client.readContract({
        address: VERIFIER_ADDRESS,
        abi: parseAbi(['function bootstrapVoucher() external view returns (address)']),
        functionName: 'bootstrapVoucher'
    });

    console.log(`\n✅ Contract EXPECTS signatures from: ${voucher}`);
    if (voucher === "0x8246a807bD699B214e02F5309e3E173C33E62a9B") {
        console.log("   (This address matches the one previously identified as unknown/missing)");
    } else {
        console.log("   (This is the currently active voucher address)");
    }
}

main().catch(console.error);
