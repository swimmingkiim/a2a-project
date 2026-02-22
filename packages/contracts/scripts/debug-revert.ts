import { ethers } from "hardhat";

async function main() {
    const BOT_ADDRESS = "0x68E0F8d90c7Afe4a22Ea62f71814F71Fc3A9FE6F";
    const TASK_BUFFER = "0x68F71c8dd0f056001dB59f34f28eDa92bb15e4B5";
    const TRUE_DAIM = "0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2";
    const TRUE_REGISTRY = "0xF720826C02AAfaEC56959387d61efA501eB1E56e";

    console.log("-----------------------------------------");
    console.log("   DEBUGGING TRUE QUANTUM TASK BUFFER    ");
    console.log("-----------------------------------------");

    // 1. Check Task Buffer State
    const taskBuffer = await ethers.getContractAt("QuantumTaskBuffer", TASK_BUFFER);
    const registryAddress = await taskBuffer.registry();
    const daimAddress = await taskBuffer.daimToken();
    const baseDeposit = await taskBuffer.baseDeposit();

    console.log("TaskBuffer's Internal State:");
    console.log(" - Registry Address matches TRUE:", registryAddress === TRUE_REGISTRY, `(${registryAddress})`);
    console.log(" - DAIM Address matches TRUE:", daimAddress === TRUE_DAIM, `(${daimAddress})`);
    console.log(" - Base Deposit:", ethers.formatEther(baseDeposit), "DAIM");

    // 2. Check Bot State
    const registry = await ethers.getContractAt("AgentRegistry", TRUE_REGISTRY);
    const daim = await ethers.getContractAt("DaimToken", TRUE_DAIM);

    const isRegistered = (await registry.agents(BOT_ADDRESS)).isRegistered;
    const balance = await daim.balanceOf(BOT_ADDRESS);
    const allowance = await daim.allowance(BOT_ADDRESS, TASK_BUFFER);

    console.log("\nBot's On-Chain State:");
    console.log(" - Registered on TRUE Registry:", isRegistered);
    console.log(" - DAIM Balance:", ethers.formatEther(balance));
    console.log(" - Allowance to TaskBuffer:", ethers.formatEther(allowance));

    console.log("\n3️⃣ Simulating `submitTask` via eth_call...");
    const complexityHash = ethers.id("debug_task");
    const metadataUri = "ipfs://QmDebug";

    try {
        // We use callStatic / staticCall to simulate the transaction
        await taskBuffer.getFunction("submitTask").staticCall(
            complexityHash,
            metadataUri,
            { from: BOT_ADDRESS }
        );
        console.log("✅ Simulation SUCCEEDED! No revert in the logic itself. Suspect gas issues or front-end input types.");
    } catch (e: any) {
        console.log("❌ Simulation REVERTED. Reason:");
        if (e.reason) {
            console.log("   ->", e.reason);
        } else if (e.data) {
            console.log("   -> Data:", e.data);
        } else {
            console.log(e);
        }
    }
}

main().catch(console.error);
