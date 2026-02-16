import { ethers } from "hardhat";

async function main() {
    const CONTRACT_ADDRESS = "0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2"; // DAIM
    const USER_ADDRESS = "0x77f83e1798B9E51aD259937202D2772Cf1cE9B59"; // From event log

    const DaimToken = await ethers.getContractAt("DaimToken", CONTRACT_ADDRESS);

    // 1. Verify Balance directly
    const balance = await DaimToken.balanceOf(USER_ADDRESS);
    console.log(`\nUser Address: ${USER_ADDRESS}`);
    console.log(`On-Chain Balance: ${ethers.formatUnits(balance, 18)} DAIM`);
    console.log(`Raw Balance: ${balance.toString()}`);

    if (balance > 0n) {
        console.log("✅ The user HAS the tokens on-chain.");
    } else {
        console.log("❌ The user has 0 tokens on-chain.");
    }
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});
