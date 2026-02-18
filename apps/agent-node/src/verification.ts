import { ProjectSchema } from "@swimmingkiim/api-sdk";

export { ProjectSchema };

export const verifyProjectApi = async (apiUrl: string, ownerDid: string) => {
  const results: string[] = [];
  const errors: string[] = [];

  // Helper to fetch with timeout
  const fetchWithTimeout = async (url: string, options: any = {}) => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), 5000);
    try {
      const res = await fetch(url, { ...options, signal: controller.signal });
      return res;
    } finally {
      clearTimeout(id);
    }
  };

  // 1. Verify Manifest
  try {
    // Ensure no trailing slash for consistency
    const baseUrl = apiUrl.replace(/\/$/, "");
    const manifestUrl = `${baseUrl}/manifest.json`;

    const res = await fetchWithTimeout(manifestUrl);
    if (!res.ok) {
      throw new Error(`Failed to fetch manifest.json: ${res.status} ${res.statusText}`);
    }

    const manifest = (await res.json()) as any;
    if (!manifest.tools || !Array.isArray(manifest.tools)) {
      throw new Error('Invalid manifest: missing "tools" array');
    }
    results.push("✅ manifest.json verified");

    // 2. Verify MCP Endpoints (from manifest or default)
    // MCP endpoint (SSE) checks
    const ssePath = manifest.mcp && manifest.mcp.endpoint ? manifest.mcp.endpoint : "/sse";
    const sseUrl = ssePath.startsWith("http") ? ssePath : `${baseUrl}${ssePath}`;

    // Use HEAD or GET to check availability
    const sseRes = await fetchWithTimeout(sseUrl, { method: "GET" });
    if (sseRes.status !== 200 && sseRes.status !== 402) {
      // If it's 404/500/502/503/504 -> Fail
      if (sseRes.status >= 400 && sseRes.status !== 402 && sseRes.status !== 405) {
        throw new Error(`SSE endpoint check failed: ${sseRes.status} ${sseRes.statusText}`);
      }
    }
    results.push(`✅ SSE endpoint verified (${sseRes.status === 402 ? "Paid" : "Free"})`);
  } catch (e: any) {
    errors.push(`Manifest/API Check Failed: ${e.message}`);
  }

  // 3. Verify llms.txt
  try {
    const baseUrl = apiUrl.replace(/\/$/, "");
    const llmsUrl = `${baseUrl}/llms.txt`;
    const res = await fetchWithTimeout(llmsUrl);
    if (!res.ok) {
      throw new Error(`llms.txt unreachable: ${res.status} ${res.statusText}`);
    }
    results.push("✅ llms.txt verified");
  } catch (e: any) {
    errors.push(`Link Check Failed: ${e.message}`);
  }

  // 4. Verify DID (did:web only)
  if (ownerDid.startsWith("did:web:")) {
    try {
      const didParts = ownerDid.split(":");
      const domain = didParts[2];
      const path = didParts.slice(3).join("/");

      const didUrl = `https://${domain}/${path ? path + "/" : ""}.well-known/did.json`;

      const res = await fetchWithTimeout(didUrl);
      if (!res.ok) {
        throw new Error(`DID document unreachable at ${didUrl}: ${res.status}`);
      }
      const didDoc = (await res.json()) as any;
      if (didDoc.id !== ownerDid) {
        throw new Error(`DID Document ID mismatch. Found ${didDoc.id}, expected ${ownerDid}`);
      }
      results.push("✅ DID verified");
    } catch (e: any) {
      errors.push(`DID Verification Failed: ${e.message}`);
    }
  }

  if (errors.length > 0) {
    throw new Error(errors.join(", "));
  }

  console.log(`[VerifyProject] Success for ${apiUrl}:`, results);
  return results;
};
