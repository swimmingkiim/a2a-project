/**
 * requestVouch — Obtain an on-chain vouch signature for AgentRegistry registration.
 *
 * Calls the A2A Vouch API (Railway-hosted Paymaster).
 * The API verifies your address against CredentialVerifier, checks rate limits,
 * and returns an EIP-712 vouch signature.
 *
 * @example
 * ```ts
 * import { requestVouch } from "@swimmingkiim/api-sdk";
 *
 * const vouch = await requestVouch({
 *   walletAddress: "0xYourAddress",
 *   did: "my-agent",
 *   description: "I write smart contracts for DeFi protocols",
 * });
 *
 * if (vouch.ok) {
 *   console.log("Signature:", vouch.signature);
 *   // Now call AgentRegistry.register() with this signature
 * }
 * ```
 */

export interface VouchRequest {
  walletAddress: string;
  did: string;
  description?: string;
}

export interface VouchResponse {
  ok: boolean;
  signature?: string;
  voucherAddress?: string;
  message?: string;
  nextStep?: string;
  reason?: string;
  code?: string;
}

const DEFAULT_VOUCH_URL = "https://paymaster-service-production.up.railway.app";

export async function requestVouch(
  req: VouchRequest,
  apiUrl: string = DEFAULT_VOUCH_URL
): Promise<VouchResponse> {
  const url = `${apiUrl.replace(/\/$/, "")}/v1/vouch`;

  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      walletAddress: req.walletAddress,
      did: req.did,
      description: req.description || "",
    }),
  });

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    return {
      ok: false,
      reason: body.reason || `HTTP ${resp.status}`,
      code: body.code || "HTTP_ERROR",
    };
  }

  return resp.json();
}
