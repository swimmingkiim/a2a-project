import { ethers } from "hardhat";

async function main() {
    const [deployer] = await ethers.getSigners();
    if (!deployer) throw new Error("Deployer account is missing. Did you provide DEPLOYER_PRIVATE_KEY?");

    console.log("-----------------------------------------");
    console.log("   WIRING TRUE QUANTUM TASK BUFFER       ");
    console.log("-----------------------------------------");
    console.log("Deployer:", deployer.address);

    const TRUE_DAIM_ADDRESS = "0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2";
    const TRUE_REGISTRY_ADDRESS = "0xF720826C02AAfaEC56959387d61efA501eB1E56e";
    const ORACLE_REGISTRY = "0x97dAC2DAeb07FB5A39855A23BAc5FCfCFb7dFFbE";
    const TASK_BUFFER = "0x68F71c8dd0f056001dB59f34f28eDa92bb15e4B5";

    const oracleRegistry = await ethers.getContractAt("OracleRegistry", ORACLE_REGISTRY);
    const taskBuffer = await ethers.getContractAt("QuantumTaskBuffer", TASK_BUFFER);
    const daim = await ethers.getContractAt("DaimToken", TRUE_DAIM_ADDRESS);
    const registry = await ethers.getContractAt("AgentRegistry", TRUE_REGISTRY_ADDRESS);

    // Manual nonce tracking to avoid mempool 'nonce too low' issues
    let currentNonce = await deployer.getNonce("pending");
    console.log("Current Nonce:", currentNonce);

    console.log("\n3️⃣ Wiring Contracts Together...");

    try {
        const tx1 = await taskBuffer.setOracleRegistry(ORACLE_REGISTRY, { nonce: currentNonce++ });
        await tx1.wait(1);
        console.log("   -> Wired OracleRegistry to TaskBuffer");
    } catch (e: any) {
        console.log("   -> setOracleRegistry failed or already set. Error:", e.message);
    }

    try {
        const TASK_BUFFER_ROLE = await oracleRegistry.TASK_BUFFER_ROLE();
        const tx2 = await oracleRegistry.grantRole(TASK_BUFFER_ROLE, TASK_BUFFER, { nonce: currentNonce++ });
        await tx2.wait(1);
        console.log("   -> Granted TASK_BUFFER_ROLE to TaskBuffer");
    } catch (e: any) {
        console.log("   -> grantRole (TASK_BUFFER_ROLE) failed or already granted. Error:", e.message);
    }

    console.log("\n4️⃣ Granting Required Roles...");

    const MINTER_ROLE = await daim.MINTER_ROLE();
    const hasMinter = await daim.hasRole(MINTER_ROLE, TASK_BUFFER);
    if (!hasMinter) {
        console.log("   -> Granting MINTER_ROLE on True DAIM to TaskBuffer...");
        try {
            const tx3 = await daim.grantRole(MINTER_ROLE, TASK_BUFFER, { nonce: currentNonce++ });
            await tx3.wait(1);
            console.log("   -> MINTER_ROLE granted!");
        } catch (e: any) {
            console.log("   -> MINTER_ROLE grant failed:", e.message);
        }
    } else {
        console.log("   -> TaskBuffer already has MINTER_ROLE on True DAIM");
    }

    const ORACLE_ROLE = await registry.ORACLE_ROLE();
    const hasOracle = await registry.hasRole(ORACLE_ROLE, TASK_BUFFER);
    if (!hasOracle) {
        console.log("   -> Granting ORACLE_ROLE on True Registry to TaskBuffer...");
        try {
            const tx4 = await registry.grantRole(ORACLE_ROLE, TASK_BUFFER, { nonce: currentNonce++ });
            await tx4.wait(1);
            console.log("   -> ORACLE_ROLE granted!");
        } catch (e: any) {
            console.log("   -> ORACLE_ROLE grant failed:", e.message);
        }
    } else {
        console.log("   -> TaskBuffer already has ORACLE_ROLE on True Registry");
    }

    console.log("\n✅ Script Complete. The True Ecosystem is now Restored.");
}

main().catch(console.error);
