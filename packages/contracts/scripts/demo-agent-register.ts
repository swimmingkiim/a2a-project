import { ethers } from "hardhat";

async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("--- Agent Registration Demo ---");
    console.log("Executor:", deployer.address);

    // Addresses (From Deployed Artifact)
    // In a real automated script, we'd read DEPLOYED_ADDRESSES.md or a json file.
    // UPDATE THESE VALUES AFTER DEPLOYMENT
    const COMP_TOKEN_ADDR = process.env.COMP_TOKEN_ADDRESS || "0x...";
    const AGENT_REGISTRY_ADDR = process.env.AGENT_REGISTRY_ADDRESS || "0x...";
    const MOCK_ORACLE_ADDR = "0x...";

    // 1. Setup Interfaces
    const ComputeToken = await ethers.getContractAt("ComputeToken", COMP_TOKEN_ADDR);
    const AgentRegistry = await ethers.getContractAt("AgentRegistry", AGENT_REGISTRY_ADDR);

    // 2. Mint COMP (Simulate acquiring tokens)
    console.log("\n1. Acquiring COMP Tokens...");
    // Mock token allows deployer to mint
    const mintAmount = ethers.parseEther("1000"); // 1000 COMP
    try {
        const txMint = await ComputeToken.mint(deployer.address, mintAmount);
        await txMint.wait();
        console.log("   -> Minted 1000 COMP");
    } catch (e) {
        console.log("   -> Minting failed (maybe not owner?):", e.message);
    }

    // 3. Approve Registry
    console.log("\n2. Approving Registry...");
    const txApprove = await ComputeToken.approve(AGENT_REGISTRY_ADDR, ethers.MaxUint256);
    await txApprove.wait();
    console.log("   -> Approved Infinite COMP");

    // 4. Register Agent
    console.log("\n3. Registering Agent...");
    // Params:
    // _unitPrice: 10 (High throughput agent)
    // _metadata: "ipfs://QmTest..."
    // _verifierData: "0x" (Mock Verifier accepts anything)
    const unitPrice = 10;

    // Calculate Quadratic Cost Client-Side (10 USD Base)
    // Cost = 10 * (Units^2)
    const baseStakeUSD = ethers.parseUnits("10", 8); // $10 with 8 decimals
    const costUSD = baseStakeUSD * BigInt(unitPrice * unitPrice);

    // Convert to COMP using contract helper
    const cost = await AgentRegistry.getCompAmountFromUSD(costUSD);
    console.log(`   -> Calculated Cost for 10 units: ${ethers.formatEther(cost)} COMP`);

    const txRegister = await AgentRegistry.register(
        "ipfs://QmTestAgentMetadata",
        unitPrice,
        "0x" // Mock proof
    );
    console.log("   -> Transaction sent:", txRegister.hash);
    await txRegister.wait();
    console.log("✅ Agent Registered Successfully!");

    // 5. Verify Registration
    const agent = await AgentRegistry.agents(deployer.address);
    if (agent.isRegistered) {
        console.log("   -> Verified: Agent is registered.");
        console.log("   -> Staked Amount:", ethers.formatEther(agent.stakedAmount), "COMP");
        console.log("   -> Metadata:", agent.metadataUrl);
    } else {
        console.log("❌ Agent not found in registry (Eventual consistency delay?)");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
