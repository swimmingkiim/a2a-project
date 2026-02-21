import { ethers, network } from "hardhat";
import * as dotenv from "dotenv";
dotenv.config();

// Mainnet Deployed Addresses (Base)
const DAIM_TOKEN_ADDRESS = "0x1BF0a1BBD8262FBD7C00534E200A87537D6Fa6aB";
const TASK_BUFFER_ADDRESS = "0xB372f6764407B58473127A5Df22797a0033428D2";

async function main() {
    let deployer: any;
    const signers = await ethers.getSigners();
    const pk = process.env.DEPLOYER_PRIVATE_KEY;

    if (signers && signers.length > 0) {
        deployer = signers[0];
    } else if (pk) {
        try {
            deployer = new ethers.Wallet(pk, ethers.provider);
        } catch (e: any) {
            console.error("❌ The provided DEPLOYER_PRIVATE_KEY is invalid:", e.message);
            process.exit(1);
        }
    } else {
        console.error("❌ The DEPLOYER_PRIVATE_KEY was not found.");
        console.error("👉 Please make sure you prepend it to the command exactly like this:");
        console.error('DEPLOYER_PRIVATE_KEY="0xYourPrivateKey" npx hardhat run scripts/create-sample-task.ts --network base-mainnet');
        process.exit(1);
    }
    console.log("-----------------------------------------");
    console.log("   MAINNET: CREATING SAMPLE TASK FOR UI  ");
    console.log("-----------------------------------------");
    console.log(`Using wallet: ${deployer.address}`);

    const daimToken = await ethers.getContractAt("DaimToken", DAIM_TOKEN_ADDRESS);
    const taskBuffer = await ethers.getContractAt("QuantumTaskBuffer", TASK_BUFFER_ADDRESS);

    // 1. Check DAIM balance
    const balance = await daimToken.balanceOf(deployer.address);
    const baseDeposit = await taskBuffer.baseDeposit();

    console.log(`Current Balance: ${ethers.formatEther(balance)} DAIM`);
    console.log(`Required Deposit: ${ethers.formatEther(baseDeposit)} DAIM`);

    if (balance < baseDeposit) {
        console.error("❌ Insufficient DAIM balance to submit a task.");
        process.exit(1);
    }

    // 2. Check & Approve Allowance
    const allowance = await daimToken.allowance(deployer.address, TASK_BUFFER_ADDRESS);
    if (allowance < baseDeposit) {
        console.log("🔸 Approving QuantumTaskBuffer to spend DAIM...");
        const approveTx = await daimToken.approve(TASK_BUFFER_ADDRESS, ethers.MaxUint256);
        await approveTx.wait(1);
        console.log("✅ Approval confirmed.");
    } else {
        console.log("✅ Sufficient allowance already set.");
    }

    // 3. Submit Sample Task
    // Utilizing a basic IPFS metadata URI. The UI will attempt to fetch this.
    // In a real scenario, this would be a CID to a JSON file containing { title, description, input_assets, output_assets }
    const sampleMetadataUri = "ipfs://QmSampleTaskMetadata1234567890";
    const complexityHash = ethers.id("sample_ui_task_" + Date.now());

    console.log(`🔸 Submitting Task to network...`);
    const submitTx = await taskBuffer.submitTask(
        complexityHash,
        sampleMetadataUri,
        // Optional: Manual gas limit to prevent estimation errors
        { gasLimit: 500000 }
    );

    console.log(`Waiting for confirmation... (TxHash: ${submitTx.hash})`);
    const receipt = await submitTx.wait(1);

    // Parse logs to find specific Task ID
    const taskSubmittedEvent = receipt?.logs.find((log: any) => {
        try {
            // @ts-ignore
            const parsed = taskBuffer.interface.parseLog(log);
            return parsed && parsed.name === 'TaskSubmitted';
        } catch (e) { return false; }
    });

    let taskId = "Unknown";
    if (taskSubmittedEvent) {
        // @ts-ignore
        const parsedEvent = taskBuffer.interface.parseLog(taskSubmittedEvent as any);
        taskId = parsedEvent?.args[0].toString();
    }

    console.log("🎉 Sample Task Created Successfully!");
    console.log(`✅ Task ID: ${taskId}`);
    console.log(`✅ Metadata URI: ${sampleMetadataUri}`);
    console.log("\\n👉 Now visit https://a10m.work/oracle and connect your wallet to see the task in the dropdown!");
}

main().catch((error) => {
    console.error("Task submission failed:", error);
    process.exitCode = 1;
});
