import { ethers } from "hardhat";

async function main() {
    const CONTRACT_ADDRESS = "0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2";
    console.log(`Checking contract: ${CONTRACT_ADDRESS}`);

    // Force usage of a public RPC if local one fails/missing (Hardhat config might handle it, but being safe)
    // Actually, relying on Hardhat runtime is safer for now.

    const DaimToken = await ethers.getContractAt("DaimToken", CONTRACT_ADDRESS);

    // 1. Check Basics
    try {
        const decimals = await DaimToken.decimals();
        const symbol = await DaimToken.symbol();
        console.log(`Token: ${symbol} (Decimals: ${decimals})`);
    } catch (e) {
        console.error("Failed to read token basics:", e.message);
    }

    // 2. Scan for recent Transfer events (last ~1 hour)
    // Base block time is 2s. 1 hour = 1800 blocks. 
    // User said 10:45pm, now is 11:00pm. ~15 mins ago. ~450 blocks.
    const currentBlock = await ethers.provider.getBlockNumber();
    console.log(`Current Block: ${currentBlock}`);
    const fromBlock = currentBlock - 1000;

    console.log(`Scanning for Transfer events from block ${fromBlock} to ${currentBlock}...`);

    const filter = DaimToken.filters.Transfer();
    const events = await DaimToken.queryFilter(filter, fromBlock);

    console.log(`Found ${events.length} transfer events.`);

    events.forEach((event: any) => {
        const { from, to, value } = event.args;
        console.log(`\nEvent found in block ${event.blockNumber}:`);
        console.log(`  From: ${from}`);
        console.log(`  To:   ${to}`);
        console.log(`  Value (Raw): ${value.toString()}`);
        console.log(`  Value (Fmt): ${ethers.formatUnits(value, 18)}`);

        // Highlight if matches user's report
        if (value.toString() === "12500000") {
            console.log("  >>> MATCHES 12,500,000 RAW WEI REPORT <<<");
        }
        if (ethers.formatUnits(value, 18) === "12500000.0") {
            console.log("  >>> MATCHES 12,500,000 WHOLE TOKENS REPORT <<<");
        }
    });

}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});
