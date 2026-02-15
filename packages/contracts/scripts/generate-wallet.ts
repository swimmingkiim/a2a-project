import { ethers } from "hardhat";

async function main() {
    const wallet = ethers.Wallet.createRandom();
    console.log(JSON.stringify({
        address: wallet.address,
        privateKey: wallet.privateKey
    }));
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
