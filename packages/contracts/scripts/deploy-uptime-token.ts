import { ethers } from "hardhat";

async function main() {
    console.log("\n===================================================");
    console.log("🪙  PART 1: DAIM TOKEN DEPLOYMENT (EPHEMERAL) 🪙");
    console.log("===================================================\n");

    // 1. Generate Ephemeral Wallet (In-Memory)
    const randomWallet = ethers.Wallet.createRandom();
    const ephemeralAddress = randomWallet.address;
    const provider = ethers.provider;
    const deployer = randomWallet.connect(provider);

    console.log("1️⃣  EPHEMERAL WALLET GENERATED");
    console.log("   Address:     ", ephemeralAddress);
    console.log("   Private Key:  [HIDDEN]");

    // 2. Wait for Funds
    console.log("\n2️⃣  WAITING FOR GAS");
    console.log("   Action: Send approx 0.002 ETH to the address above.");
    console.log("   Status: Waiting for balance > 0.001 ETH...");

    let balance = await provider.getBalance(ephemeralAddress);
    const REQUIRED_BALANCE = ethers.parseEther("0.001");

    process.stdout.write("   Polling");
    while (balance < REQUIRED_BALANCE) {
        await new Promise(r => setTimeout(r, 5000));
        balance = await provider.getBalance(ephemeralAddress);
        process.stdout.write(".");
    }
    // Config
    const TREASURY_ADDRESS = process.env.TREASURY_ADDRESS || "0xED314144920B7b0cC148947c4B458D220010aC90";
    const TOKEN_NAME = process.env.TOKEN_NAME || "Daim Token";
    const TOKEN_SYMBOL = process.env.TOKEN_SYMBOL || "DAIM";

    console.log("   Target Treasury:", TREASURY_ADDRESS);
    console.log("   Token Identity: ", `${TOKEN_NAME} ($${TOKEN_SYMBOL})`);

    // 3. Deploy Token
    console.log(`\n🚀 DEPLOYING ${TOKEN_NAME}...`);
    const TokenFactory = await ethers.getContractFactory("DaimToken", deployer);
    // Arguments: name, symbol, initial_minter(deployer)
    const daimToken = await TokenFactory.deploy(TOKEN_NAME, TOKEN_SYMBOL, deployer.address);
    await daimToken.waitForDeployment();
    const tokenAddr = await daimToken.getAddress();
    console.log(`   -> ${TOKEN_NAME} Address:`, tokenAddr);

    // 4. Minting & Handover
    console.log("\n🔒 EXECUTING TOKEN HANDOVER...");

    // Mint 50M
    const MINT_AMOUNT = ethers.parseEther("50000000");
    console.log(`   [Mint] 50M ${TOKEN_SYMBOL} -> Treasury`);
    await (await daimToken.mint(TREASURY_ADDRESS, MINT_AMOUNT)).wait();

    // Roles
    const DEFAULT_ADMIN_ROLE = await daimToken.DEFAULT_ADMIN_ROLE();
    const MINTER_ROLE = await daimToken.MINTER_ROLE();

    console.log(`   [Roles] Transferring Admin/Minter to Treasury...`);
    await (await daimToken.grantRole(DEFAULT_ADMIN_ROLE, TREASURY_ADDRESS)).wait();
    await (await daimToken.grantRole(MINTER_ROLE, TREASURY_ADDRESS)).wait();

    console.log(`   [Roles] Renouncing Deployer Roles...`);
    await (await daimToken.renounceRole(MINTER_ROLE, deployer.address)).wait();
    await (await daimToken.renounceRole(DEFAULT_ADMIN_ROLE, deployer.address)).wait();

    console.log("\n-----------------------------------------");
    console.log("✅ PART 1 COMPLETE");
    console.log("-----------------------------------------");
    console.log("SAVE THIS ADDRESS FOR PART 2:");
    console.log("DaimToken:", tokenAddr);
    console.log("-----------------------------------------");
    console.log("Ephemeral Wallet Abandoned.");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
