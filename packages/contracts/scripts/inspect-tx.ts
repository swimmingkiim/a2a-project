import { ethers } from "hardhat";

async function main() {
    const txHash = process.env.TX_HASH;
    if (!txHash) {
        throw new Error("Please provide a TX_HASH environment variable");
    }

    console.log("-----------------------------------------");
    console.log("   INSPECTING USER APPROVE TRANSACTION   ");
    console.log("-----------------------------------------");

    const tx = await ethers.provider.getTransaction(txHash);

    if (!tx) {
        console.log("❌ Transaction not found!");
        return;
    }

    console.log("Target Contract (to):", tx.to);
    console.log("Sender (from):", tx.from);

    const TRUE_DAIM = "0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2".toLowerCase();
    const PARALLEL_DAIM = "0x1BF0a1BBD8262FBD7C00534E200A87537D6Fa6aB".toLowerCase();

    if (tx.to?.toLowerCase() === TRUE_DAIM) {
        console.log("✅ The user called approve on the TRUE DAIM Contract.");
    } else if (tx.to?.toLowerCase() === PARALLEL_DAIM) {
        console.log("❌ The user called approve on the FALSE (PARALLEL) DAIM Contract.");
    } else {
        console.log("⚠️ The user called approve on an UNKNOWN Contract:", tx.to);
    }

    // Let's also check the actual allowance on the True DAIM for this sender
    const TASK_BUFFER = "0x68F71c8dd0f056001dB59f34f28eDa92bb15e4B5";
    const daim = await ethers.getContractAt("DaimToken", TRUE_DAIM);
    const allowance = await daim.allowance(tx.from, TASK_BUFFER);
    const balance = await daim.balanceOf(tx.from);

    console.log("\nCurrent On-Chain State for the Sender on TRUE DAIM:");
    console.log(" - Balance:", ethers.formatEther(balance));
    console.log(" - Allowance to True QuantumTaskBuffer:", ethers.formatEther(allowance));
}

main().catch(console.error);
