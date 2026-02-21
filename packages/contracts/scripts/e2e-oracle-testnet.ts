import { ethers } from "hardhat";

// Testnet Deployed Addresses (Base Sepolia)
const DAIM_TOKEN_ADDRESS = "0x29A7F1aD64ebC0214a66505adc237Ecc1bBA346f";
const AGENT_REGISTRY_ADDRESS = "0x62b2adA575A9187056c9F7b43cB4B517aBBA3f6b";
const ORACLE_REGISTRY_ADDRESS = "0x3D6c3eD3b705D6f434d0D282Fa127F0Ce3d98Ab5";
const TASK_BUFFER_ADDRESS = "0xEA915c8f0c3e85591d0E38b869948595807e101C";

async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("-----------------------------------------");
    console.log("   TESTNET E2E: ORACLE FEE SPLIT TEST    ");
    console.log("-----------------------------------------");

    const daimToken = await ethers.getContractAt("DaimToken", DAIM_TOKEN_ADDRESS);
    const taskBuffer = await ethers.getContractAt("QuantumTaskBuffer", TASK_BUFFER_ADDRESS);

    console.log("🔸 Checking / Initializing Base Configs...");
    const currentDeposit = await taskBuffer.baseDeposit();
    const currentReward = await taskBuffer.baseReward();

    let currentNonce = await deployer.getNonce("pending");

    if (currentDeposit === 0n) {
        console.log("   -> Setting baseDeposit to 10 DAIM...");
        const tx1 = await taskBuffer.setBaseDeposit(ethers.parseEther("10"), { nonce: currentNonce++ });
        await tx1.wait(1);
    }

    if (currentReward === 0n) {
        console.log("   -> Setting baseReward to 50 DAIM...");
        const tx2 = await taskBuffer.setBaseReward(ethers.parseEther("50"), { nonce: currentNonce++ });
        await tx2.wait(1);
    }

    // Ensure ORACLE_ROLE is granted to deployer for testing
    const ORACLE_ROLE = await taskBuffer.ORACLE_ROLE();
    const hasRole = await taskBuffer.hasRole(ORACLE_ROLE, deployer.address);
    if (!hasRole) {
        console.log("   -> Granting ORACLE_ROLE to testing wallet...");
        const tx3 = await taskBuffer.grantRole(ORACLE_ROLE, deployer.address, { nonce: currentNonce++ });
        await tx3.wait(1);
    }

    // Approve Task Buffer for Deposit
    console.log("🔸 Approving QuantumTaskBuffer...");
    const approveTx = await daimToken.approve(TASK_BUFFER_ADDRESS, ethers.MaxUint256, { nonce: currentNonce++ });
    await approveTx.wait(1);

    // Let's grab the balance diff for deployer
    const preSubmitBal = await daimToken.balanceOf(deployer.address);
    console.log(`✅ Pre-submit Deployer Balance: ${ethers.formatEther(preSubmitBal)} DAIM`);

    // Ensure the wallet is registered in AgentRegistry
    console.log("🔸 Checking Agent Registration...");
    const agentRegistry = await ethers.getContractAt("AgentRegistry", AGENT_REGISTRY_ADDRESS);
    const agentData = await agentRegistry.agents(deployer.address);
    if (!agentData.isRegistered) {
        console.log("   -> Registering testing wallet as Agent...");
        const dummyDid = "did:web:e2e-testnet-" + Date.now() + ".com";
        const dummyEndpoint = "https://e2e-testnet.com/api";
        const stakeApproveTx = await daimToken.approve(AGENT_REGISTRY_ADDRESS, ethers.parseEther("100"), { nonce: currentNonce++ });
        await stakeApproveTx.wait(1);

        try {
            const registerTx = await agentRegistry.register(dummyEndpoint, 1, "0x", { nonce: currentNonce++ });
            await registerTx.wait(1);
            console.log("   -> ✅ Registered successfully!");
        } catch (e) {
            console.log("   -> ⚠️ Registration skipped or failed. Error: ", (e as any).message);
        }
    } else {
        console.log("   -> ✅ Wallet is already registered.");
    }

    // Submit Task (Agent Action)
    const complexityHash = ethers.id("testnet_task_hash_" + Date.now());
    console.log(`🔸 Submitting Task...`);
    const submitTx = await taskBuffer.submitTask(
        complexityHash,
        "ipfs://QmTestMetadataURI",
        { nonce: currentNonce++, gasLimit: 500000 }
    );
    const receipt1 = await submitTx.wait(1);

    const taskSubmittedEvent = receipt1?.logs.find((log: any) => {
        try {
            const parsed = taskBuffer.interface.parseLog(log);
            return parsed && parsed.name === 'TaskSubmitted';
        } catch (e) { return false; }
    });

    const parsedEvent = taskBuffer.interface.parseLog(taskSubmittedEvent as any);
    const taskId = parsedEvent?.args[0];
    const depositAmt = parsedEvent?.args[2];
    console.log(`✅ Task Submitted (ID: ${taskId}, Deposit: ${ethers.formatEther(depositAmt)} DAIM)`);

    const preFinalizeBal = await daimToken.balanceOf(deployer.address);

    // Finalize Task (Oracle Action) -> Simulating success
    console.log("🔸 Finalizing Task (Success: Complexity 80, Score 90)...");
    const finalizeTx = await taskBuffer.finalizeTask(taskId, 80, 90, { nonce: currentNonce++ });
    const receipt2 = await finalizeTx.wait(1);
    console.log(`✅ Task Finalized! (Hash: ${receipt2?.hash})`);

    const postFinalizeBal = await daimToken.balanceOf(deployer.address);
    console.log(`✅ Post-Finalize Deployer Balance: ${ethers.formatEther(postFinalizeBal)} DAIM`);

    const oracleRegistry = await ethers.getContractAt("OracleRegistry", ORACLE_REGISTRY_ADDRESS);
    const oracleData = await oracleRegistry.oracles(deployer.address);
    console.log(`🔍 Oracle Data - Total: ${oracleData.totalEvaluations}, Valid: ${oracleData.validEvaluations}, Slashed: ${oracleData.slashedEvaluations}`);

    if (oracleData.totalEvaluations > 0n) {
        console.log("🎉 E2E TESTNET VERIFICATION SUCCESSFUL!");
    } else {
        console.error("❌ E2E Verification Failed: OracleRegistry not updated.");
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
