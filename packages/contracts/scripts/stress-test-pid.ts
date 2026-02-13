import { ethers } from "hardhat";

async function main() {
    const [deployer] = await ethers.getSigners();

    // REPLACE THESE AFTER DEPLOYMENT
    // (We will use sed or manual copy-paste in a real workflow, 
    // here I'll try to read from a file or just ask user to update? 
    // Better: I'll accept them as args or just hardcode for the specific run.
    // For now, I'll put placeholders and we will update them after running deploy.)

    // Hardcoded Addresses from deployment targeting Base Sepolia (Stress Test Env)
    const ORACLE_ADDR = "0x590d72Cf19DE2757662b4451D0c05940Eb9B74f8";
    const TREASURY_ADDR = "0x7465EbF286116F14AD013a9199237F85093Ac877";
    const REGISTRY_ADDR = "0xf59a3E157a72E41AFA4EA816e5d6FA30F5c74042";
    const VERIFIER_ADDR = "0xABCD7235e4426012F553eC409C539058997ad959";

    // if (!ORACLE_ADDR || !TREASURY_ADDR) { ... } // Removed check

    const MockOracle = await ethers.getContractAt("MockV3Aggregator", ORACLE_ADDR);
    const Treasury = await ethers.getContractAt("TreasuryController", TREASURY_ADDR);
    const Registry = await ethers.getContractAt("AgentRegistry", REGISTRY_ADDR);

    console.log("--- Starting PID Stress Test ---");
    console.log("Target: $50 USD");
    console.log("Epoch: 60s");

    // Simulation Loop
    for (let i = 0; i < 20; i++) { // Run for ~20 iterations
        console.log(`\n--- Iteration ${i + 1}/20 ---`);

        // 1. Random Price Movement (+/- $5)
        const currentPrice = 50 + (Math.random() * 10 - 5); // 45 to 55
        const price8 = BigInt(Math.floor(currentPrice * 1e8));
        const price18 = BigInt(Math.floor(currentPrice * 1e18)); // Helper for Keeper

        console.log(`\n[Market] Price moves to $${currentPrice.toFixed(2)}`);

        // Update Oracle
        const txOracle = await MockOracle.updatePrice(price8);
        await txOracle.wait();

        // 2. Keeper Update
        // Check if upgradable
        try {
            const txUpdate = await Treasury.updateEpoch(price18);
            await txUpdate.wait();
            console.log("[Keeper] Epoch Updated!");

            // Log New Rates
            const [burn, recycle] = await Treasury.getRates();
            console.log(`[PID] New Burn Rate: ${ethers.formatEther(burn)}`);
            // Check Direction
            // Burn should go UP if Price < 50
            // Burn should go DOWN if Price > 50
        } catch (e) {
            if (e.message.includes("EpochNotFinished")) {
                console.log("[Keeper] Skipping (Epoch Not Finished)");
            } else {
                console.log("[Keeper] Error:", e.message);
            }
        }

        // 3. Agent Activity
        // Register a dummy agent (re-using same address with different units? 
        // Registry checks !isRegistered. So we have to unstake first or use new wallet.
        // For simplicity, we just Calculate Cost to see impact of Price.)

        // Cost = Base($10) * Units^2
        // If Price is Low, Cost in COMP should be High.
        // If Price is High, Cost in COMP should be Low.

        const units = 5;
        const costUSD = BigInt(250 * 1e8); // $10 * 25 = $250
        const costComp = await Registry.getCompAmountFromUSD(costUSD);

        console.log(`[Agent] Cost for 5 Units ($250): ${ethers.formatEther(costComp)} COMP`);

        console.log("Waiting 30 seconds...");
        await new Promise(r => setTimeout(r, 30000));
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
