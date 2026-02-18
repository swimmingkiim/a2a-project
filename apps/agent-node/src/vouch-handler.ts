import { z } from "zod";

/**
 * Vouch Handler — Issues EIP-712 attestation proofs for new agent registration.
 *
 * Uses the Bootstrap Voucher's private key (VOUCHER_PRIVATE_KEY) to sign attestations
 * after verifying the requester's VC (Verifiable Credential).
 *
 * Flow:
 *   1. Client submits VC JWT + wallet address
 *   2. Handler verifies VC via trust-sdk
 *   3. AttestationSigner creates EIP-712 signed proof
 *   4. Client uses proof to call AgentRegistry.register()
 */

// --- Input Validation ---
const VouchRequestSchema = z.object({
    /** Verifiable Credential JWT string (self-signed, contains DID + wallet) */
    vcJwt: z.string().min(10, "vcJwt is required"),
    /** Ethereum wallet address of the agent requesting registration */
    walletAddress: z
        .string()
        .regex(/^0x[a-fA-F0-9]{40}$/, "Invalid Ethereum address"),
});

// --- Constants ---
const VOUCHER_PRIVATE_KEY = process.env.VOUCHER_PRIVATE_KEY;
const CREDENTIAL_VERIFIER_ADDRESS =
    process.env.CREDENTIAL_VERIFIER_ADDRESS ||
    "0xc173A512b3394f6897F9B20c7A411B5247BCeD19";
const CHAIN_ID = Number(process.env.CHAIN_ID || "8453"); // Base Mainnet

/**
 * Handles POST /api/vouch requests.
 * Verifies VC and returns a signed attestation proof for on-chain registration.
 */
export const handleVouchRequest = async (req: any, res: any) => {
    if (!VOUCHER_PRIVATE_KEY) {
        return res.status(503).json({
            error: "Vouch service is disabled (VOUCHER_PRIVATE_KEY not configured)",
        });
    }

    try {
        // 1. Validate input
        const data = VouchRequestSchema.parse(req.body);

        // 2. Verify VC
        const { VCHandler } = await import("@swimmingkiim/trust-sdk");
        const vcHandler = new VCHandler();
        const verified = await vcHandler.verifyCredential(data.vcJwt);

        if (!verified) {
            return res.status(401).json({ error: "Invalid Credential Signature" });
        }

        // Decode JWT payload
        const payload = JSON.parse(
            Buffer.from(data.vcJwt.split(".")[1], "base64").toString(),
        );
        const issuerDid = payload.iss;
        const vcWallet = payload.vc?.credentialSubject?.walletAddress;

        // Verify wallet consistency: VC wallet must match request wallet
        if (
            vcWallet &&
            vcWallet.toLowerCase() !== data.walletAddress.toLowerCase()
        ) {
            return res.status(400).json({
                error: "Wallet address mismatch between VC and request",
            });
        }

        // 3. Create attestation
        const { AttestationSigner } = await import("@swimmingkiim/api-sdk");

        const formattedKey = VOUCHER_PRIVATE_KEY.startsWith("0x")
            ? VOUCHER_PRIVATE_KEY
            : `0x${VOUCHER_PRIVATE_KEY}`;

        const signer = new AttestationSigner({
            privateKey: formattedKey as `0x${string}`,
            verifierContractAddress: CREDENTIAL_VERIFIER_ADDRESS,
            chainId: CHAIN_ID,
            verifyVC: async (jwt: string) => {
                const valid = await vcHandler.verifyCredential(jwt);
                const p = JSON.parse(
                    Buffer.from(jwt.split(".")[1], "base64").toString(),
                );
                return { valid, did: p.iss };
            },
        });

        const proof = await signer.createAttestation(
            data.vcJwt,
            data.walletAddress,
        );

        console.log(
            `[Vouch] Attestation created for ${issuerDid} → ${data.walletAddress}`,
        );

        // 4. Return the encoded proof
        res.status(200).json({
            success: true,
            proof: proof.encode(),
            didHash: proof.didHash,
            deadline: proof.deadline.toString(),
            message:
                "Use this proof to call AgentRegistry.register(metadataUrl, resourceUnits, proof)",
        });
    } catch (error: any) {
        if (error.name === "ZodError") {
            return res.status(400).json({
                error: "Invalid request",
                details: error.errors,
            });
        }
        console.error("[Vouch] Error:", error);
        res.status(500).json({ error: error.message || "Internal Server Error" });
    }
};
