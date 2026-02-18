import { config } from "../config";
import { PaymasterContext } from "../types";
import { RateLimiter } from "./rate-limiter";

export class AuthService {
  private rateLimiter: RateLimiter;

  constructor() {
    // Rate Limiter: 10 requests per 10 seconds (default)
    this.rateLimiter = new RateLimiter(10, 10000);
  }

  async verifyRequest(context: PaymasterContext | undefined, params: any[]): Promise<string> {
    let authorizedDid = "Admin";
    const apiKey = context?.apiKey;
    let isAuthenticated = false;

    // 1. Static Key Check (Admin/Legacy)
    if (config.A2A_PAYMASTER_API_KEY && apiKey === config.A2A_PAYMASTER_API_KEY) {
      isAuthenticated = true;
    }

    // 2. Dynamic Key Check (DB)
    if (!isAuthenticated && apiKey) {
      // Lazy load DB logic to match original implementation
      // Need to handle DB dependency injection better in future, but keeping it simple for now or importing getDbPool
      const { getDbPool } = require("../db");

      try {
        const pool = getDbPool();
        const res = await pool.query("SELECT did, is_active FROM api_keys WHERE api_key = $1", [
          apiKey,
        ]);

        if (res.rows.length > 0 && res.rows[0].is_active) {
          isAuthenticated = true;
          authorizedDid = res.rows[0].did;

          // Async update usage count (fire and forget)
          pool
            .query("UPDATE api_keys SET usage_count = usage_count + 1 WHERE api_key = $1", [apiKey])
            .catch(console.error);
        }
      } catch (dbError) {
        console.error("[Auth] DB Connection Failed:", dbError);
        throw new Error("Service Unavailable: DB Connection Failed");
      }
    }

    if (!isAuthenticated) {
      console.warn(`[Auth] Invalid API Key: ${apiKey}`);
      throw new Error(`Unauthorized: Invalid API Key.`);
    }

    // 3. Rate Limiting
    const limitKey = context?.apiKey || context?.clientIp || "unknown";
    if (this.rateLimiter.isRateLimited(limitKey)) {
      throw new Error("Too Many Requests");
    }

    // 4. Request Verification (DID check placeholder)
    const userOp = params[0];
    if (userOp?.sender === "0xUnauthorized") {
      throw new Error("Forbidden: Unauthorized DID");
    }

    return authorizedDid;
  }
}
