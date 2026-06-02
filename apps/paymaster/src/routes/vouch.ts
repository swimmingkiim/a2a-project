import { Router } from "express";
import { createPublicClient, http, createWalletClient } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { base } from "viem/chains";

const router: any = Router();

// Rate limiting store (resets on deploy — acceptable for now)
const rateStore = new Map<string, { count: number; resetAt: number }>();
const RATE_MAX = 5;
const RATE_WINDOW = 60 * 60 * 1000; // 1 hour

function allow(key: string): boolean {
  const now = Date.now();
  const cur = rateStore.get(key);
  if (!cur || now > cur.resetAt) {
    rateStore.set(key, { count: 1, resetAt: now + RATE_WINDOW });
    return true;
  }
  if (cur.count >= RATE_MAX) return false;
  cur.count++;
  return true;
}

// ── Blacklist ──────────────────────────────────
const BLACKLIST = new Set<string>([
  // Known malicious addresses — add as needed
]);

// ── Contract addresses ──────────────────────────
const VERIFIER = "0xc173A512b3394f6897F9B20c7A411B5247BCeD19";
const REGISTRY = "0xF720826C02AAfaEC56959387d61efA501eB1E56e";

const verifierAbi = [{
  name: "isVerified",
  type: "function",
  inputs: [{ name: "agent", type: "address" }],
  outputs: [{ name: "", type: "bool" }],
  stateMutability: "view",
}] as const;

const registryAbi = [{
  name: "isRegistered",
  type: "function",
  inputs: [{ name: "agent", type: "address" }],
  outputs: [{ name: "", type: "bool" }],
  stateMutability: "view",
}] as const;

// ── POST /v1/vouch ─────────────────────────────
router.post("/vouch", async (req: any, res: any) => {
  const { walletAddress, did, description } = req.body || {};
  const clientIp = req.ip || req.socket?.remoteAddress || "unknown";

  // Validation
  if (!walletAddress || !/^0x[a-fA-F0-9]{40}$/.test(walletAddress)) {
    return res.status(400).json({ ok: false, reason: "Invalid wallet address", code: "INVALID_ADDRESS" });
  }
  if (!did || typeof did !== "string" || did.length < 3) {
    return res.status(400).json({ ok: false, reason: "DID is required (min 3 chars)", code: "INVALID_DID" });
  }

  const addr = walletAddress.toLowerCase();

  // Rate limit
  if (!allow(clientIp) || !allow(`w:${addr}`)) {
    return res.status(429).json({ ok: false, reason: "Rate limit — try again later.", code: "RATE_LIMIT" });
  }

  // Blacklist
  if (BLACKLIST.has(addr)) {
    return res.status(403).json({ ok: false, reason: "This address has been flagged.", code: "BLACKLISTED" });
  }

  try {
    const publicClient = createPublicClient({ chain: base, transport: http() });

    // Check if already registered
    const alreadyRegistered = await publicClient.readContract({
      address: REGISTRY,
      abi: registryAbi,
      functionName: "isRegistered",
      args: [addr as `0x${string}`],
    }).catch(() => false);

    if (alreadyRegistered) {
      return res.json({ ok: false, reason: "This address is already registered.", code: "ALREADY_REGISTERED" });
    }

    // Check CredentialVerifier (informational only — does not reject)
    const isVerified = await publicClient.readContract({
      address: VERIFIER,
      abi: verifierAbi,
      functionName: "isVerified",
      args: [addr as `0x${string}`],
    }).catch(() => null);

    if (isVerified === false) {
      console.log(`[VOUCH] ⚠️ ${addr} not verified on CredentialVerifier — vouch still issued`);
    }

    // Sign
    const voucherKey = process.env.VOUCHER_PRIVATE_KEY;
    if (!voucherKey) {
      return res.status(500).json({ ok: false, reason: "Voucher not configured", code: "CONFIG_ERROR" });
    }

    const account = privateKeyToAccount(voucherKey as `0x${string}`);

    const walletClient = createWalletClient({
      chain: base,
      transport: http(),
      account,
    });

    const message = `A2A Protocol Vouch for ${addr} (${did})`;
    const signature = await walletClient.signMessage({ message });

    console.log(`[VOUCH] ✅ ${addr} ${did} — ${description || "(no desc)"}`);

    return res.json({
      ok: true,
      signature,
      voucherAddress: account.address,
      message,
      nextStep: "Use trust-sdk.register({ did, walletAddress, signature, paymasterUrl: paymaster-service-production.up.railway.app })",
    });
  } catch (err: any) {
    console.error("[VOUCH]", err);
    return res.status(500).json({ ok: false, reason: "Internal error", code: "SERVER_ERROR" });
  }
});

export { router as vouchRouter };
