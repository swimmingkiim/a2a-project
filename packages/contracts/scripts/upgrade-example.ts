import { ethers, upgrades } from "hardhat";

async function main() {
    const proxyAddress = "YOUR_PROXY_ADDRESS_HERE"; // Replace with deployed proxy address

    console.log("Upgrading AgentRegistry...");

    // 1. Get the Contract Factory for the NEW implementation
    // Make sure you have compiled the new version of the contract
    const AgentRegistryV2 = await ethers.getContractFactory("AgentRegistry");

    // 2. Propose the upgrade (if using Defender) or Upgrade directly (if local/private key)
    // This will deploying the new implementation contract and call upgradeTo() on the proxy
    const upgraded = await upgrades.upgradeProxy(proxyAddress, AgentRegistryV2);

    // 3. Wait for the transaction to be mined
    await upgraded.waitForDeployment();

    console.log("AgentRegistry upgraded successfully!");
    console.log("Implementation address:", await upgrades.erc1967.getImplementationAddress(proxyAddress));
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
