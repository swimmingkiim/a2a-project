import { ethers, upgrades } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
    console.log("🚀 Starting Genesis Deployment...");

    const [deployer] = await ethers.getSigners();
    console.log("Deployer:", deployer.address);

    // --- 1. Generate 5 Genesis Wallets ---
    console.log("\n🔐 Generating 5 Genesis Guardian Keys...");
    const genesisWallets = [];
    const genesisAddresses = [];

    // Create directory for keys if not exists
    const keyDir = path.join(__dirname, "../../genesis-keys");
    if (!fs.existsSync(keyDir)) {
        fs.mkdirSync(keyDir, { recursive: true });
    }

    for (let i = 1; i <= 5; i++) {
        const wallet = ethers.Wallet.createRandom();
        genesisWallets.push(wallet);
        genesisAddresses.push(wallet.address);

        const keyData = {
            address: wallet.address,
            privateKey: wallet.privateKey,
            mnemonic: wallet.mnemonic?.phrase
        };

        fs.writeFileSync(
            path.join(keyDir, `genesis_key_${i}.json`),
            JSON.stringify(keyData, null, 2)
        );
        console.log(`   - Key ${i} saved to genesis-keys/genesis_key_${i}.json (${wallet.address})`);
    }

    // --- 2. Deploy Mocks ---
    console.log("\n🛠️ Deploying Mocks...");
    const MockPriceFeed = await ethers.getContractFactory("MockPriceFeed");
    const mockPriceFeed = await MockPriceFeed.deploy(200000000000, 8); // $2000, 8 decimals
    await mockPriceFeed.waitForDeployment();
    console.log("   - MockPriceFeed deployed to:", await mockPriceFeed.getAddress());

    // Deploy Mock Verifier
    const MockVerifier = await ethers.getContractFactory("contracts/mocks/MockVerifier.sol:MockVerifier");
    const mockVerifier = await MockVerifier.deploy();
    await mockVerifier.waitForDeployment();
    console.log("   - MockVerifier deployed to:", await mockVerifier.getAddress());

    // --- 3. Deploy Core Contracts ---
    console.log("\n🏗️ Deploying Core Contracts...");

    // DaimToken
    const DaimToken = await ethers.getContractFactory("DaimToken");
    const daimToken = await upgrades.deployProxy(DaimToken, [deployer.address], { kind: 'uups' });
    await daimToken.waitForDeployment();
    const daimTokenAddress = await daimToken.getAddress();
    console.log("   - DaimToken deployed to:", daimTokenAddress);

    // AgentRegistry
    // initialize(daimToken, priceFeed, treasury, verifier, admin)
    const AgentRegistry = await ethers.getContractFactory("AgentRegistry");
    const agentRegistry = await upgrades.deployProxy(AgentRegistry, [
        daimTokenAddress,
        await mockPriceFeed.getAddress(),
        deployer.address, // Treasury is deployer for genesis
        await mockVerifier.getAddress(),
        deployer.address
    ], { kind: 'uups' });
    await agentRegistry.waitForDeployment();
    const agentRegistryAddress = await agentRegistry.getAddress();
    console.log("   - AgentRegistry deployed to:", agentRegistryAddress);

    // QuantumTaskBuffer
    // initialize(daimToken, registry, treasury, admin)
    const QuantumTaskBuffer = await ethers.getContractFactory("QuantumTaskBuffer");
    const quantumTaskBuffer = await upgrades.deployProxy(QuantumTaskBuffer, [
        daimTokenAddress,
        agentRegistryAddress,
        deployer.address,
        deployer.address
    ], { kind: 'uups' });
    await quantumTaskBuffer.waitForDeployment();
    const quantumTaskBufferAddress = await quantumTaskBuffer.getAddress();
    console.log("   - QuantumTaskBuffer deployed to:", quantumTaskBufferAddress);

    // --- 4. Deploy Governance Contracts ---
    console.log("\n🏛️ Deploying Governance Contracts...");

    // EmergencyCouncil
    // initialize(admin, registry, guardians)
    const EmergencyCouncil = await ethers.getContractFactory("EmergencyCouncil");
    const emergencyCouncil = await upgrades.deployProxy(EmergencyCouncil, [
        deployer.address,
        agentRegistryAddress,
        genesisAddresses // Pass the array of 5 addresses
    ], { kind: 'uups' });
    await emergencyCouncil.waitForDeployment();
    const emergencyCouncilAddress = await emergencyCouncil.getAddress();
    console.log("   - EmergencyCouncil deployed to:", emergencyCouncilAddress);

    // DeadMansSwitch
    // initialize(admin, emergencyCouncil)
    const DeadMansSwitch = await ethers.getContractFactory("DeadMansSwitch");
    const deadMansSwitch = await upgrades.deployProxy(DeadMansSwitch, [
        deployer.address,
        emergencyCouncilAddress
    ], { kind: 'uups' });
    await deadMansSwitch.waitForDeployment();
    const deadMansSwitchAddress = await deadMansSwitch.getAddress();
    console.log("   - DeadMansSwitch deployed to:", deadMansSwitchAddress);


    // --- 5. Wire Permissions ---
    console.log("\n🔌 Wiring Permissions...");

    // Roles
    const DEFAULT_ADMIN_ROLE = await daimToken.DEFAULT_ADMIN_ROLE();
    const MINTER_ROLE = await daimToken.MINTER_ROLE();
    const ORACLE_ROLE = await agentRegistry.ORACLE_ROLE();
    const COUNCIL_FORMER_ROLE = await emergencyCouncil.COUNCIL_FORMER_ROLE();

    // 1. QuantumTaskBuffer needs MINTER on DaimToken
    await daimToken.grantRole(MINTER_ROLE, quantumTaskBufferAddress);
    console.log("   - Granted MINTER_ROLE to QuantumTaskBuffer");

    // 2. QuantumTaskBuffer needs ORACLE_ROLE on AgentRegistry (to record observations)
    await agentRegistry.grantRole(ORACLE_ROLE, quantumTaskBufferAddress);
    console.log("   - Granted ORACLE_ROLE to QuantumTaskBuffer");

    // 3. DeadMansSwitch needs COUNCIL_FORMER_ROLE on EmergencyCouncil
    await emergencyCouncil.grantRole(COUNCIL_FORMER_ROLE, deadMansSwitchAddress);
    console.log("   - Granted COUNCIL_FORMER_ROLE to DeadMansSwitch");

    // 4. DeadMansSwitch needs DEFAULT_ADMIN_ROLE on all upgradable contracts to transfer them later
    // Contracts: DaimToken, AgentRegistry, QuantumTaskBuffer, EmergencyCouncil
    const targets = [daimToken, agentRegistry, quantumTaskBuffer, emergencyCouncil];

    for (const target of targets) {
        const addr = await target.getAddress();
        await target.grantRole(DEFAULT_ADMIN_ROLE, deadMansSwitchAddress);
        await deadMansSwitch.addTargetContract(addr);
        console.log(`   - Granted DEFAULT_ADMIN_ROLE to DeadMansSwitch on ${addr}`);
    }


    // --- 6. Initial Ecosystem Setup ---
    console.log("\n🌱 Bootstrapping Ecosystem...");

    // 1. Mint 1,000,000,000 DAIM
    const initialSupply = ethers.parseEther("1000000000");
    await daimToken.mint(deployer.address, initialSupply);
    console.log("   - Minted 1,000,000,000 DAIM to Deployer");

    // 2. Register Genesis Wallets as Agents (Force Registration)
    // We need to fund them with ETH for gas, and DAIM for staking
    // Stake amount logic:
    // Registry: costUSD = BASE_STAKE_USD * (Units^2)
    // BASE_STAKE_USD = $10. Units = 1 (let's say). Cost = $10.
    // Price = $2000. 
    // DAIM needed = ($10 / $2000) = 0.005 DAIM? 
    // Wait, getDaimAmountFromUSD: (usdAmount * 1e18) / price.
    // $10 * 1e8 (USD decimals) = 10 * 1e8.
    // Price = 2000 * 1e8.
    // (10 * 1e8 * 1e18) / (2000 * 1e8) = 10e18 / 2000 = 1/200 * 1e18 = 0.005 * 1e18 = 5 * 1e15.

    // Let's give them 100 DAIM each to be safe and let them register with 10 units.
    // 10 units = $1000 cost.
    // $1000 / $2000 = 0.5 DAIM.

    const stakeAmount = ethers.parseEther("10"); // 10 DAIM each
    const ethFund = ethers.parseEther("0.1"); // 0.1 ETH for gas

    for (let i = 0; i < 5; i++) {
        const wallet = genesisWallets[i];
        const signer = wallet.connect(ethers.provider); // Connect to provider!

        console.log(`   Processing Genesis Agent ${i + 1} (${wallet.address})...`);

        // Fund ETH
        await deployer.sendTransaction({
            to: wallet.address,
            value: ethFund
        });

        // Fund DAIM
        await daimToken.transfer(wallet.address, stakeAmount);

        // Approve Registry
        const daimWithSigner = daimToken.connect(signer);
        await daimWithSigner.approve(agentRegistryAddress, stakeAmount);

        // Register
        // register(metadataUrl, resourceUnits, vcProof)
        const units = 5; // Moderate units
        const registryWithSigner = agentRegistry.connect(signer);

        // Dummy proof
        const proof = ethers.toUtf8Bytes("genesis_proof");

        await registryWithSigner.register(
            `https://a2a.network/genesis/${i + 1}`,
            units,
            proof
        );
        console.log(`     - Registered as Agent (Units: ${units})`);
    }

    console.log("\n✅ Genesis Deployment Complete!");
    console.log("---------------------------------------------------");
    console.log("DaimToken:", daimTokenAddress);
    console.log("AgentRegistry:", agentRegistryAddress);
    console.log("EmergencyCouncil:", emergencyCouncilAddress);
    console.log("DeadMansSwitch:", deadMansSwitchAddress);
    console.log("Genesis Keys Location:", keyDir);
    console.log("---------------------------------------------------");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
