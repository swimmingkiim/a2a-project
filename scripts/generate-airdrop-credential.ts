
import { VCHandler } from '@swimmingkiim/trust-sdk';
import { IdentityManager } from '@swimmingkiim/trust-sdk';

async function main() {
    const idManager = new IdentityManager();
    const vcHandler = new VCHandler();

    // 1. Create or Load Identity (Ephemeral for demo, normally you'd use existing DID)
    console.log("Creating/Loading Identity...");
    // ideally, load from local KMS if available, or create new ephemeral one
    // For this script, we'll create a new ephemeral DID (did:key) just to demonstrate.
    // In production, the bot would already HAVE a DID.
    const did = await idManager.createEphemeralDID();
    console.log(`Your DID: ${did.did}`);

    // 2. Define the Claims
    // The Airdrop requires proving you own a wallet address.
    const walletAddress = "0xYOUR_WALLET_ADDRESS_HERE"; // User should replace this

    console.log(`Generating VC for wallet: ${walletAddress}`);

    // 3. Issue Self-Signed Credential
    // Issuer = Subject = Your DID
    const vc = await vcHandler.createCredential(
        did.did,
        did.did,
        {
            walletAddress: walletAddress,
            project: "My Awesome Project"
        }
    );

    console.log("\n--- Verifiable Credential (JWT) ---");
    console.log(vc.proof.jwt);
    console.log("-----------------------------------\n");
    console.log("Use this JWT in the Authorization header or body for POST /api/airdrop");
}

main().catch(console.error);
