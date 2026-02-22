import { ethers } from "hardhat";
import * as dotenv from "dotenv";
dotenv.config();

// New Mainnet Deployed Addresses (Base)
const NEW_DAIM_TOKEN_ADDRESS = "0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2";
const NEW_AGENT_REGISTRY_ADDRESS = "0xF720826C02AAfaEC56959387d61efA501eB1E56e";
const NEW_TASK_BUFFER_ADDRESS = "0x68F71c8dd0f056001dB59f34f28eDa92bb15e4B5";

async function main() {
    const signers = await (ethers as any).getSigners();
    let deployer: any;
    const pk = process.env.DEPLOYER_PRIVATE_KEY;

    if (pk) {
        deployer = new (ethers as any).Wallet(pk, (ethers as any).provider);
    } else if (signers && signers.length > 0) {
        deployer = signers[0];
    } else {
        console.error("❌ The DEPLOYER_PRIVATE_KEY was not found.");
        process.exit(1);
    }

    // The user's bot wallet
    const BOT_WALLET_ADDRESS = "0x68E07b77EbceBba538d38eA901E7d8d212A9FE6F";
    const botPk = process.env.BOT_PRIVATE_KEY;

    console.log("-----------------------------------------");
    console.log("   MIGRATION: FUND & REGISTER BOT WALLET ");
    console.log("-----------------------------------------");
    console.log(`Treasury Wallet: ${deployer.address}`);
    console.log(`Bot Wallet: ${BOT_WALLET_ADDRESS}`);

    const daimToken = await ethers.getContractAt("DaimToken", NEW_DAIM_TOKEN_ADDRESS);
    const agentRegistry = await ethers.getContractAt("AgentRegistry", NEW_AGENT_REGISTRY_ADDRESS);
    const taskBuffer = await ethers.getContractAt("QuantumTaskBuffer", NEW_TASK_BUFFER_ADDRESS);

    // 1. Transfer DAIM from Deployer -> Bot
    console.log("\n🔸 Step 1: Transferring new DAIM tokens to Bot Wallet...");
    const transferAmount = ethers.parseEther("200"); // 100 for staking, 100 for tasks

    const currentBotBalance = await daimToken.balanceOf(BOT_WALLET_ADDRESS);
    console.log(`Current Bot DAIM Balance: ${ethers.formatEther(currentBotBalance)}`);

    if (currentBotBalance < ethers.parseEther("150")) {
        try {
            const tx1 = await daimToken.connect(deployer).transfer(BOT_WALLET_ADDRESS, transferAmount);
            await tx1.wait(1);
            console.log(`✅ Successfully sent 200 DAIM to ${BOT_WALLET_ADDRESS}. Tx: ${tx1.hash}`);
        } catch (e: any) {
            console.error("❌ Failed to transfer DAIM:", e.message);
            // Don't exit here, maybe the user funded it already
        }
    } else {
        console.log("✅ Bot already has sufficient DAIM balance. Skipping transfer.");
    }

    if (!botPk) {
        console.log("\n⚠️ BOT_PRIVATE_KEY not found in .env. Skipping the auto-registration step.");
        console.log("The bot wallet has been funded 200 DAIM! It can now hit the /api/vouch endpoint on its own or run its normal registration flow.");
        return;
    }

    // 2. Register Bot on New AgentRegistry
    const botWallet = new (ethers as any).Wallet(botPk, (ethers as any).provider);
    console.log("\n🔸 Step 2: Registering Bot on New AgentRegistry...");

    try {
        const isReg = (await agentRegistry.agents(botWallet.address)).isRegistered;
        if (isReg) {
            console.log("✅ Bot is already registered on the new registry!");
        } else {
            // Approve DAIM for staking
            console.log("Approving 100 DAIM for staking...");
            const approveTx = await daimToken.connect(botWallet).approve(NEW_AGENT_REGISTRY_ADDRESS, ethers.parseEther("100"));
            await approveTx.wait(1);

            // Register
            console.log("Registering on-chain...");
            const regTx = await agentRegistry.connect(botWallet).register("https://bot-a2a.net/api", 1, "0x");
            await regTx.wait(1);
            console.log("✅ Successfully registered bot out on new AgentRegistry!");
        }
    } catch (e: any) {
        console.error("❌ Failed to register bot:", e.message);
    }

    main().catch((error) => {
        console.error(error);
        process.exitCode = 1;
    });
