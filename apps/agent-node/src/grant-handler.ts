// import { VCHandler } from '@swimmingkiim/trust-sdk'; // Moved to dynamic import or injection
// import { grantService } from './grant.js'; // Moved to injection

export interface GrantDependencies {
  db: any;
  vcHandler?: any; // Instance or class? Let's say instance for simplicity in mocking
  grantService?: any;
}

export const handleGrantRequest = async (req: any, res: any, dbOrDeps: any) => {
  // Backward compatibility or dependency injection support
  let db: any;
  let deps: GrantDependencies;

  if (dbOrDeps && dbOrDeps.query) {
    db = dbOrDeps;
    deps = { db };
  } else {
    deps = dbOrDeps || {};
    db = deps.db;
  }

  if (!db) {
    res.status(503).json({ error: "Database not initialized" });
    return;
  }

  // Load dependencies (Default to real ones if not injected)
  let service = deps.grantService;
  if (!service) {
    try {
      const module = await import("./grant.js");
      service = module.grantService;
    } catch (e) {
      console.warn("Failed to load grant service:", e);
    }
  }

  if (!service || !service.isEnabled()) {
    res.status(503).json({ error: "Grant service is disabled (No Wallet Configured)" });
    return;
  }

  try {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return res.status(401).json({ error: "Missing Bearer Token (VC)" });
    }

    const jwt = authHeader.split(" ")[1];

    // 1. Verify Credential
    let verified = false;
    let payload: any = {};

    if (deps.vcHandler) {
      // Mock usage
      verified = await deps.vcHandler.verifyCredential(jwt);
      // In mock, we might need payload too?
      // Let's assume the mock verification just returns true/false
      // And we decode payload manually as before.
    } else {
      // Real usage
      const { VCHandler } = await import("@swimmingkiim/trust-sdk");
      const vcHandler = new VCHandler();
      verified = await vcHandler.verifyCredential(jwt);
    }

    if (!verified) {
      return res.status(401).json({ error: "Invalid Credential Signature" });
    }

    // Decode to get claims
    payload = JSON.parse(Buffer.from(jwt.split(".")[1], "base64").toString());

    const issuerDid = payload.iss;
    const walletAddress = payload.vc?.credentialSubject?.walletAddress;

    if (!walletAddress) {
      return res.status(400).json({ error: 'Credential missing "walletAddress" claim' });
    }

    // 2. Check if Project is Registered
    const projectRes = await db.query("SELECT * FROM projects WHERE owner_did = $1", [issuerDid]);
    if (projectRes.rows.length === 0) {
      return res.status(403).json({ error: "DID is not a registered project" });
    }

    // 3. Anti-Sybil Checks (DB Constraints)
    // Check if DID already claimed
    const didCheck = await db.query("SELECT * FROM developer_grants WHERE did = $1", [issuerDid]);
    if (didCheck.rows.length > 0) {
      return res.status(409).json({ error: "Grant already claimed for this DID" });
    }

    // Check if Wallet already claimed
    const walletCheck = await db.query("SELECT * FROM developer_grants WHERE wallet_address = $1", [
      walletAddress,
    ]);
    if (walletCheck.rows.length > 0) {
      return res.status(409).json({ error: "Grant already claimed for this Wallet Address" });
    }

    // 4. Send Grant
    console.log(`[API] Processing Grant for ${issuerDid} -> ${walletAddress}`);
    const txHash = await service.sendGrant(walletAddress);

    // 5. Record in DB
    await db.query(
      "INSERT INTO developer_grants (did, wallet_address, tx_hash) VALUES ($1, $2, $3)",
      [issuerDid, walletAddress, txHash],
    );

    res.status(200).json({
      success: true,
      message: "Grant sent!",
      txHash,
    });
  } catch (error: any) {
    console.error("[API] Grant Error:", error);
    res.status(500).json({ error: error.message || "Internal Server Error" });
  }
};
