import { ethers } from "hardhat";

async function main() {
    console.log("\n===================================================");
    console.log("🏗️  PART 2: SYSTEM DEPLOYMENT (EPHEMERAL) 🏗️");
    console.log("===================================================\n");

    // Check Inputs
    const DAIM_TOKEN_ADDRESS = process.env.DAIM_TOKEN_ADDRESS;
    if (!DAIM_TOKEN_ADDRESS || !ethers.isAddress(DAIM_TOKEN_ADDRESS)) {
        throw new Error("❌ MISSING or INVALID 'DAIM_TOKEN_ADDRESS' in .env or environment variables.");
    }
    console.log("Target Token:", DAIM_TOKEN_ADDRESS);

    // 1. Generate Ephemeral Wallet
    const randomWallet = ethers.Wallet.createRandom();
    const ephemeralAddress = randomWallet.address;
    const provider = ethers.provider;
    const deployer = randomWallet.connect(provider);

    console.log("\n1️⃣  EPHEMERAL WALLET GENERATED");
    console.log("   Address:     ", ephemeralAddress);
    console.log("   Private Key:  [HIDDEN]");

    // 2. Wait for Funds
    console.log("\n2️⃣  WAITING FOR GAS");
    console.log("   Action: Send approx 0.005 ETH to the address above.");
    console.log("   Status: Waiting for balance > 0.003 ETH...");

    let balance = await provider.getBalance(ephemeralAddress);
    const REQUIRED_BALANCE = ethers.parseEther("0.003");

    process.stdout.write("   Polling");
    while (balance < REQUIRED_BALANCE) {
        await new Promise(r => setTimeout(r, 5000));
        balance = await provider.getBalance(ephemeralAddress);
        process.stdout.write(".");
    }
    console.log("\n\n✅ FUNDS RECEIVED:", ethers.formatEther(balance), "ETH");

    // Config
    const TREASURY_ADDRESS = process.env.TREASURY_ADDRESS || "0xED314144920B7b0cC148947c4B458D220010aC90";
    console.log("   Target Treasury:", TREASURY_ADDRESS);

    // 3. Deploy System
    console.log("\n🚀 DEPLOYING CORE SYSTEM...");

    // A. Oracle
    console.log("   [1/5] AdminPriceOracle...");
    const OracleFactory = await ethers.getContractFactory("AdminPriceOracle", deployer);
    const oracle = await OracleFactory.deploy();
    await oracle.waitForDeployment();
    const oracleAddr = await oracle.getAddress();

    // B. Treasury
    console.log("   [2/5] TreasuryController (3600s)...");
    const TreasuryFactory = await ethers.getContractFactory("TreasuryController", deployer);
    const treasury = await TreasuryFactory.deploy(
        deployer.address,
        ethers.parseEther("50"),
        3600
    );
    await treasury.waitForDeployment();
    const treasuryAddr = await treasury.getAddress();

    // C. Verifier
    console.log("   [3/5] AllowlistVerifier...");
    const VerifierFactory = await ethers.getContractFactory("AllowlistVerifier", deployer);
    const verifier = await VerifierFactory.deploy();
    await verifier.waitForDeployment();
    const verifierAddr = await verifier.getAddress();

    // D. Registry
    console.log("   [4/5] AgentRegistry...");
    const RegistryFactory = await ethers.getContractFactory("AgentRegistry", deployer);
    const registry = await RegistryFactory.deploy(
        DAIM_TOKEN_ADDRESS,
        oracleAddr,
        treasuryAddr,
        verifierAddr,
        deployer.address
    );
    await registry.waitForDeployment();
    const registryAddr = await registry.getAddress();

    // E. Modules
    console.log("   [5/5] Modules...");
    const SessionKeyFactory = await ethers.getContractFactory("SessionKeyModule", deployer);
    const sessionKey = await SessionKeyFactory.deploy(registryAddr);
    await sessionKey.waitForDeployment();

    const CircuitBreakerFactory = await ethers.getContractFactory("CircuitBreakerModule", deployer);
    const circuitBreaker = await CircuitBreakerFactory.deploy(registryAddr);
    await circuitBreaker.waitForDeployment();

    // 4. Handover
    console.log("\n🔒 EXECUTING SYSTEM HANDOVER...");

    console.log(`   [Oracle] Transferring Ownership...`);
    await (await oracle.transferOwnership(TREASURY_ADDRESS)).wait();

    console.log(`   [Treasury] Transferring Ownership...`);
    await (await treasury.transferOwnership(TREASURY_ADDRESS)).wait();

    console.log(`   [Verifier] Transferring Ownership...`);
    await (await verifier.transferOwnership(TREASURY_ADDRESS)).wait();

    console.log(`   [Registry] Transferring Access Control...`);
    const DEFAULT_ADMIN_ROLE = await registry.DEFAULT_ADMIN_ROLE();
    await (await registry.grantRole(DEFAULT_ADMIN_ROLE, TREASURY_ADDRESS)).wait();
    await (await registry.renounceRole(DEFAULT_ADMIN_ROLE, deployer.address)).wait();

    console.log("\n-----------------------------------------");
    console.log("✅ PART 2 COMPLETE");
    console.log("-----------------------------------------");
    console.log("Contracts Deployed & Transferred:");
    console.log("Token:   ", DAIM_TOKEN_ADDRESS);
    console.log("Oracle:  ", oracleAddr);
    console.log("Treasury:", treasuryAddr);
    console.log("Verifier:", verifierAddr);
    console.log("Registry:", registryAddr);
    console.log("SessionKey:", await sessionKey.getAddress());
    console.log("CircuitBreaker:", await circuitBreaker.getAddress());
    console.log("-----------------------------------------");
    console.log("Ephemeral Wallet Abandoned.");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
