import { Router, Request, Response } from "express";
import { verifyMessage } from "viem";
import { getDbPool } from "../db";
import crypto from "crypto";

const router: Router = Router();

// Message that user must sign
const getSignMessage = (did: string, timestamp: number) =>
  `Register A2A Paymaster for ${did} at ${timestamp}`;



// Verification Logic
async function verifyApi(url: string): Promise<{ valid: boolean; reason?: string }> {
  try {
    // 1. HTTPS Check
    if (!url.startsWith("https://")) {
      return { valid: false, reason: "URL must start with https://" };
    }

    // 2. Root Check
    const rootRes = await fetch(`${url}/`);
    if (!rootRes.ok) {
      return { valid: false, reason: `Root ${url}/ returned ${rootRes.status}` };
    }

    // 3. llms.txt Check
    const llmsRes = await fetch(`${url}/llms.txt`);
    if (!llmsRes.ok) {
      return { valid: false, reason: `llms.txt at ${url}/llms.txt returned ${llmsRes.status}` };
    }
    const llmsText = await llmsRes.text();
    if (!llmsText || llmsText.trim().length === 0) {
      return { valid: false, reason: "llms.txt is empty" };
    }

    // 4. Manifest Check (.well-known/ai-plugin.json)
    const manifestRes = await fetch(`${url}/.well-known/ai-plugin.json`);
    if (!manifestRes.ok) {
      return {
        valid: false,
        reason: `Manifest at ${url}/.well-known/ai-plugin.json returned ${manifestRes.status}`,
      };
    }
    const manifest = await manifestRes.json();
    const requiredFields = ["name_for_human", "description_for_human", "api"];
    for (const field of requiredFields) {
      if (!manifest[field]) {
        return { valid: false, reason: `Manifest missing field: ${field}` };
      }
    }

    // 5. Route Check (Simple Reachability)
    // We expect manifest.api to have 'url' pointing to OpenAPI spec
    if (manifest.api && manifest.api.url) {
      const specRes = await fetch(manifest.api.url);
      if (!specRes.ok) {
        return {
          valid: false,
          reason: `OpenAPI spec at ${manifest.api.url} unreachable (${specRes.status})`,
        };
      }
      // Ideally we parse spec and check a GET route, but for MVP we check spec existence
      // OR if user provided a specific status endpoint in manifest (not standard but useful)
      // Let's check if the root url itself is a valid "service" by expecting 200 on root which we already did.
      // Strict check: Try to fetch the OpenAPI spec content.
      const specContent = await specRes.text();
      if (!specContent || specContent.length < 10) {
        return { valid: false, reason: "OpenAPI spec seems empty" };
      }
    } else {
      return { valid: false, reason: "Manifest missing api.url" };
    }

    return { valid: true };
  } catch (error: any) {
    return { valid: false, reason: `Verification failed: ${error.message}` };
  }
}



router.post("/register", async (req: Request, res: Response) => {
  try {
    const { did, signature, timestamp, apiUrl } = req.body;

    if (!did || !signature || !timestamp) {
      return res.status(400).json({ error: "Missing did, signature, or timestamp" });
    }

    // 1. Verify Timestamp (prevent replay attacks, allow 5 min window)
    const now = Date.now();
    if (Math.abs(now - timestamp) > 5 * 60 * 1000) {
      return res.status(400).json({ error: "Timestamp expired or invalid" });
    }

    // 2. Extract Address from DID (Assuming did:pkh or did:ethr)
    // Format: did:pkh:eip155:1:0x123... or did:ethr:0x123...
    // Simple extraction for MVP
    const parts = did.split(":");
    const addressPart = parts.find((p: string) => p.startsWith("0x"));

    if (!addressPart || addressPart.length !== 42) {
      return res
        .status(400)
        .json({ error: "Unsupported DID format. Must contain Ethereum address." });
    }

    // 3. Verify Signature
    const message = getSignMessage(did, timestamp);
    const valid = await verifyMessage({
      address: addressPart as `0x${string}`,
      message: message,
      signature: signature as `0x${string}`,
    });

    if (!valid) {
      return res.status(401).json({ error: "Invalid Signature" });
    }

    // 4. [NEW] Verify API if provided
    if (apiUrl) {
      console.log(`🔍 Verifying API: ${apiUrl}`);
      const verification = await verifyApi(apiUrl);
      if (!verification.valid) {
        return res.status(400).json({ error: `API Verification Failed: ${verification.reason}` });
      }
      console.log("✅ API Verified Successfully");
    }

    // 5. Generate API Key
    const apiKey = crypto.randomBytes(32).toString("hex");

    // 6. Store in DB
    const client = await getDbPool().connect();
    try {
      await client.query(
        `INSERT INTO api_keys (did, api_key) VALUES ($1, $2)
                 ON CONFLICT (did) DO UPDATE SET api_key = ($2), updated_at = NOW()`,
        [did, apiKey],
      );
    } finally {
      client.release();
    }

    console.log(`✅ Registered API Key for DID: ${did}`);

    return res.json({
      success: true,
      did,
      apiKey,
      message: "Keep this key safe! It will not be shown again.",
    });
  } catch (error: any) {
    console.error("Registration Error:", error);
    return res.status(500).json({ error: "Internal Server Error", details: error.message });
  }
});

export { router as registerRouter };
