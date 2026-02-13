import { ethers } from "hardhat";

/**
 * Deploys the ComputeToken contract to the configured network
 * 
 * Usage:
 *   pnpm deploy:sepolia    # Deploy to Base Sepolia testnet
 *   pnpm deploy:mainnet    # Deploy to Base Mainnet
 * 
 * Environment Variables Required:
 *   PAYMASTER_ADDRESS      # Address that will receive MINTER_ROLE
 *   DEPLOYER_PRIVATE_KEY   # Private key of deployer wallet
 *   BASE_SEPOLIA_RPC_URL   # RPC endpoint (optional, has default)
 *   BASESCAN_API_KEY       # For contract verification
 */
async function main() {
    const [deployer] = await ethers.getSigners();

    console.log("🚀 Deploying ComputeToken with account:", deployer.address);
    console.log("💰 Account balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "ETH");

    // Get Paymaster address from environment
    const paymasterAddress = process.env.PAYMASTER_ADDRESS;

    if (!paymasterAddress) {
        throw new Error("❌ PAYMASTER_ADDRESS environment variable is required");
    }

    if (!ethers.isAddress(paymasterAddress)) {
        throw new Error(`❌ Invalid PAYMASTER_ADDRESS: ${paymasterAddress}`);
    }

    console.log("🔑 Paymaster address (will receive MINTER_ROLE):", paymasterAddress);

    // Deploy ComputeToken
    const ComputeToken = await ethers.getContractFactory("ComputeToken");
    const computeToken = await ComputeToken.deploy(paymasterAddress);

    await computeToken.waitForDeployment();

    const tokenAddress = await computeToken.getAddress();

    console.log("\n✅ ComputeToken deployed successfully!");
    console.log("📍 Contract address:", tokenAddress);
    console.log("📝 Token name:", await computeToken.name());
    console.log("🔤 Token symbol:", await computeToken.symbol());
    console.log("🔢 Decimals:", await computeToken.decimals());
    console.log("💎 Total supply:", ethers.formatEther(await computeToken.totalSupply()), "COMP");

    // Verify roles
    const MINTER_ROLE = await computeToken.MINTER_ROLE();
    const DEFAULT_ADMIN_ROLE = await computeToken.DEFAULT_ADMIN_ROLE();

    console.log("\n🔐 Access Control:");
    console.log("  - Admin:", deployer.address, await computeToken.hasRole(DEFAULT_ADMIN_ROLE, deployer.address) ? "✅" : "❌");
    console.log("  - Minter:", paymasterAddress, await computeToken.hasRole(MINTER_ROLE, paymasterAddress) ? "✅" : "❌");

    // Save deployment info
    const deploymentInfo = {
        network: (await ethers.provider.getNetwork()).name,
        chainId: (await ethers.provider.getNetwork()).chainId,
        contractAddress: tokenAddress,
        deployer: deployer.address,
        paymaster: paymasterAddress,
        deploymentTime: new Date().toISOString(),
        txHash: computeToken.deploymentTransaction()?.hash,
    };

    console.log("\n📋 Deployment Summary:");
    console.log(JSON.stringify(deploymentInfo, (key, value) =>
        typeof value === 'bigint' ? value.toString() : value
        , 2));


    console.log("\n🔍 Verify contract on Basescan:");
    console.log(`npx hardhat verify --network ${(await ethers.provider.getNetwork()).name} ${tokenAddress} ${paymasterAddress}`);

    console.log("\n✨ Deployment complete!");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });
