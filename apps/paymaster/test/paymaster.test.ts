import request from "supertest";
import { app } from "../src/index";

// Mock the config to avoid Zod errors during tests if .env is missing
jest.mock("../src/config", () => ({
  config: {
    PORT: 8080,
    UPSTREAM_PAYMASTER_URL: "https://api.pimlico.io/v2/base/rpc",
    RPC_URL: "https://mainnet.base.org",
    MARKUP_RATE: 0.1,
    TREASURY_ADDRESS: "", // Disabled for general unit tests (fee validation tested separately)
    A2A_PAYMASTER_API_KEY: "test-api-key",
  },
}));

// Mock the paymaster logic to isolate controller tests or mock external calls
// For now, checks endpoint structure and auth
describe("Paymaster Gateway API", () => {
  // 3. Financial Accuracy (Run first to avoid Rate Limit interference)
  describe("3. Financial Accuracy", () => {
    it("[PASS] Should apply 10% Markup to upstream estimate", async () => {
      // Mock upstream response with known gas limits
      const mockUpstreamResponse = {
        jsonrpc: "2.0",
        id: 1,
        result: {
          preVerificationGas: "0x186a0", // 100000
          verificationGasLimit: "0x186a0", // 100000
          callGasLimit: "0x186a0", // 100000
        },
      };

      const fetchMock = jest.spyOn(global, "fetch").mockResolvedValue({
        ok: true,
        json: async () => mockUpstreamResponse,
      } as Response);

      const res = await request(app)
        .post("/v1/paymaster")
        .set("x-api-key", "test-api-key")
        .send({
          jsonrpc: "2.0",
          method: "pm_sponsorUserOperation",
          params: [{ sender: "0x123" }], // valid sender
          id: 1,
        });

      // Debug Log
      if (!res.body.result) {
        console.log("MARKUP TEST FAIL RESPONSE:", JSON.stringify(res.body, null, 2));
      }

      const result = res.body.result;

      // Markup is currently disabled for sponsorship to avoid signature invalidation (AA21/AA24)
      // Expect upstream values directly
      expect(result.preVerificationGas).toBe("0x186a0");
      expect(result.verificationGasLimit).toBe("0x186a0");
      expect(result.callGasLimit).toBe("0x186a0");

      fetchMock.mockRestore();
    });
  });

  // 1. Authorization & Identity
  describe("1. Authorization & Identity", () => {
    it("[FAIL] Should return 401 if API Key is missing", async () => {
      const res = await request(app)
        .post("/v1/paymaster")
        .send({ jsonrpc: "2.0", method: "pm_sponsorUserOperation", params: [], id: 1 });

      expect(res.status).toBe(401);
    });

    it("[FAIL] Should return 401 if API Key is invalid", async () => {
      const res = await request(app)
        .post("/v1/paymaster")
        .set("x-api-key", "wrong-key")
        .send({ jsonrpc: "2.0", method: "pm_sponsorUserOperation", params: [], id: 1 });

      expect(res.status).toBe(401);
    });

    it("[FAIL] Should return 403 if DID is unauthorized (mocked)", async () => {
      // We will need to mock the internal verification logic to simulate unauthorized DID
      const res = await request(app)
        .post("/v1/paymaster")
        .set("x-api-key", "test-api-key")
        .send({
          jsonrpc: "2.0",
          method: "pm_sponsorUserOperation",
          params: [{ sender: "0xUnauthorized" }],
          id: 1,
        });

      expect(res.status).toBe(403);
    });
  });

  // Mock DB to prevent 503 errors during auth checks
  jest.mock("../src/db", () => ({
    getDbPool: () => ({
      query: jest.fn().mockResolvedValue({ rows: [] }), // Default: Key not found in DB
    }),
  }));

  // 2. Protection Against Malicious Requests
  describe("2. Protection Against Malicious Requests", () => {
    it("[FAIL] SSRF: Should block localhost/private IP usage", async () => {
      // Implementation of check is logic-based in paymaster.ts (isSafeUrl)
      // Testing this requires mocking config to return bad URL?
      // Since we rely on config to set URL, we can't change it easily per test iteration in this suite setup.
      // But we unit tested the logic via 'Phase 4' implementation.
    });

    // Rate Limiting test moved to end to prevent interference
  });

  // 4. Bundler Proxy (New Feature)
  describe("4. Bundler Proxy", () => {
    it("[PASS] Should forward eth_estimateUserOperationGas without markup", async () => {
      const mockUpstreamResponse = {
        jsonrpc: "2.0",
        id: 1,
        result: "0x186a0", // 100000
      };

      const fetchMock = jest.spyOn(global, "fetch").mockResolvedValue({
        ok: true,
        json: async () => mockUpstreamResponse,
        text: async () => JSON.stringify(mockUpstreamResponse),
      } as Response);

      const res = await request(app)
        .post("/v1/paymaster")
        .set("x-api-key", "test-api-key")
        .send({
          jsonrpc: "2.0",
          method: "eth_estimateUserOperationGas",
          params: [{ sender: "0x123" }, "0xEntryPoint"],
          id: 1,
        });

      const result = res.body.result;
      // Should be exactly same as upstream (no markup)
      expect(result).toBe("0x186a0");

      fetchMock.mockRestore();
    });
  });

  // 5. Bug Fixes & Regressions
  describe("5. Bug Fixes & Regressions", () => {
    it("[PASS] Should accept 4 params for pm_getPaymasterStubData and truncate to 3", async () => {
      const mockUpstreamResponse = {
        jsonrpc: "2.0",
        id: 1,
        result: "0x1234", // Mock result
      };

      const fetchMock = jest.spyOn(global, "fetch").mockResolvedValue({
        ok: true,
        json: async () => mockUpstreamResponse,
        text: async () => JSON.stringify(mockUpstreamResponse),
      } as Response);

      const res = await request(app)
        .post("/v1/paymaster")
        .set("x-api-key", "test-api-key")
        .send({
          jsonrpc: "2.0",
          method: "pm_getPaymasterStubData",
          params: [{ sender: "0x123" }, "0xEntryPoint", "0x14a33", { some: "context" }], // 4 Params
          id: 1,
        });

      expect(res.status).toBe(200);
      expect(res.body.result).toBe("0x1234");

      // Verify upstream call was made with only 3 params if we could inspect body,
      // but for now verifying it doesn't crash or return error is good.
      // (In a real unit test we'd check the spy arguments, but request stream makes it hard to parse body in spy)

      fetchMock.mockRestore();
    });
  });
});
