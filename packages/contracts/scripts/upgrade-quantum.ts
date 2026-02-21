import { ethers, upgrades } from "hardhat";
import * as dotenv from "dotenv";

dotenv.config();

const QUANTUM_TASK_BUFFER_PROXY = "0xB372f6764407B58473127A5Df22797a0033428D2";

async function main() {
    let deployer: any;
    const signers = await ethers.getSigners();
    if (signers && signers.length > 0) {
        deployer = signers[0];
    } else {
        const pk = process.env.DEPLOYER_PRIVATE_KEY;
        if (!pk) throw new Error("DEPLOYER_PRIVATE_KEY is missing");
        deployer = new ethers.Wallet(pk, ethers.provider || ethers.getDefaultProvider());
    }

    console.log("--------------------------------------------------");
    console.log("  MAINNET UPGRADE: QuantumTaskBuffer ");
    console.log("--------------------------------------------------");
    console.log(`Using deployer wallet: ${deployer.address}`);
    console.log(`Target Proxy: ${QUANTUM_TASK_BUFFER_PROXY}`);

    console.log("\n1. Preparing upgrade for QuantumTaskBuffer...");
    const QuantumTaskBufferV2 = await ethers.getContractFactory("QuantumTaskBuffer", deployer);

    console.log("2. Sending upgrade transaction...");
    const upgradedTaskBuffer = await upgrades.upgradeProxy(QUANTUM_TASK_BUFFER_PROXY, QuantumTaskBufferV2);

    // Wait for deployment transaction to be mined
    await upgradedTaskBuffer.waitForDeployment();

    console.log(`✅ QuantumTaskBuffer successfully upgraded!`);

    // Attempt verification (might fail if already verified or similar bytecode, but good to try)
    try {
        const implementationAddr = await upgrades.erc1967.getImplementationAddress(QUANTUM_TASK_BUFFER_PROXY);
        console.log(`   Implementation Address: ${implementationAddr}`);
    } catch (e: any) {
        console.log(`   Could not fetch implementation address: ${e.message}`);
    }
}

main().catch((error) => {
    console.error("Upgrade failed:", error);
    process.exitCode = 1;
});
