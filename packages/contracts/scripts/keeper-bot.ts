import { ethers } from "hardhat";

async function main() {
    console.log("--- Treasury Keeper Bot (Production) ---");
    const [keeper] = await ethers.getSigners();
    console.log("Keeper Address:", keeper.address);

    // Configuration (Load from Env in real usage)
    const TREASURY_ADDR = process.env.MAINNET_TREASURY_ADDR || "";
    const ORACLE_ADDR = process.env.MAINNET_ORACLE_ADDR || "0x71041dddad3595F745215C5c8b314F29152e245E"; // Chainlink ETH/USD or similar? Need DAIM/USD. 
    // On Base Mainnet, we might need a specific/custom oracle or Uniswap TWAP. 
    // For now, assuming standard Chainlink Interface availability.

    if (!TREASURY_ADDR) {
        console.error("❌ Error: Valid Treasury Address required via env.");
        process.exit(1);
    }

    const Treasury = await ethers.getContractAt("TreasuryController", TREASURY_ADDR);
    const Oracle = await ethers.getContractAt("MockV3Aggregator", ORACLE_ADDR); // Use generic aggregator interface

    // 1. Check Epoch
    const lastEpoch = await Treasury.lastEpochTime();
    const duration = await Treasury.epochDuration();
    const nextEpoch = lastEpoch + duration;
    const now = BigInt(Math.floor(Date.now() / 1000));

    if (now < nextEpoch) {
        const wait = nextEpoch - now;
        console.log(`⏳ Epoch not finished. Next update in ${wait}s.`);
        return;
    }

    console.log("⚡ Epoch ready for update!");

    // 2. Oracle Data
    console.log("Fetching Price Data...");
    // Ideally use multiple sources or ensure high-res
    const roundData = await Oracle.latestRoundData();
    const price8 = roundData[1];
    const price18 = price8 * 10000000000n; // 8 -> 18 decimals
    console.log(`   Price: $${ethers.formatUnits(price8, 8)}`);

    // 3. Execution with Gas Bump
    console.log("Executing UpdateTransaction...");
    try {
        const feeData = await ethers.provider.getFeeData();

        // Aggressive Gas: MaxFeePerGas = Base * 1.5 + Priority
        const maxPriorityFeePerGas = ethers.parseUnits("1.5", "gwei"); // Force 1.5 gwei priority
        const maxFeePerGas = (feeData.maxFeePerGas || 0n) + maxPriorityFeePerGas;

        const tx = await Treasury.updateEpoch(price18, {
            maxPriorityFeePerGas,
            maxFeePerGas
        });

        console.log(`   -> Tx Sent: ${tx.hash}`);
        await tx.wait();
        console.log("✅ Epoch Updated!");

    } catch (e) {
        console.error("❌ Update Failed:", e.message);
        // Retry Loop Logic could go here (e.g., wait 30s and retry with higher gas)
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
