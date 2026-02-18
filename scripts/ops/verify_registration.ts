
import { createPublicClient, http, parseAbi, formatUnits } from 'viem';
import { base } from 'viem/chains';

const REGISTRY_ADDRESS = '0xF720826C02AAfaEC56959387d61efA501eB1E56e';

const REGISTRY_ABI = parseAbi([
    'function agents(address) external view returns (string metadataUrl, uint256 stakedAmount, uint256 resourceUnits, uint64 registeredAt, bool isRegistered, uint8 reputation, uint256 lastComplexityHash)',
    'event AgentRegistered(address indexed agent, string metadataUrl, uint256 resourceUnits, uint256 stakedAmount)'
]);

async function main() {
    const txHash = process.argv[2];
    if (!txHash) {
        console.error('Usage: pnpm tsx scripts/ops/verify_registration.ts <TX_HASH>');
        process.exit(1);
    }

    const client = createPublicClient({ chain: base, transport: http('https://mainnet.base.org') });

    console.log(`\n🔍 Checking Transaction: ${txHash}\n`);
    const receipt = await client.getTransactionReceipt({ hash: txHash as `0x${string}` });

    console.log(`Status:      ${receipt.status === 'success' ? '✅ SUCCESS' : '❌ REVERTED'}`);
    console.log(`Block:       ${receipt.blockNumber}`);
    console.log(`From:        ${receipt.from}`);
    console.log(`To:          ${receipt.to}`);
    console.log(`Gas Used:    ${receipt.gasUsed}`);
    console.log(`Logs Count:  ${receipt.logs.length}`);

    if (receipt.status !== 'success') {
        console.log('\n❌ Transaction FAILED on-chain.');
        return;
    }

    const agentAddress = receipt.from;
    console.log(`\n📋 Checking Agent Registration for ${agentAddress}...`);

    try {
        const agent = await client.readContract({
            address: REGISTRY_ADDRESS,
            abi: REGISTRY_ABI,
            functionName: 'agents',
            args: [agentAddress]
        });

        const [metadataUrl, stakedAmount, resourceUnits, registeredAt, isRegistered, reputation] = agent;

        if (isRegistered) {
            console.log(`\n🎉 AGENT IS REGISTERED!`);
            console.log(`   Metadata URL:    ${metadataUrl}`);
            console.log(`   Staked Amount:   ${formatUnits(stakedAmount, 18)} DAIM`);
            console.log(`   Resource Units:  ${resourceUnits}`);
            console.log(`   Registered At:   ${new Date(Number(registeredAt) * 1000).toISOString()}`);
            console.log(`   Reputation:      ${reputation}`);
        } else {
            console.log(`\n⚠️ Agent is NOT registered despite TX success.`);
        }
    } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        console.log(`\n❌ Error reading agent: ${msg}`);
    }
}

main().catch(console.error);
