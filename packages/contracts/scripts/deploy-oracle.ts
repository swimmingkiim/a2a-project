import { ethers, run } from "hardhat";

async function main() {
    console.log("🚀 Deploying AdminPriceOracle...");

    // Default Initial Price: $0.10 (8 decimals)
    // 0.10 * 10^8 = 10,000,000
    const INITIAL_PRICE = process.env.INITIAL_DAIM_PRICE || "10000000";

    console.log(`   - Initial Price: ${INITIAL_PRICE} ($${parseInt(INITIAL_PRICE) / 100000000})`);

    const AdminPriceOracle = await ethers.getContractFactory("AdminPriceOracle");
    const oracle = await AdminPriceOracle.deploy(INITIAL_PRICE);

    await oracle.waitForDeployment();
    const address = await oracle.getAddress();

    console.log(`✅ AdminPriceOracle deployed to: ${address}`);
    console.log(`👉 Add this to your .env: CHAINLINK_ORACLE_ADDRESS=${address}`);

    // Verify
    console.log("⏳ Waiting for 5 block confirmations before verification...");
    await oracle.deploymentTransaction()?.wait(5);

    try {
        await run("verify:verify", {
            address: address,
            constructorArguments: [INITIAL_PRICE],
        });
        console.log("✅ Contract Verified!");
    } catch (error) {
        console.warn("⚠️ Verification Failed:", error);
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
