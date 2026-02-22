import { ethers, upgrades } from "hardhat";

async function main() {
    const [deployer] = await ethers.getSigners();
    if (!deployer) throw new Error("Deployer account is missing. Did you provide DEPLOYER_PRIVATE_KEY?");

    console.log("-----------------------------------------");
    console.log("   DEPLOYING TRUE QUANTUM TASK BUFFER    ");
    console.log("-----------------------------------------");
    console.log("Deployer:", deployer.address);

    // Original, True Mainnet Addresses
    const TRUE_DAIM_ADDRESS = "0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2";
    const TRUE_REGISTRY_ADDRESS = "0xF720826C02AAfaEC56959387d61efA501eB1E56e";
    const TRUE_TREASURY_ADDRESS = "0x129154b7E3f0Ab0E59615ef578f6511b072FB431";

    console.log("\n1️⃣ Deploying True OracleRegistry (UUPS Proxy)...");
    const OracleRegistry = await ethers.getContractFactory("OracleRegistry");
    const oracleRegistry = await upgrades.deployProxy(OracleRegistry, [
        deployer.address
    ], { kind: 'uups' });
    await oracleRegistry.waitForDeployment();
    const oracleRegistryAddress = await oracleRegistry.getAddress();
    console.log("✅ OracleRegistry Deployed:", oracleRegistryAddress);

    console.log("\n2️⃣ Deploying True QuantumTaskBuffer (UUPS Proxy)...");
    const QuantumTaskBuffer = await ethers.getContractFactory("QuantumTaskBuffer");
    const taskBuffer = await upgrades.deployProxy(QuantumTaskBuffer, [
        TRUE_DAIM_ADDRESS,
        TRUE_REGISTRY_ADDRESS,
        TRUE_TREASURY_ADDRESS,
        deployer.address
    ], { kind: 'uups' });
    await taskBuffer.waitForDeployment();
    const taskBufferAddress = await taskBuffer.getAddress();
    console.log("✅ QuantumTaskBuffer Deployed:", taskBufferAddress);

    console.log("\n3️⃣ Wiring Contracts Together...");

    // Set OracleRegistry in TaskBuffer
    const tx1 = await taskBuffer.setOracleRegistry(oracleRegistryAddress);
    await tx1.wait(1);
    console.log("   -> Wired OracleRegistry to TaskBuffer");

    // Grant TASK_BUFFER_ROLE in OracleRegistry to TaskBuffer
    const TASK_BUFFER_ROLE = await oracleRegistry.TASK_BUFFER_ROLE();
    const tx2 = await oracleRegistry.grantRole(TASK_BUFFER_ROLE, taskBufferAddress);
    await tx2.wait(1);
    console.log("   -> Granted TASK_BUFFER_ROLE to TaskBuffer");

    console.log("\n4️⃣ Granting Required Roles...");
    const daim = await ethers.getContractAt("DaimToken", TRUE_DAIM_ADDRESS);
    const registry = await ethers.getContractAt("AgentRegistry", TRUE_REGISTRY_ADDRESS);

    // Grant MINTER_ROLE to TaskBuffer (so it can mint rewards, if needed, though MVP fee is from deposit)
    const MINTER_ROLE = await daim.MINTER_ROLE();
    const hasMinter = await daim.hasRole(MINTER_ROLE, taskBufferAddress);
    if (!hasMinter) {
        console.log("   -> Granting MINTER_ROLE on True DAIM to TaskBuffer...");
        const tx3 = await daim.grantRole(MINTER_ROLE, taskBufferAddress);
        await tx3.wait(1);
    }

    // Grant ORACLE_ROLE in Registry to TaskBuffer (so TaskBuffer can update reputation)
    const ORACLE_ROLE = await registry.ORACLE_ROLE();
    const hasOracle = await registry.hasRole(ORACLE_ROLE, taskBufferAddress);
    if (!hasOracle) {
        console.log("   -> Granting ORACLE_ROLE on True Registry to TaskBuffer...");
        const tx4 = await registry.grantRole(ORACLE_ROLE, taskBufferAddress);
        await tx4.wait(1);
    }

    console.log("\n✅ Script Complete. The True Ecosystem is now Restored.");
}

main().catch(console.error);
