import { ethers, upgrades } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
    console.log("🚀 Starting Genesis Deployment...");

    const [deployer] = await ethers.getSigners();
    console.log("Deployer:", deployer.address);

    // Create directory for keys if not exists
    const keyDir = path.join(__dirname, "../../genesis-keys");
    if (!fs.existsSync(keyDir)) {
        fs.mkdirSync(keyDir, { recursive: true });
    }

    // --- 1. Security & Wallet Generation (The "Vault") ---
    console.log("\n🔐 Generating Secure Ecosystem Wallets...");

    // Helper to generate and save key
    const generateKey = (name: string, note: string) => {
        const wallet = ethers.Wallet.createRandom();
        const keyData = {
            address: wallet.address,
            privateKey: wallet.privateKey,
            mnemonic: wallet.mnemonic?.phrase,
            note: note
        };
        fs.writeFileSync(path.join(keyDir, `${name}_KEY_${Date.now()}.json`), JSON.stringify(keyData, null, 2));
        console.log(`   - Generated ${name}: ${wallet.address}`);
        return wallet;
    };

    // 1.1 Genesis Guardians (5 Keys)
    const genesisWallets = [];
    const genesisAddresses = [];
    for (let i = 1; i <= 5; i++) {
        const w = generateKey(`GUARDIAN_${i}`, "Emergency Council Member");
        genesisWallets.push(w);
        genesisAddresses.push(w.address);
    }

    // 1.2 Ecosystem Wallets (4 Keys)
    // - Treasury: Receives protocol fees (taxes, slashing).
    // - Liquidity: Funds for Uniswap/CEX listings.
    // - Ecosystem: Grants, Airdrops, Marketing.
    // - Team: Dev fund, vesting.
    const treasuryWallet = generateKey("TREASURY", "Receives Taxes & Fees. Keep Safe.");
    const liquidityWallet = generateKey("LIQUIDITY", "Funds for DEX/CEX Listings.");
    const ecosystemWallet = generateKey("ECOSYSTEM", "Grants & Community Incentives.");
    const teamWallet = generateKey("TEAM", "Core Team & Development Fund.");

    // 1.3 Final Admin (The Master Key)
    let finalAdmin = process.env.FINAL_ADMIN_ADDRESS;
    let finalAdminWallet;

    if (!finalAdmin) {
        finalAdminWallet = generateKey("FINAL_ADMIN", "MASTER KEY. FULL CONTROL. OFFLINE BACKUP REQUIRED.");
        finalAdmin = finalAdminWallet.address;
    } else {
        console.log(`   - Using Provided Final Admin: ${finalAdmin}`);
    }

    // --- 2. Deployment (Mocks) ---
    console.log("\n🛠️ Deploying Mocks...");

    // MockPriceFeed
    const MockPriceFeed = await ethers.getContractFactory("MockPriceFeed");
    const mockPriceFeed = await MockPriceFeed.deploy(200000000000, 8); // $2000, 8 decimals
    await mockPriceFeed.waitForDeployment();
    await mockPriceFeed.deploymentTransaction()?.wait(2);
    console.log("   - MockPriceFeed deployed to:", await mockPriceFeed.getAddress());

    // Deploy Mock Verifier
    const MockVerifier = await ethers.getContractFactory("contracts/mocks/MockVerifier.sol:MockVerifier");
    const mockVerifier = await MockVerifier.deploy();
    await mockVerifier.waitForDeployment();
    await mockVerifier.deploymentTransaction()?.wait(2);
    console.log("   - MockVerifier deployed to:", await mockVerifier.getAddress());


    // --- 3. Deploy Core Contracts ---
    console.log("\n🏗️ Deploying Core Contracts...");

    // DaimToken
    const DaimToken = await ethers.getContractFactory("DaimToken");
    const daimToken = await upgrades.deployProxy(DaimToken, [deployer.address], { kind: 'uups' });
    await daimToken.waitForDeployment();
    await daimToken.deploymentTransaction()?.wait(2);
    const daimTokenAddress = await daimToken.getAddress();
    console.log("   - DaimToken deployed to:", daimTokenAddress);

    // AgentRegistry
    // initialize(daimToken, priceFeed, treasury, verifier, admin)
    // NOTE: We use the generated 'treasuryWallet.address' here!
    const AgentRegistry = await ethers.getContractFactory("AgentRegistry");
    const agentRegistry = await upgrades.deployProxy(AgentRegistry, [
        daimTokenAddress,
        await mockPriceFeed.getAddress(),
        treasuryWallet.address, // <-- Updated to use generated Treasury
        await mockVerifier.getAddress(),
        deployer.address
    ], { kind: 'uups' });
    await agentRegistry.waitForDeployment();
    await agentRegistry.deploymentTransaction()?.wait(2);
    const agentRegistryAddress = await agentRegistry.getAddress();
    console.log("   - AgentRegistry deployed to:", agentRegistryAddress);

    // QuantumTaskBuffer
    // initialize(daimToken, registry, treasury, admin)
    // NOTE: We use the generated 'treasuryWallet.address' here!
    const QuantumTaskBuffer = await ethers.getContractFactory("QuantumTaskBuffer");
    const quantumTaskBuffer = await upgrades.deployProxy(QuantumTaskBuffer, [
        daimTokenAddress,
        agentRegistryAddress,
        treasuryWallet.address, // <-- Updated to use generated Treasury
        deployer.address
    ], { kind: 'uups' });
    await quantumTaskBuffer.waitForDeployment();
    await quantumTaskBuffer.deploymentTransaction()?.wait(2);
    const quantumTaskBufferAddress = await quantumTaskBuffer.getAddress();
    console.log("   - QuantumTaskBuffer deployed to:", quantumTaskBufferAddress);

    // --- 4. Deploy Governance Contracts ---
    console.log("\n🏛️ Deploying Governance Contracts...");

    // EmergencyCouncil
    const EmergencyCouncil = await ethers.getContractFactory("EmergencyCouncil");
    const emergencyCouncil = await upgrades.deployProxy(EmergencyCouncil, [
        deployer.address,
        agentRegistryAddress,
        genesisAddresses
    ], { kind: 'uups' });
    await emergencyCouncil.waitForDeployment();
    await emergencyCouncil.deploymentTransaction()?.wait(2);
    const emergencyCouncilAddress = await emergencyCouncil.getAddress();
    console.log("   - EmergencyCouncil deployed to:", emergencyCouncilAddress);

    // DeadMansSwitch
    const DeadMansSwitch = await ethers.getContractFactory("DeadMansSwitch");
    const deadMansSwitch = await upgrades.deployProxy(DeadMansSwitch, [
        deployer.address,
        emergencyCouncilAddress
    ], { kind: 'uups' });
    await deadMansSwitch.waitForDeployment();
    await deadMansSwitch.deploymentTransaction()?.wait(2);
    const deadMansSwitchAddress = await deadMansSwitch.getAddress();
    console.log("   - DeadMansSwitch deployed to:", deadMansSwitchAddress);


    // --- 5. Wire Permissions ---
    console.log("\n🔌 Wiring Permissions...");

    const DEFAULT_ADMIN_ROLE = await daimToken.DEFAULT_ADMIN_ROLE();
    const MINTER_ROLE = await daimToken.MINTER_ROLE();
    const ORACLE_ROLE = await agentRegistry.ORACLE_ROLE();
    const COUNCIL_FORMER_ROLE = await emergencyCouncil.COUNCIL_FORMER_ROLE();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const UPGRADER_ROLE = await (agentRegistry as any).UPGRADER_ROLE();

    console.log("   - Granting MINTER_ROLE to QuantumTaskBuffer...");
    let tx = await daimToken.grantRole(MINTER_ROLE, quantumTaskBufferAddress);
    await tx.wait(2); // Wait 2 blocks
    console.log("     -> Confirmed.");

    console.log("   - Granting ORACLE_ROLE to QuantumTaskBuffer...");
    tx = await agentRegistry.grantRole(ORACLE_ROLE, quantumTaskBufferAddress);
    await tx.wait(2);
    console.log("     -> Confirmed.");

    console.log("   - Granting COUNCIL_FORMER_ROLE to DeadMansSwitch...");
    tx = await emergencyCouncil.grantRole(COUNCIL_FORMER_ROLE, deadMansSwitchAddress);
    await tx.wait(2);
    console.log("     -> Confirmed.");

    const targets = [daimToken, agentRegistry, quantumTaskBuffer, emergencyCouncil];
    for (const target of targets) {
        const addr = await target.getAddress();
        console.log(`   - Granting Admin & Wiring DMS for ${addr}...`);
        tx = await target.grantRole(DEFAULT_ADMIN_ROLE, deadMansSwitchAddress);
        await tx.wait(2);

        tx = await deadMansSwitch.addTargetContract(addr);
        await tx.wait(2);
        console.log("     -> Confirmed.");
    }


    // --- 6. Initial Ecosystem Setup ---
    console.log("\n🌱 Bootstrapping Ecosystem & Token Distribution...");

    // 1. Mint Total Supply (1.05 Billion)
    const initialSupply = ethers.parseEther("1050000000"); // 1.05 Billion
    console.log("   - Minting Total Supply...");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    tx = await (daimToken as any).mint(deployer.address, initialSupply);
    await tx.wait(2);
    console.log("     -> Minted 1,050,000,000 DAIM to Deployer (Confirmed).");

    // 2. Distribute Tokens
    const allocations = [
        { name: "Treasury", wallet: treasuryWallet.address, amount: ethers.parseEther("420000000") },
        { name: "Liquidity", wallet: liquidityWallet.address, amount: ethers.parseEther("315000000") },
        { name: "Ecosystem", wallet: ecosystemWallet.address, amount: ethers.parseEther("210000000") },
        { name: "Team", wallet: teamWallet.address, amount: ethers.parseEther("52500000") },
        { name: "Final Admin", wallet: finalAdmin, amount: ethers.parseEther("52500000") },
    ];

    for (const alloc of allocations) {
        console.log(`     -> Sending ${ethers.formatEther(alloc.amount)} DAIM to ${alloc.name}...`);
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        tx = await (daimToken as any).transfer(alloc.wallet, alloc.amount);
        await tx.wait(2);
        console.log("        -> Confirmed.");
    }

    // 3. Register Genesis Wallets
    const stakeAmount = ethers.parseEther("10");
    const ethFund = ethers.parseEther("0.001");

    for (let i = 0; i < 5; i++) {
        const wallet = genesisWallets[i];
        const signer = wallet.connect(ethers.provider);

        console.log(`   Processing Genesis Agent ${i + 1} (${wallet.address})...`);

        // Fund ETH
        tx = await deployer.sendTransaction({
            to: wallet.address,
            value: ethFund
        });
        await tx.wait(2);

        // Fund DAIM
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        tx = await (daimToken as any).mint(wallet.address, stakeAmount);
        await tx.wait(2);

        // Approve Registry
        const daimWithSigner = daimToken.connect(signer);
        tx = await daimWithSigner.approve(agentRegistryAddress, stakeAmount);
        await tx.wait(2);

        // Register Agent
        // DID Proof: Mock for now "GENESIS_NODE_X"
        const genesisProof = ethers.toUtf8Bytes(`GENESIS_NODE_${i + 1}`);
        const registryWithSigner = agentRegistry.connect(signer);

        tx = await registryWithSigner.register("ipfs://genesis_metadata", 10, genesisProof);
        await tx.wait(2);
        console.log("     -> Registered & Staked (Confirmed).");
    }

    // --- 7. Transfer Admin Rights ---
    console.log("\n👑 Transferring Admin Rights to FINAL ADMIN...");

    // Grant Admin Roles to Final Admin
    const allContracts = [daimToken, agentRegistry, quantumTaskBuffer, emergencyCouncil];
    for (const contract of allContracts) {
        const addr = await contract.getAddress();
        console.log(`   - Granting Roles on ${addr}...`);

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        tx = await (contract as any).grantRole(DEFAULT_ADMIN_ROLE, finalAdmin);
        await tx.wait(2);

        // Also grant Upgrader role
        if (contract !== daimToken) { // DaimToken might handle upgrader differently or same
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const hasUpgrader = await (contract as any).UPGRADER_ROLE().catch(() => null);
            if (hasUpgrader) {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                tx = await (contract as any).grantRole(hasUpgrader, finalAdmin);
                await tx.wait(2);
            }
        }
        console.log("     -> Confirmed.");
    }

    // Renounce Deployer Roles
    console.log("   - Renouncing Deployer Roles...");
    for (const contract of allContracts) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        tx = await (contract as any).renounceRole(DEFAULT_ADMIN_ROLE, deployer.address);
        await tx.wait(2);
    }
    console.log("\n✅ Admin Rights Transferred Successfully.");

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
