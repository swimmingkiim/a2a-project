
import { VCHandler, IdentityManager } from '@swimmingkiim/trust-sdk';

async function main() {
    const idManager = new IdentityManager();
    const vcHandler = new VCHandler();

    // 1. Create Identity (Ephemeral did:key — in-memory, no DB)
    console.log("Creating Identity...");
    const identity = await idManager.createEphemeralDID();
    console.log(`Your DID: ${identity.did}`);

    // 2. Define the Claims
    // The Grant requires proving you own a wallet address.
    const walletAddress = "0xYOUR_WALLET_ADDRESS_HERE"; // User should replace this

    console.log(`Generating VC for wallet: ${walletAddress}`);

    // 3. Issue Self-Signed Credential
    // Issuer = Subject = Your DID
    const vcJwt = await vcHandler.createCredential(
        identity.did,
        identity.did,
        {
            walletAddress: walletAddress,
            project: "My Awesome Project"
        },
        identity.keyPair  // signing key from createEphemeralDID()
    );

    console.log("\n--- Verifiable Credential (JWT) ---");
    console.log(vcJwt);
    console.log("-----------------------------------\n");
    console.log("Use this JWT in the Authorization header or body for POST /api/grant");
}

main().catch(console.error);
