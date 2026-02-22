import { ethers } from "hardhat";

async function main() {
    const BOT_ADDRESS = "0x68E0F8d90c7Afe4a22Ea62f71814F71Fc3A9FE6F";
    const TASK_BUFFER = "0x68F71c8dd0f056001dB59f34f28eDa92bb15e4B5";
    const FAILED_TX_DATA = "0xfb8f41b200000000000000000000000068f71c8dd0f056001db59f34f28eda92bb15e4b500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008ac7230489e80000"; // Wait, look at this data.

    // Let's decode this data. The selector is 0xfb8f41b2.
    // What function signature is that?
    // Let's check ERC20 approve: 0x095ea7b3
    // transfer: 0xa9059cbb
    // transferFrom: 0x23b872dd
    // submitTask: wait, what is submitTask selector?

    const taskBuffer = await ethers.getContractAt("QuantumTaskBuffer", TASK_BUFFER);
    const submitTaskFragment = taskBuffer.interface.getFunction("submitTask");
    console.log("Expected submitTask selector:", submitTaskFragment?.selector);

    console.log("User's failed tx data selector:", "0xfb8f41b2");
}

main().catch(console.error);
