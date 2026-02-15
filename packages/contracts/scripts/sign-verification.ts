import { ethers } from "hardhat";

async function main() {
    const privateKey = process.env.DEPLOYER_PRIVATE_KEY;
    if (!privateKey) {
        console.error("❌ Error: DEPLOYER_PRIVATE_KEY environment variable is not set.");
        console.error("Usage: DEPLOYER_PRIVATE_KEY=<YOUR_KEY> npx hardhat run scripts/sign-verification.ts");
        process.exit(1);
    }

    const wallet = new ethers.Wallet(privateKey);
    const message = "[basescan.org 15/02/2026 07:07:45] I, hereby verify that I am the owner/creator of the address [0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2]";

    console.log("\n🔐 Signing Verification Message for BaseScan");
    console.log("------------------------------------------------");
    console.log(`📝 Message:  "${message}"`);
    console.log(`👤 Signer:   ${wallet.address}`);
    console.log("------------------------------------------------");

    const signature = await wallet.signMessage(message);

    console.log("\n✅ Signature Generated:");
    console.log(signature);
    console.log("\nCopy the signature above and paste it into BaseScan.");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
