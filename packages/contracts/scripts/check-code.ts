import { ethers } from "hardhat";

async function main() {
    const target = "0x2dCDEA8a708f1FDECA5e2E59d4cb70Bd2E9BdEC8";
    console.log("Checking Target:", target);

    const provider = new ethers.JsonRpcProvider("https://mainnet.base.org");
    const code = await provider.getCode(target);

    if (code === "0x") {
        console.log("👉 Type: EOA (Regular Wallet) - No Code");
    } else {
        console.log("👉 Type: CONTRACT");
        console.log("   Length:", code.length);
    }
}

main().catch(console.error);
