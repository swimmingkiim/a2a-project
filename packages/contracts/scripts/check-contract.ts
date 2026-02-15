import { ethers } from "hardhat";

async function main() {
    const address = "0x8246a807bD699B214e02F5309e3E173C33E62a9B";
    const code = await ethers.provider.getCode(address);
    const isContract = code !== "0x";

    console.log(`Address: ${address}`);
    console.log(`Is Contract: ${isContract}`);
    console.log(`Code: ${code}`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
