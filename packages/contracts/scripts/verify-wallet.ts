import { ethers } from "ethers";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
    const pk = process.env.DEPLOYER_PRIVATE_KEY;
    if (!pk) {
        console.error("No Private Key found in .env");
        return;
    }
    const wallet = new ethers.Wallet(pk);
    console.log("Derived Address from .env PK:", wallet.address);
}

main();
