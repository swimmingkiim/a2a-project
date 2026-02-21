
import { ethers, upgrades } from "hardhat";
import dotenv from "dotenv";

dotenv.config();

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

console.log("-----------------------------------------");
console.log("   QUANTUM A2A DEPLOYMENT: UUPS UPGRADE  ");
console.log("-----------------------------------------");

async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("🔹 Deployer:", deployer.address);
    const balance = await ethers.provider.getBalance(deployer.address);
    // console.log("🔹 Balance:", ethers.formatEther(balance), "ETH");

    // --- 0. Prepare Dependencies ---
    let daimTokenAddress = process.env.DAIM_TOKEN_ADDRESS || "";
    let mockOracleAddress = process.env.CHAINLINK_ORACLE_ADDRESS || "";
    let mockVerifierAddress = process.env.DID_VERIFIER_ADDRESS || "";
    const treasuryAddress = process.env.TREASURY_ADDRESS || deployer.address;

    // --- 1. Mocks (If missing) ---
    if (!mockOracleAddress) {
        console.log("🔸 Deploying MockOracle...");
        const MockOracle = await ethers.getContractFactory("MockV3Aggregator");
        const mockOracle = await MockOracle.deploy(8, 200000000000); // $2000 ETH
        await mockOracle.waitForDeployment();
        mockOracleAddress = await mockOracle.getAddress();
        console.log("   -> MockOracle deployed at:", mockOracleAddress);
        await delay(3000);
    }

    if (!mockVerifierAddress) {
        console.log("🔸 Deploying MockVerifier...");
        const MockVerifier = await ethers.getContractFactory("contracts/mocks/MockVerifier.sol:MockVerifier");
        const mockVerifier = await MockVerifier.deploy();
        await mockVerifier.waitForDeployment();
        mockVerifierAddress = await mockVerifier.getAddress();
        console.log("   -> MockVerifier deployed at:", mockVerifierAddress);
        await delay(3000);
    }

    // --- 2. Deploy DaimToken (UUPS Upgradeable) ---
    let daimToken;

    if (!daimTokenAddress) {
        console.log("🔸 Deploying DaimToken (UUPS Proxy)...");
        const DaimToken = await ethers.getContractFactory("DaimToken");
        // Initialize with deployer as default admin
        daimToken = await upgrades.deployProxy(DaimToken, [deployer.address], {
            kind: 'uups',
            initializer: 'initialize'
        });
        await daimToken.waitForDeployment();
        daimTokenAddress = await daimToken.getAddress();
        console.log("   -> DaimToken Proxy deployed at:", daimTokenAddress);
        await delay(4000);
    } else {
        const DaimToken = await ethers.getContractFactory("DaimToken");
        daimToken = DaimToken.attach(daimTokenAddress);
    }

    // --- 3. Deploy AgentRegistry (UUPS Upgradeable) ---
    console.log("🔸 Deploying AgentRegistry (UUPS Proxy)...");
    const AgentRegistry = await ethers.getContractFactory("AgentRegistry");
    const agentRegistry = await upgrades.deployProxy(AgentRegistry, [
        daimTokenAddress,
        mockOracleAddress,
        treasuryAddress,
        mockVerifierAddress,
        deployer.address
    ], { kind: 'uups' });
    await agentRegistry.waitForDeployment();
    const registryAddress = await agentRegistry.getAddress();
    console.log("   -> AgentRegistry Proxy deployed at:", registryAddress);
    await delay(4000);

    // --- 3.5 Deploy OracleRegistry (UUPS Upgradeable) ---
    console.log("🔸 Deploying OracleRegistry (UUPS Proxy)...");
    const OracleRegistry = await ethers.getContractFactory("OracleRegistry");
    const oracleRegistry = await upgrades.deployProxy(OracleRegistry, [
        deployer.address
    ], { kind: 'uups' });
    await oracleRegistry.waitForDeployment();
    const oracleRegistryAddress = await oracleRegistry.getAddress();
    console.log("   -> OracleRegistry Proxy deployed at:", oracleRegistryAddress);
    await delay(4000);

    // --- 4. Deploy QuantumTaskBuffer (UUPS Upgradeable) ---
    console.log("🔸 Deploying QuantumTaskBuffer (UUPS Proxy)...");
    const QuantumTaskBuffer = await ethers.getContractFactory("QuantumTaskBuffer");
    const taskBuffer = await upgrades.deployProxy(QuantumTaskBuffer, [
        daimTokenAddress,
        registryAddress,
        treasuryAddress,
        deployer.address
    ], { kind: 'uups' });
    await taskBuffer.waitForDeployment();
    const taskBufferAddress = await taskBuffer.getAddress();
    console.log("✅ QuantumTaskBuffer Proxy deployed at:", taskBufferAddress);
    await delay(4000);

    // --- 5. Wiring Contracts & Verification ---
    console.log("🔌 Wiring Contracts...");

    // Grant MINTER_ROLE to TaskBuffer (so it can mint rewards)
    if (daimToken) {
        // @ts-ignore
        const MINTER_ROLE = await daimToken.MINTER_ROLE();
        // @ts-ignore
        const hasRole = await daimToken.hasRole(MINTER_ROLE, taskBufferAddress);
        if (!hasRole) {
            console.log("   -> Granting MINTER_ROLE to TaskBuffer...");
            // @ts-ignore
            const tx = await daimToken.grantRole(MINTER_ROLE, taskBufferAddress);
            await tx.wait(1);
            await delay(3000);
        }
    }

    // Grant ORACLE_ROLE in Registry to TaskBuffer (so TaskBuffer can update reputation)
    // @ts-ignore
    const ORACLE_ROLE = await agentRegistry.ORACLE_ROLE();
    // @ts-ignore
    const hasOracleRole = await agentRegistry.hasRole(ORACLE_ROLE, taskBufferAddress);
    if (!hasOracleRole) {
        console.log("   -> Granting ORACLE_ROLE (Registry) to TaskBuffer...");
        // @ts-ignore
        const tx = await agentRegistry.grantRole(ORACLE_ROLE, taskBufferAddress);
        await tx.wait(1);
        await delay(3000);
    }

    // Set OracleRegistry in TaskBuffer and grant roles
    console.log("   -> Wiring OracleRegistry to TaskBuffer...");
    // @ts-ignore
    const tx1 = await taskBuffer.setOracleRegistry(oracleRegistryAddress);
    await tx1.wait(1);
    await delay(3000);

    // @ts-ignore
    const TASK_BUFFER_ROLE = await oracleRegistry.TASK_BUFFER_ROLE();
    // @ts-ignore
    const hasTaskBufferRole = await oracleRegistry.hasRole(TASK_BUFFER_ROLE, taskBufferAddress);
    if (!hasTaskBufferRole) {
        console.log("   -> Granting TASK_BUFFER_ROLE to TaskBuffer...");
        // @ts-ignore
        const tx2 = await oracleRegistry.grantRole(TASK_BUFFER_ROLE, taskBufferAddress);
        await tx2.wait(1);
        await delay(3000);
    }

    console.log("🎉 Deployment & Wiring Complete!");
    console.log("----------------------------------------------------");
    console.log("Contract Addresses for Verification:");
    console.log("DAIM Token: ", daimTokenAddress);
    console.log("AgentRegistry (Proxy): ", registryAddress);
    console.log("OracleRegistry (Proxy): ", oracleRegistryAddress);
    console.log("QuantumTaskBuffer (Proxy): ", taskBufferAddress);
    console.log("----------------------------------------------------");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
