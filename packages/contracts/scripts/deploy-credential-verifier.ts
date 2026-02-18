import { ethers, upgrades } from "hardhat";

/**
 * Deploys the production CredentialVerifier and updates the AgentRegistry
 * to use it instead of MockVerifier.
 *
 * Prerequisites:
 *   - DEPLOYER_PRIVATE_KEY in .env (must have ADMIN_ROLE on AgentRegistry)
 *   - TRUSTED_SIGNER_ADDRESS in .env (the off-chain attestation signer)
 *   - AGENT_REGISTRY_ADDRESS in .env (the deployed AgentRegistry proxy)
 *
 * Usage:
 *   npx hardhat run scripts/deploy-credential-verifier.ts --network base-mainnet
 */
async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("Deployer:", deployer.address);

    const trustedSigner = process.env.TRUSTED_SIGNER_ADDRESS;
    const registryAddress = process.env.AGENT_REGISTRY_ADDRESS;

    if (!trustedSigner) {
        throw new Error("TRUSTED_SIGNER_ADDRESS not set in environment");
    }
    if (!registryAddress) {
        throw new Error("AGENT_REGISTRY_ADDRESS not set in environment");
    }

    // 1. Deploy CredentialVerifier (UUPS Proxy)
    console.log("\n🔐 Deploying CredentialVerifier...");
    const VerifierFactory = await ethers.getContractFactory("CredentialVerifier");
    const verifier = await upgrades.deployProxy(VerifierFactory, [
        deployer.address,
        trustedSigner,
    ], { kind: "uups" });
    await verifier.waitForDeployment();
    const verifierAddress = await verifier.getAddress();
    console.log("   CredentialVerifier deployed to:", verifierAddress);

    // 2. Update AgentRegistry to use new verifier
    console.log("\n🔗 Updating AgentRegistry verifier...");
    const registry = await ethers.getContractAt("AgentRegistry", registryAddress);
    const tx = await registry.setVerifier(verifierAddress);
    await tx.wait(2);
    console.log("   AgentRegistry.verifier updated (confirmed).");

    // 3. Summary
    console.log("\n✅ Deployment Complete!");
    console.log("---------------------------------------------------");
    console.log("CredentialVerifier:", verifierAddress);
    console.log("Trusted Signer:", trustedSigner);
    console.log("AgentRegistry:", registryAddress);
    console.log("---------------------------------------------------");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
