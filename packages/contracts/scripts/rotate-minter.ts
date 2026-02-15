import { ethers } from "hardhat";

async function main() {
    const NEW_MINTER = process.env.NEW_MINTER_ADDRESS;
    const OLD_MINTER = process.env.OLD_MINTER_ADDRESS; // Optional, to revoke

    if (!NEW_MINTER) {
        console.error("❌ Error: NEW_MINTER_ADDRESS environment variable is not set.");
        process.exit(1);
    }

    // DaimToken Address (from DEPLOYED_ADDRESSES.md)
    const DAIM_TOKEN_ADDRESS = "0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2";

    console.log("🔄 Rotating DaimToken Minter Role...");
    console.log(`📍 Contract: ${DAIM_TOKEN_ADDRESS}`);
    console.log(`👤 New Minter: ${NEW_MINTER}`);
    if (OLD_MINTER) console.log(`🗑️  Old Minter (to revoke): ${OLD_MINTER}`);

    const [admin] = await ethers.getSigners();
    console.log(`🔑 Admin (Executor): ${admin.address}`);

    const daimToken = await ethers.getContractAt("DaimToken", DAIM_TOKEN_ADDRESS);
    const MINTER_ROLE = await daimToken.MINTER_ROLE();

    // 1. Grant Role to New Minter
    if (await daimToken.hasRole(MINTER_ROLE, NEW_MINTER)) {
        console.log("✅ New Minter already has the role.");
    } else {
        console.log("Tx: Granting MINTER_ROLE to new address...");
        const tx = await daimToken.grantRole(MINTER_ROLE, NEW_MINTER);
        await tx.wait();
        console.log(`✅ Role Granted! (Tx: ${tx.hash})`);
    }

    // 2. Revoke Role from Old Minter (if provided)
    if (OLD_MINTER) {
        if (await daimToken.hasRole(MINTER_ROLE, OLD_MINTER)) {
            console.log("Tx: Revoking MINTER_ROLE from old address...");
            const tx = await daimToken.revokeRole(MINTER_ROLE, OLD_MINTER);
            await tx.wait();
            console.log(`✅ Role Revoked! (Tx: ${tx.hash})`);
        } else {
            console.log("ℹ️  Old Minter does not have the role.");
        }
    }

    console.log("\n✨ Rotation Complete!");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
