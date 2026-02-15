import { ethers } from "hardhat";

async function main() {
    const [signer] = await ethers.getSigners();
    console.log(`🔑 Current Signer: ${signer ? signer.address : "Undefined"}`);

    if (!signer) {
        console.error("❌ No signer configured. Check hardhat.config.ts and DEPLOYER_PRIVATE_KEY.");
        return;
    }

    const DAIM_TOKEN_ADDRESS = "0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2";
    const daimToken = await ethers.getContractAt("DaimToken", DAIM_TOKEN_ADDRESS);
    const DEFAULT_ADMIN_ROLE = await daimToken.DEFAULT_ADMIN_ROLE();

    const isAdmin = await daimToken.hasRole(DEFAULT_ADMIN_ROLE, signer.address);
    console.log(`🛡️ Has DEFAULT_ADMIN_ROLE? ${isAdmin ? "✅ YES" : "❌ NO"}`);

    const balance = await ethers.provider.getBalance(signer.address);
    console.log(`💰 Balance: ${ethers.formatEther(balance)} ETH`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
