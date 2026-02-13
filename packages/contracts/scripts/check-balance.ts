import { ethers } from "hardhat";

async function main() {
    const [deployer] = await ethers.getSigners();
    const provider = new ethers.JsonRpcProvider("https://sepolia.base.org");

    console.log("Checking balance for address:", deployer.address);
    const balance = await provider.getBalance(deployer.address);
    // Also check hardhat provider just in case
    const balanceConfig = await ethers.provider.getBalance(deployer.address);

    console.log("Balance (Direct RPC):", ethers.formatEther(balance), "ETH");
    console.log("Balance (Hardhat):", ethers.formatEther(balanceConfig), "ETH");

    if (balance === 0n && balanceConfig === 0n) {
        console.error("Balance is still 0.");
        process.exit(1);
    } else {
        console.log("✅ Funds detected!");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
