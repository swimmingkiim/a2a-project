import { ethers } from "hardhat";
async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("Wallet:", deployer.address);
    const latest = await deployer.getNonce("latest");
    const pending = await deployer.getNonce("pending");
    console.log("Latest Nonce:", latest);
    console.log("Pending Nonce:", pending);
}
main().catch(console.error);
