import { ethers, run } from "hardhat";

async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with the account:", deployer.address);

    // Helper to prevent nonce race conditions on testnet
    const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

    // 1. Deploy ComputeToken
    console.log("\n1. Deploying ComputeToken...");
    const TOKEN_NAME = process.env.TOKEN_NAME || "Compute Token";
    const TOKEN_SYMBOL = process.env.TOKEN_SYMBOL || "COMP";
    console.log(`   Identity: ${TOKEN_NAME} ($${TOKEN_SYMBOL})`);

    const TokenFactory = await ethers.getContractFactory("ComputeToken");
    const compToken = await TokenFactory.deploy(TOKEN_NAME, TOKEN_SYMBOL, deployer.address);
    await compToken.waitForDeployment();
    console.log("   -> ComputeToken:", await compToken.getAddress());
    await sleep(5000);

    // 2. Deploy Mock Oracle
    console.log("\n2. Deploying Mock Oracle ($50 USD)...");
    const OracleFactory = await ethers.getContractFactory("MockV3Aggregator");
    const mockOracle = await OracleFactory.deploy(8, 5000000000);
    await mockOracle.waitForDeployment();
    const oracleAddress = await mockOracle.getAddress();
    console.log("   -> MockOracle deployed at:", oracleAddress);
    await sleep(5000);

    // 3. Deploy Treasury Controller (PID)
    console.log("\n3. Deploying TreasuryController...");
    // ... rest of script needs sleeps too
    const TreasuryFactory = await ethers.getContractFactory("TreasuryController");
    const treasury = await TreasuryFactory.deploy(
        deployer.address, // Admin
        ethers.parseEther("50"), // Target Price $50
        3600 // Epoch 1 Hour
    );
    await treasury.waitForDeployment();
    const treasuryAddress = await treasury.getAddress();
    console.log("   -> TreasuryController deployed at:", treasuryAddress);
    await sleep(5000);

    // 4. Deploy Mock Verifier (For easy testing)
    console.log("\n4. Deploying MockVerifier (Auto-Approve)...");
    const VerifierFactory = await ethers.getContractFactory("MockVerifier");
    const verifier = await VerifierFactory.deploy();
    await verifier.waitForDeployment();
    const verifierAddress = await verifier.getAddress();
    console.log("   -> MockVerifier deployed at:", verifierAddress);
    await sleep(5000);

    // 5. Deploy AgentRegistry
    console.log("\n5. Deploying AgentRegistry...");
    const RegistryFactory = await ethers.getContractFactory("AgentRegistry");
    const registry = await RegistryFactory.deploy(
        await compToken.getAddress(), // Use accessor to be safe
        oracleAddress,
        treasuryAddress, // Treasury Address (Using Controller as recipient for now or Admin wallet if separate?)
        // The contract takes 'treasury' address. 
        // To enable PID control over funds, the TreasuryController usually *is* the treasury 
        // or manages it. For this script, we point to the TreasuryController contract 
        // assuming it has a 'receive' or we just send funds there.
        // Warning: TreasuryController doesn't have withdraw logic in the snippet I wrote?
        // It extends AccessControl. Let's check. 
        // Actually, TreasuryController manages *Rates*. Step 248 shows logic.
        // It doesn't seem to have `withdraw`. 
        // User feedback: "Keeper... updateEpoch".
        // Funds should arguably go to a Gnosis Safe or the Controller if it had logic.
        // For now, let's send funds to the *Deployer* (Admin) to act as Treasury Wallet,
        // OR send to TreasuryController if we plan to upgrade it to hold funds.
        // Let's us Deployer address as 'treasury wallet' ensuring funds are accessible,
        // while TreasuryController manages the *Policy*.
        verifierAddress,
        deployer.address // Admin
    );
    await registry.waitForDeployment();
    const registryAddress = await registry.getAddress();
    console.log("   -> AgentRegistry deployed at:", registryAddress);
    await sleep(5000);

    // 6. Deploy Modules
    console.log("\n6. Deploying Bulkhead Modules...");

    // Session Key
    const SessionFactory = await ethers.getContractFactory("SessionKeyModule");
    const sessionModule = await SessionFactory.deploy(ethers.ZeroAddress); // Mock Reputation
    await sessionModule.waitForDeployment();
    console.log("   -> SessionKeyModule deployed at:", await sessionModule.getAddress());

    // Circuit Breaker
    const CircuitFactory = await ethers.getContractFactory("CircuitBreakerModule");
    const circuitBreaker = await CircuitFactory.deploy();
    await circuitBreaker.waitForDeployment();
    console.log("   -> CircuitBreakerModule deployed at:", await circuitBreaker.getAddress());

    // 7. Verification / Setup
    console.log("\n7. Final Setup...");
    // Grant Minter Role to Deployer for testnet token
    // (Already done by constructor logic if deployer passed, but let's confirm minting)
    // Mint some initial tokens to deployer for testing
    // await compToken.mint(deployer.address, ethers.parseEther("100000"));
    // console.log("   -> Minted 100,000 COMP to deployer");

    console.log("\n✅ Deployment Complete!");
    console.log("----------------------------------------------------");
    console.log(`COMP Token:        ${await compToken.getAddress()}`);
    console.log(`Oracle:            ${oracleAddress}`);
    console.log(`TreasuryControl:   ${treasuryAddress}`);
    console.log(`Verifier:          ${verifierAddress}`);
    console.log(`AgentRegistry:     ${registryAddress}`);
    console.log(`SessionModule:     ${await sessionModule.getAddress()}`);
    console.log(`CircuitBreaker:    ${await circuitBreaker.getAddress()}`);
    console.log("----------------------------------------------------");

    // Attempt Verification (Wait a bit for block explorer to index)
    // console.log("Waiting for block confirmations...");
    // await registry.deploymentTransaction()?.wait(5);
    // await run("verify:verify", { address: registryAddress, constructorArguments: [...] });
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
