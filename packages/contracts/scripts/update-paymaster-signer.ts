import { ethers } from "hardhat";
import hre from "hardhat";

async function main() {
    console.log("🔐 Updating Paymaster Signer...");

    const PAYMASTER_ADDRESS = process.env.PAYMASTER_ADDRESS;
    const NEW_SIGNER = process.env.NEW_SIGNER_ADDRESS;

    if (!PAYMASTER_ADDRESS) {
        throw new Error("❌ PAYMASTER_ADDRESS environment variable is missing.");
    }
    if (!NEW_SIGNER) {
        throw new Error("❌ NEW_SIGNER_ADDRESS environment variable is missing.");
    }

    console.log(`target Paymaster: ${PAYMASTER_ADDRESS}`);
    console.log(`New Signer:       ${NEW_SIGNER}`);

    const [admin] = await hre.ethers.getSigners();
    console.log(`Executor (Admin): ${(await admin.getAddress())}`);

    // Attach to contract
    // We assume a generic interface with setSigner or setVerifyingSigner
    // You might need to adjust the ABI if your contract has a different function name.
    const paymaster = await ethers.getContractAt(
        ["function setSigner(address _signer) external", "function setVerifyingSigner(address _signer) external", "function owner() view returns (address)"],
        PAYMASTER_ADDRESS,
        admin
    );

    // Check ownership (optional debugging)
    try {
        const owner = await paymaster.owner();
        console.log(`Contract Owner:   ${owner}`);
        if (owner.toLowerCase() !== (await admin.getAddress()).toLowerCase()) {
            console.warn("⚠️  WARNING: Executor is NOT the contract owner. Transaction may fail.");
        }
    } catch (e) {
        console.log("ℹ️  Could not fetch owner (function might not exist).");
    }

    // Attempt setSigner first
    try {
        console.log("Attempting setSigner...");
        const tx = await paymaster.setSigner(NEW_SIGNER);
        console.log(`✅ Transaction sent: ${tx.hash}`);
        await tx.wait();
        console.log("✅ Signer updated successfully.");
        return;
    } catch (e) {
        console.log("⚠️  setSigner failed or not found. Trying setVerifyingSigner...");
    }

    // Attempt setVerifyingSigner
    try {
        const tx = await paymaster.setVerifyingSigner(NEW_SIGNER);
        console.log(`✅ Transaction sent: ${tx.hash}`);
        await tx.wait();
        console.log("✅ Verifying Signer updated successfully.");
    } catch (e: any) {
        console.error("❌ Failed to update signer. Please check the contract ABI and function name.");
        console.error(e.message);
        process.exit(1);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
