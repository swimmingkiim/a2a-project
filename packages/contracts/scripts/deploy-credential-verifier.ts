import { ethers, upgrades } from "hardhat";

/**
 * Upgrades AgentRegistry (adds setVerifier) and deploys CredentialVerifier (Web of Trust).
 *
 * Steps:
 *   1. Upgrade AgentRegistry implementation (UUPS) to add setVerifier()
 *   2. Deploy CredentialVerifier proxy
 *   3. Wire: registry.setVerifier(credentialVerifier)
 *
 * Prerequisites:
 *   - DEPLOYER_PRIVATE_KEY in .env (must have ADMIN_ROLE + UPGRADER_ROLE on AgentRegistry)
 *
 * Usage:
 *   npx hardhat run scripts/deploy-credential-verifier.ts --network base-mainnet
 */

const AGENT_REGISTRY_PROXY = "0xF720826C02AAfaEC56959387d61efA501eB1E56e";

async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("Deployer:", deployer.address);
    console.log("Network:", (await ethers.provider.getNetwork()).chainId);

    // --- Step 1: Upgrade AgentRegistry ---
    console.log("\n📦 Step 1: Upgrading AgentRegistry implementation...");
    const AgentRegistryV2 = await ethers.getContractFactory("AgentRegistry");

    // Force import to register the proxy (needed if first time using upgrades plugin on this machine)
    try {
        await upgrades.forceImport(AGENT_REGISTRY_PROXY, AgentRegistryV2, { kind: "uups" });
        console.log("   Proxy imported to upgrades manifest.");
    } catch {
        console.log("   Proxy already in manifest, skipping import.");
    }

    const upgraded = await upgrades.upgradeProxy(AGENT_REGISTRY_PROXY, AgentRegistryV2);
    await upgraded.waitForDeployment();
    const newImpl = await upgrades.erc1967.getImplementationAddress(AGENT_REGISTRY_PROXY);
    console.log("   ✅ AgentRegistry upgraded. New impl:", newImpl);

    // Verify setVerifier exists
    const registry = await ethers.getContractAt("AgentRegistry", AGENT_REGISTRY_PROXY);

    // --- Step 2: Deploy CredentialVerifier ---
    console.log("\n🔐 Step 2: Deploying CredentialVerifier (Web of Trust)...");

    // Bootstrap voucher = deployer (admin) for now
    const bootstrapVoucher = deployer.address;

    const VerifierFactory = await ethers.getContractFactory("CredentialVerifier");
    const verifier = await upgrades.deployProxy(VerifierFactory, [
        deployer.address,       // admin
        AGENT_REGISTRY_PROXY,   // agentRegistry
        bootstrapVoucher,       // bootstrapVoucher
    ], { kind: "uups" });
    await verifier.waitForDeployment();
    const verifierAddress = await verifier.getAddress();
    console.log("   ✅ CredentialVerifier deployed to:", verifierAddress);

    // --- Step 3: Wire ---
    console.log("\n🔗 Step 3: Wiring AgentRegistry → CredentialVerifier...");
    const tx = await registry.setVerifier(verifierAddress);
    const receipt = await tx.wait(2);
    console.log("   ✅ AgentRegistry.verifier updated. TX:", receipt?.hash);

    // --- Summary ---
    console.log("\n" + "=".repeat(60));
    console.log("  DEPLOYMENT COMPLETE");
    console.log("=".repeat(60));
    console.log("  AgentRegistry (proxy):    ", AGENT_REGISTRY_PROXY);
    console.log("  AgentRegistry (new impl): ", newImpl);
    console.log("  CredentialVerifier:       ", verifierAddress);
    console.log("  Bootstrap Voucher:        ", bootstrapVoucher);
    console.log("  Old MockVerifier:          0x9B4690Fc80cD87C6f52E1b4962C08E2036dFDf38 (replaced)");
    console.log("=".repeat(60));
    console.log("\n⚠️  UPDATE docs/deployment/DEPLOYED_ADDRESSES.md with:");
    console.log(`  CredentialVerifier: ${verifierAddress}`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
