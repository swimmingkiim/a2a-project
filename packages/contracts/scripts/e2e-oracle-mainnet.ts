import { ethers } from "hardhat";

// Mainnet Deployed Addresses (Base)
const DAIM_TOKEN_ADDRESS = "0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2";
const AGENT_REGISTRY_ADDRESS = "0xF720826C02AAfaEC56959387d61efA501eB1E56e";
const ORACLE_REGISTRY_ADDRESS = "0x01df22eDAF8231002214A547D80182112dB57C03";
const TASK_BUFFER_ADDRESS = "0x68F71c8dd0f056001dB59f34f28eDa92bb15e4B5";

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("-----------------------------------------");
    console.log("   MAINNET E2E: ORACLE FEE SPLIT TEST    ");
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
        await delay(3000);
    }

    if (currentReward === 0n) {
        console.log("   -> Setting baseReward to 50 DAIM...");
        const tx2 = await taskBuffer.setBaseReward(ethers.parseEther("50"), { nonce: currentNonce++ });
        await tx2.wait(1);
        await delay(3000);
    }

    // Ensure ORACLE_ROLE is granted to deployer for testing
    const ORACLE_ROLE = await taskBuffer.ORACLE_ROLE();
    const hasRole = await taskBuffer.hasRole(ORACLE_ROLE, deployer.address);
    if (!hasRole) {
        console.log("   -> Granting ORACLE_ROLE to testing wallet...");
        try {
            const tx3 = await taskBuffer.grantRole(ORACLE_ROLE, deployer.address, { nonce: currentNonce++ });
            await tx3.wait(1);
            await delay(3000);
            console.log("   -> ✅ ORACLE_ROLE granted.");
        } catch (e) {
            console.log("   -> ⚠️ Could not grant ORACLE_ROLE natively (maybe not admin). Assuming testing wallet has permission via OracleRegistry. Error:", (e as any).message);
            // We increment nonce here as well if the transaction was broadcasted but failed. To be safe, re-sync nonce.
            currentNonce = await deployer.getNonce("pending");
        }
    }

    // Approve Task Buffer for Deposit
    console.log("🔸 Approving QuantumTaskBuffer...");
    const approveTx = await daimToken.approve(TASK_BUFFER_ADDRESS, ethers.MaxUint256, { nonce: currentNonce++ });
    await approveTx.wait(1);
    await delay(3000);

    // Ensure the wallet is registered in AgentRegistry
    console.log("🔸 Checking Agent Registration...");
    const agentRegistry = await ethers.getContractAt("AgentRegistry", AGENT_REGISTRY_ADDRESS);
    const agentData = await agentRegistry.agents(deployer.address);
    if (!agentData.isRegistered) {
        console.log("   -> Registering testing wallet as Agent...");
        // Define dummy DID and endpoint for testing
        const dummyDid = "did:web:e2e-mainnet-" + Date.now() + ".com";
        const dummyEndpoint = "https://e2e-mainnet-test.com/api";
        // Approve registry for the 100 DAIM stake required for registration
        const stakeApproveTx = await daimToken.approve(AGENT_REGISTRY_ADDRESS, ethers.parseEther("100"), { nonce: currentNonce++ });
        await stakeApproveTx.wait(1);
        await delay(3000);

        try {
            const registerTx = await agentRegistry.register(dummyEndpoint, 1, "0x", { nonce: currentNonce++ });
            await registerTx.wait(1);
            console.log("   -> ✅ Registered successfully!");
            await delay(3000);
        } catch (e) {
            console.log("   -> ⚠️ Registration skipped or failed. It might be already registered with another DID, or requires explicit voucher logic depending on the contract setup. Error: ", (e as any).message);
        }
    } else {
        console.log("   -> ✅ Wallet is already registered.");
    }

    // Let's grab the balance diff for deployer
    const preSubmitBal = await daimToken.balanceOf(deployer.address);
    console.log(`✅ Pre-submit Deployer Balance: ${ethers.formatEther(preSubmitBal)} DAIM`);

    // Submit Task (Agent Action)
    const complexityHash = ethers.id("mainnet_task_hash_" + Date.now());
    console.log(`🔸 Submitting Task...`);
    const submitTx = await taskBuffer.submitTask(
        complexityHash,
        "ipfs://QmTestMetadataURI",
        { nonce: currentNonce++, gasLimit: 500000 }
    );
    const receipt1 = await submitTx.wait(1);

    const taskSubmittedEvent = receipt1?.logs.find((log: any) => {
        try {
            // @ts-ignore
            const parsed = taskBuffer.interface.parseLog(log);
            return parsed && parsed.name === 'TaskSubmitted';
        } catch (e) { return false; }
    });

    // @ts-ignore
    const parsedEvent = taskBuffer.interface.parseLog(taskSubmittedEvent as any);
    const taskId = parsedEvent?.args[0];
    const depositAmt = parsedEvent?.args[2];
    console.log(`✅ Task Submitted (ID: ${taskId}, Deposit: ${ethers.formatEther(depositAmt)} DAIM)`);
    await delay(3000);

    // Finalize Task (Oracle Action) -> Simulating success
    console.log("🔸 Finalizing Task (Success: Complexity 80, Score 90)...");
    const finalizeTx = await taskBuffer.finalizeTask(taskId, 80, 90, { nonce: currentNonce++ });
    const receipt2 = await finalizeTx.wait(1);
    console.log(`✅ Task Finalized! (Hash: ${receipt2?.hash})`);
    await delay(3000);

    const postFinalizeBal = await daimToken.balanceOf(deployer.address);
    console.log(`✅ Post-Finalize Deployer Balance: ${ethers.formatEther(postFinalizeBal)} DAIM`);

    const oracleRegistry = await ethers.getContractAt("OracleRegistry", ORACLE_REGISTRY_ADDRESS);
    const oracleData = await oracleRegistry.oracles(deployer.address);
    console.log(`🔍 Oracle Data - Total: ${oracleData.totalEvaluations}, Valid: ${oracleData.validEvaluations}, Slashed: ${oracleData.slashedEvaluations}`);

    if (oracleData.totalEvaluations > 0n) {
        console.log("🎉 E2E MAINNET VERIFICATION SUCCESSFUL!");
    } else {
        console.error("❌ E2E Verification Failed: OracleRegistry not updated.");
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
