import assert from "assert";
import { handleGrantRequest, GrantDependencies } from "./src/grant-handler.js";

// Mock Grant Service
const mockGrantService = {
  isEnabled: () => true,
  sendGrant: async (to: string) => `0xMOCK_TX_HASH_FOR_${to}`,
};

// Mock VC Handler
const mockVcHandler = {
  verifyCredential: async (jwt: string) => true,
};

// Mock DB
const mockDb = {
  query: async (text: string, params: any[]) => {
    if (text.includes("SELECT * FROM projects")) {
      // Mock registered project
      if (params[0] === "did:web:test_project") {
        return { rows: [{ id: 1, owner_did: "did:web:test_project" }] };
      }
      return { rows: [] };
    }
    if (text.includes("SELECT * FROM developer_grants")) {
      // Mock existing claim
      if (params[0] === "did:web:already_claimed" || params[0] === "0xALREADY_CLAIMED") {
        return { rows: [{ id: 1 }] };
      }
      return { rows: [] };
    }
    if (text.includes("INSERT INTO developer_grants")) {
      return { rows: [] };
    }
    return { rows: [] };
  },
};

// Helper to generate mock VC JWT
function generateMockVC(iss: string, wallet: string) {
  const header = Buffer.from(JSON.stringify({ alg: "ES256", typ: "JWT" })).toString("base64");
  const payload = Buffer.from(
    JSON.stringify({
      iss: iss,
      vc: { credentialSubject: { walletAddress: wallet } },
    }),
  ).toString("base64");
  return `${header}.${payload}.signature`;
}

// Mock Response
function mockRes() {
  return {
    statusCode: 0,
    body: {} as any,
    status(code: number) {
      this.statusCode = code;
      return this;
    },
    json(body: any) {
      this.body = body;
      return this;
    },
  };
}

async function runTests() {
  console.log("🧪 Starting Grant Handler Tests...");

  // Test 1: Success
  {
    console.log("\nTest 1: Valid Request (Success)");
    const req = {
      headers: {
        authorization: `Bearer ${generateMockVC("did:web:test_project", "0xVALID_WALLET")}`,
      },
    };
    const res = mockRes();

    await handleGrantRequest(req, res, {
      db: mockDb,
      vcHandler: mockVcHandler,
      grantService: mockGrantService,
    });

    assert(res.statusCode === 200, "Should return 200");
    assert(res.body.success === true, "Should return success");
    console.log("✅ Passed");
  }

  // Test 2: Invalid DID (Not Registered)
  {
    console.log("\nTest 2: Unregistered Project (403)");
    const req = {
      headers: {
        authorization: `Bearer ${generateMockVC("did:web:unregistered", "0xVALID_WALLET")}`,
      },
    };
    const res = mockRes();

    await handleGrantRequest(req, res, {
      db: mockDb,
      vcHandler: mockVcHandler,
      grantService: mockGrantService,
    });

    assert(res.statusCode === 403, "Should return 403");
    console.log("✅ Passed");
  }

  // Test 3: Already Claimed DID
  {
    console.log("\nTest 3: Already Claimed DID (409)");
    const req = {
      headers: {
        authorization: `Bearer ${generateMockVC("did:web:already_claimed", "0xNEW_WALLET")}`,
      },
    };
    const res = mockRes();

    await handleGrantRequest(req, res, {
      db: mockDb,
      vcHandler: mockVcHandler,
      grantService: mockGrantService,
    });

    assert(res.statusCode === 409, "Should return 409");
    console.log("✅ Passed");
  }

  // Test 4: Missing Authorization
  {
    console.log("\nTest 4: Missing Auth Header (401)");
    const req = { headers: {} };
    const res = mockRes();

    await handleGrantRequest(req, res, {
      db: mockDb,
      vcHandler: mockVcHandler,
      grantService: mockGrantService,
    });

    assert(res.statusCode === 401, "Should return 401");
    console.log("✅ Passed");
  }
}

runTests().catch(console.error);
