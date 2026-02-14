import { ethers } from "hardhat";

async function main() {
    const [keeper] = await ethers.getSigners();
    console.log("--- Keeper Bot Demo ---");
    console.log("Executor:", keeper.address);

    const TREASURY_ADDR = "0x0b68b3b12B99ADd4A8aB60Fb65Fb74b1E0455B81"; // TreasuryController
    const ORACLE_ADDR = "0x0244456E1D27A515bf6369eff19c1Ab6b01185a7"; // MockOracle

    const Treasury = await ethers.getContractAt("TreasuryController", TREASURY_ADDR);
    const Oracle = await ethers.getContractAt("MockV3Aggregator", ORACLE_ADDR); // Using Mock interface to read

    // 1. Check Epoch Status
    console.log("\n1. Checking Epoch Status...");
    const lastEpoch = await Treasury.lastEpochTime();
    const duration = await Treasury.epochDuration();
    const nextEpoch = lastEpoch + duration;

    const block = await ethers.provider.getBlock("latest");
    const now = BigInt(block!.timestamp);

    console.log(`   -> Last Epoch: ${new Date(Number(lastEpoch) * 1000).toISOString()}`);
    console.log(`   -> Next Epoch: ${new Date(Number(nextEpoch) * 1000).toISOString()}`);
    console.log(`   -> Current:    ${new Date(Number(now) * 1000).toISOString()}`);

    if (now < nextEpoch) {
        const waitSeconds = nextEpoch - now;
        console.log(`⚠️  Epoch not finished. Waiting for ${waitSeconds} seconds...`);
        console.log("   (Skipping transaction to avoid revert)");
        return;
    }

    // 2. Get Oracle Data
    console.log("\n2. Fetching Oracle Data...");
    // MockOracle returns (roundId, answer, startedAt, updatedAt, answeredInRound)
    // We just need latest answer.
    // The Treasury expects uint256 currentPrice (18 decimals? No, Oracle usually 8).
    // Let's check TreasuryController code.
    // updateEpoch(uint256 currentPrice)
    // "currentPrice The current DAIM/USD price from Oracle (18 decimals)."
    // Ah! MockOracle is 8 decimals ($50 = 50 * 10^8).
    // Treasury logic: SD59x18 price = sd(int256(currentPrice));
    // If I pass 50*10^8 (5000000000), sd() interprets it as 5e-10 (tiny). 
    // It expects 18 decimals WAD.
    // So the Keeper must loose-couple and convert 8 -> 18.

    const roundData = await Oracle.latestRoundData();
    const price8 = roundData[1]; // Answer
    const price18 = price8 * 10000000000n; // 10^10 to convert 8 to 18

    console.log(`   -> Oracle Price: $${ethers.formatUnits(price8, 8)} (${price18.toString()} wei)`);

    // 3. Execute Update
    console.log("\n3. Calling updateEpoch...");
    try {
        const tx = await Treasury.updateEpoch(price18);
        console.log("   -> Tx sent:", tx.hash);
        await tx.wait();
        console.log("✅ Epoch Updated Successfully!");

        // Log new rates
        const [burn, recycle] = await Treasury.getRates();
        console.log(`   -> New Burn Rate: ${ethers.formatEther(burn)}`);
        console.log(`   -> New Recycle:   ${ethers.formatEther(recycle)}`);

    } catch (e) {
        console.error("❌ Update Failed:", e.message);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
