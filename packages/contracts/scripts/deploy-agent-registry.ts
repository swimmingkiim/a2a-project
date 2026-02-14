import { ethers, run } from "hardhat";

async function main() {
    console.log("🚀 Deploying AgentRegistry to Base Mainnet...");

    // 1. Configuration (Load from Env or Config)
    // You should ensure these are set in your .env file
    const DAIM_TOKEN_ADDRESS = process.env.DAIM_TOKEN_ADDRESS;
    const CHAINLINK_ORACLE_ADDRESS = process.env.CHAINLINK_ORACLE_ADDRESS || "0xcD2A119bD1F7DF95d706DE6F2057fDD45A0503E2"; // Base Mainnet DAIM/USD Feed (Example) - PLEASE VERIFY
    const TREASURY_ADDRESS = process.env.TREASURY_ADDRESS;
    const ADMIN_ADDRESS = process.env.ADMIN_ADDRESS || (await ethers.getSigners())[0].address;

    if (!DAIM_TOKEN_ADDRESS || !TREASURY_ADDRESS) {
        throw new Error("❌ Missing Environment Variables: DAIM_TOKEN_ADDRESS or TREASURY_ADDRESS");
    }

    console.log(`📋 Configuration:`);
    console.log(`   - DAIM Token: ${DAIM_TOKEN_ADDRESS}`);
    console.log(`   - Oracle: ${CHAINLINK_ORACLE_ADDRESS}`);
    console.log(`   - Treasury: ${TREASURY_ADDRESS}`);
    console.log(`   - Admin: ${ADMIN_ADDRESS}`);

    // 2. Deploy Contract
    const AgentRegistry = await ethers.getContractFactory("AgentRegistry");
    const agentRegistry = await AgentRegistry.deploy(
        DAIM_TOKEN_ADDRESS,
        CHAINLINK_ORACLE_ADDRESS,
        TREASURY_ADDRESS,
        ADMIN_ADDRESS
    );

    await agentRegistry.waitForDeployment();
    const address = await agentRegistry.getAddress();

    console.log(`✅ AgentRegistry deployed to: ${address}`);

    // 3. Verify Contract (Wait for a few block confirmations)
    console.log("⏳ Waiting for 5 block confirmations before verification...");
    await agentRegistry.deploymentTransaction()?.wait(5);

    try {
        await run("verify:verify", {
            address: address,
            constructorArguments: [
                DAIM_TOKEN_ADDRESS,
                CHAINLINK_ORACLE_ADDRESS,
                TREASURY_ADDRESS,
                ADMIN_ADDRESS
            ],
        });
        console.log("✅ Contract Verified on BaseScan!");
    } catch (error) {
        console.warn("⚠️ Verification Failed (Manual Verification Required):", error);
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
