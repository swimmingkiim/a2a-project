
import { ethers, upgrades } from "hardhat";
import dotenv from "dotenv";

dotenv.config();

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
    }

    if (!mockVerifierAddress) {
        console.log("🔸 Deploying MockVerifier...");
        const MockVerifier = await ethers.getContractFactory("MockVerifier");
        const mockVerifier = await MockVerifier.deploy();
        await mockVerifier.waitForDeployment();
        mockVerifierAddress = await mockVerifier.getAddress();
        console.log("   -> MockVerifier deployed at:", mockVerifierAddress);
    }

    // --- 2. Deploy DaimToken (Not Upgradeable) ---
    let daimToken;
    if (!daimTokenAddress) {
        console.log("🔸 Deploying DaimToken...");
        const DaimToken = await ethers.getContractFactory("DaimToken");
        daimToken = await DaimToken.deploy("Eudaimon", "DAIM", deployer.address);
        await daimToken.waitForDeployment();
        daimTokenAddress = await daimToken.getAddress();
        console.log("   -> DaimToken deployed at:", daimTokenAddress);
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
            await daimToken.grantRole(MINTER_ROLE, taskBufferAddress);
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
        await agentRegistry.grantRole(ORACLE_ROLE, taskBufferAddress);
    }

    console.log("🎉 Deployment & Wiring Complete!");
    console.log("----------------------------------------------------");
    console.log("Contract Addresses for Verification:");
    console.log("DAIM Token: ", daimTokenAddress);
    console.log("AgentRegistry (Proxy): ", registryAddress);
    console.log("QuantumTaskBuffer (Proxy): ", taskBufferAddress);
    console.log("----------------------------------------------------");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});

