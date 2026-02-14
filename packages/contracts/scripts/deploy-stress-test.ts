import { ethers } from "hardhat";

async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("--- Deploying Stress Test Environment ---");
    console.log("Deployer:", deployer.address);

    const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
    const DELAY_MS = 10000; // Safe delay for testnet

    // 1. Deploy Mock Token
    console.log("\n1. Deploying DaimToken...");
    const TokenFactory = await ethers.getContractFactory("DaimToken");
    const daimToken = await TokenFactory.deploy("Test Token", "TEST", deployer.address);
    await daimToken.waitForDeployment();
    console.log("   -> Token:", await daimToken.getAddress());
    await sleep(DELAY_MS);

    // 2. Deploy Mock Oracle (Start at $50)
    console.log("\n2. Deploying Mock Oracle...");
    const OracleFactory = await ethers.getContractFactory("MockV3Aggregator");
    const mockOracle = await OracleFactory.deploy(8, 5000000000); // $50
    await mockOracle.waitForDeployment();
    console.log("   -> Oracle:", await mockOracle.getAddress());
    await sleep(DELAY_MS);

    // 3. Deploy Treasury (Short Epoch: 60 seconds)
    console.log("\n3. Deploying TreasuryController (60s Epoch)...");
    const TreasuryFactory = await ethers.getContractFactory("TreasuryController");
    const treasury = await TreasuryFactory.deploy(
        deployer.address,
        ethers.parseEther("50"), // Target $50
        60 // 60 Seconds Epoch
    );
    await treasury.waitForDeployment();
    console.log("   -> Treasury:", await treasury.getAddress());
    await sleep(DELAY_MS);

    // 4. Deploy Allowlist Verifier
    console.log("\n4. Deploying AllowlistVerifier...");
    const VerifierFactory = await ethers.getContractFactory("AllowlistVerifier");
    const verifier = await VerifierFactory.deploy(); // Ownable by deployer
    await verifier.waitForDeployment();
    console.log("   -> Verifier:", await verifier.getAddress());
    await sleep(DELAY_MS);

    // 5. Deploy Registry
    console.log("\n5. Deploying Registry...");
    const RegistryFactory = await ethers.getContractFactory("AgentRegistry");
    const registry = await RegistryFactory.deploy(
        await daimToken.getAddress(),
        await mockOracle.getAddress(),
        await treasury.getAddress(),
        await verifier.getAddress(),
        deployer.address
    );
    await registry.waitForDeployment();
    console.log("   -> Registry:", await registry.getAddress());
    await sleep(DELAY_MS);

    // 6. Whitelist Deployer for testing
    console.log("\n6. Whitelisting Deployer...");
    const txAllow = await verifier.setAllowed(deployer.address, true);
    await txAllow.wait();
    console.log("   -> Deployer whitelisted.");
    await sleep(DELAY_MS);

    // 7. Mint Tokens for Testing
    console.log("\n7. Minting 10,000 DAIM...");
    const txMint = await daimToken.mint(deployer.address, ethers.parseEther("10000"));
    await txMint.wait();
    await sleep(DELAY_MS);

    // 8. Approve Registry
    console.log("\n8. Approving Registry...");
    const txApprove = await daimToken.approve(await registry.getAddress(), ethers.MaxUint256);
    await txApprove.wait();

    console.log("\n✅ Stress Test Env Ready!");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
