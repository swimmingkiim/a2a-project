import { ethers } from "hardhat";

async function main() {
    console.log("--- Checking Mainnet Balance (Direct) ---");
    const deployerAddress = "0xb6AF245cB3f8F85b1b4d62BD3f1C93f9cC48b88c";
    console.log("Checking Address:", deployerAddress);

    const provider = new ethers.JsonRpcProvider("https://mainnet.base.org");
    const balance = await provider.getBalance(deployerAddress);
    const balanceEth = ethers.formatEther(balance);

    console.log(`Balance (https://mainnet.base.org): ${balanceEth} ETH`);

    if (balance === 0n) {
        console.log("❌ CONFIRMED: Balance is 0.");
    } else {
        console.log("✅ FUNDS FOUND! Hardhat config might be using a different RPC.");
    }
}

main().catch(console.error);
