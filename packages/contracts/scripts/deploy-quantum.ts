import { ethers, run } from "hardhat";

async function main() {
    console.log("🚀 Starting Quantum A2A Protocol Deployment...");

    const [deployer] = await ethers.getSigners();
    console.log("🔹 Deployer:", deployer.address);

    // --- 1. Environment / Mock Setup ---
    // If addresses are provided in env, use them. Otherwise deploy Mocks/Fresh.

    let daimTokenAddress = process.env.DAIM_TOKEN_ADDRESS;
    let oracleAddress = process.env.CHAINLINK_ORACLE_ADDRESS;
    let verifierAddress = process.env.VERIFIER_ADDRESS;
    let treasuryAddress = process.env.TREASURY_ADDRESS || deployer.address; // Default to deployer for logic check

    let daimToken;
    let registry;
    let taskBuffer;

    // Deploy Mocks if needed (Localhost or Testnet without config)
    if (!oracleAddress) {
        console.log("🔸 Deploying MockOracle...");
        const MockOracle = await ethers.getContractFactory("MockV3Aggregator");
        const mockOracle = await MockOracle.deploy(8, 1000000000); // $10.00
        await mockOracle.waitForDeployment();
        oracleAddress = await mockOracle.getAddress();
        console.log("   -> MockOracle deployed at:", oracleAddress);
    }

    if (!verifierAddress) {
        console.log("🔸 Deploying MockVerifier...");
        const MockVerifier = await ethers.getContractFactory("MockVerifier");
        const mockVerifier = await MockVerifier.deploy();
        await mockVerifier.waitForDeployment();
        verifierAddress = await mockVerifier.getAddress();
        console.log("   -> MockVerifier deployed at:", verifierAddress);
    }

    // --- 2. Deploy Core Contracts (if not existing) ---
    // Note: We force redeploy of ComputeToken and AgentRegistry because we modified source code 
    // and need the new functions (mintWithEudaimonia, recordObservation).
    // Using existing address with changed code would fail or define undefined behavior on interface call.
    if (true) {
        console.log("🔸 Deploying DaimToken...");
        const DaimToken = await ethers.getContractFactory("DaimToken");
        daimToken = await DaimToken.deploy("Eudaimon", "DAIM", deployer.address);
        await daimToken.waitForDeployment();
        daimTokenAddress = await daimToken.getAddress();
        console.log("   -> DaimToken deployed at:", daimTokenAddress);

        console.log("🔸 Deploying AgentRegistry (New Logic)...");
        const AgentRegistry = await ethers.getContractFactory("AgentRegistry");
        registry = await AgentRegistry.deploy(
            daimTokenAddress,
            oracleAddress,
            treasuryAddress,
            verifierAddress,
            deployer.address
        );
        await registry.waitForDeployment();
        const registryAddress = await registry.getAddress();
        console.log("   -> AgentRegistry deployed at:", registryAddress);
    } else {
        // Attach existings (Not recommended for this update step)
        // daimToken = await ethers.getContractAt("DaimToken", daimTokenAddress);
    }

    // --- 3. Deploy QuantumTaskBuffer ---
    console.log("🔸 Deploying QuantumTaskBuffer...");
    const QuantumTaskBuffer = await ethers.getContractFactory("QuantumTaskBuffer");
    const registryAddress = await registry.getAddress();

    taskBuffer = await QuantumTaskBuffer.deploy(
        daimTokenAddress,
        registryAddress,
        treasuryAddress,
        deployer.address
    );
    await taskBuffer.waitForDeployment();
    const taskBufferAddress = await taskBuffer.getAddress();
    console.log("✅ QuantumTaskBuffer deployed at:", taskBufferAddress);

    // --- 4. Setup Roles (Wiring) ---
    console.log("🔌 Wiring Contracts...");

    // A. Grant MINTER_ROLE to QuantumTaskBuffer in ComputeToken
    const MINTER_ROLE = await daimToken.MINTER_ROLE();
    const tx1 = await daimToken.grantRole(MINTER_ROLE, taskBufferAddress);
    await tx1.wait();
    console.log("   -> Granted MINTER_ROLE to TaskBuffer");

    // B. Grant ORACLE_ROLE to QuantumTaskBuffer in AgentRegistry
    // Note: The registry needs to allow the Buffer to call `recordObservation`. 
    // Wait, AgentRegistry.sol has `onlyRole(ORACLE_ROLE)` on `recordObservation`.
    // So we need to grant ORACLE_ROLE to the Buffer.
    const REGISTRY_ORACLE_ROLE = await registry.ORACLE_ROLE();
    const tx2 = await registry.grantRole(REGISTRY_ORACLE_ROLE, taskBufferAddress);
    await tx2.wait();
    console.log("   -> Granted ORACLE_ROLE (Registry) to TaskBuffer");

    // C. Grant ORACLE_ROLE to Admin in QuantumTaskBuffer (so Admin can finalize tasks for testing)
    // Already done in constructor, but let's verify or add another oracle if needed.

    console.log("🎉 Deployment & Wiring Complete!");

    // --- 5. Verification Hint ---
    console.log("\nTo verify manually:");
    console.log(`npx hardhat verify --network base_mainnet ${taskBufferAddress} ${daimTokenAddress} ${registryAddress} ${treasuryAddress} ${deployer.address}`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
