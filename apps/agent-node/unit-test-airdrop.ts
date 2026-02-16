
import { handleAirdropRequest } from './src/airdrop-handler';

// Mocks
const mockReq = (headers: any = {}) => ({
    headers,
    body: {}
});

const mockRes = () => {
    const res: any = {};
    res.statusCode = 0;
    res.body = null;
    res.status = (code: number) => {
        res.statusCode = code;
        return res;
    };
    res.json = (data: any) => {
        res.body = data;
        return res;
    };
    return res;
};

const mockDb = (projects: any[] = [], airdrops: any[] = []) => ({
    query: async (sql: string, params: any[]) => {
        if (sql.includes('FROM projects')) {
            const found = projects.filter(p => p.owner_did === params[0]);
            return { rows: found };
        }
        if (sql.includes('FROM airdrops')) {
            if (sql.includes('WHERE did')) {
                const found = airdrops.filter(a => a.did === params[0]);
                return { rows: found };
            }
            if (sql.includes('WHERE wallet_address')) {
                const found = airdrops.filter(a => a.wallet_address === params[0]);
                return { rows: found };
            }
        }
        if (sql.includes('INSERT INTO airdrops')) {
            airdrops.push({ did: params[0], wallet_address: params[1], tx_hash: params[2] });
            return { rows: [] };
        }
        return { rows: [] };
    }
});

const mockService = (enabled = true) => ({
    isEnabled: () => enabled,
    sendAirdrop: async (to: string) => {
        return "0xMOCK_TX_HASH";
    }
});

const mockVcHandler = (valid = true) => ({
    verifyCredential: async (jwt: string) => {
        return valid;
    }
});

// Helper to create JWT
const createMockJwt = (did: string, wallet: string) => {
    const header = Buffer.from(JSON.stringify({ alg: 'ES256', typ: 'JWT' })).toString('base64');
    const payload = Buffer.from(JSON.stringify({
        iss: did,
        sub: did,
        vc: {
            credentialSubject: {
                walletAddress: wallet
            }
        }
    })).toString('base64');
    return `${header}.${payload}.SIGNATURE`;
};


async function runTests() {
    console.log("Running Airdrop Unit Tests...");

    // Test 1: No DB
    {
        const req = mockReq();
        const res = mockRes();
        await handleAirdropRequest(req, res, { db: null });
        console.assert(res.statusCode === 503, `Test 1 Failed: Expected 503, got ${res.statusCode}`);
        console.log("Test 1 Passed (No DB)");
    }

    // Test 2: Service Disabled
    {
        const db = mockDb();
        const req = mockReq();
        const res = mockRes();
        const deps = { db, airdropService: mockService(false) };
        await handleAirdropRequest(req, res, deps);
        console.assert(res.statusCode === 503, `Test 2 Failed: Expected 503, got ${res.statusCode}`);
        console.log("Test 2 Passed (Service Disabled)");
    }

    // Test 3: Successful Airdrop
    {
        const did = "did:web:example.com";
        const wallet = "0x123";
        const db = mockDb([{ owner_did: did }], []); // Registered project, no airdrops
        const req = mockReq({ authorization: `Bearer ${createMockJwt(did, wallet)}` });
        const res = mockRes();
        const deps = {
            db,
            airdropService: mockService(true),
            vcHandler: mockVcHandler(true)
        };

        await handleAirdropRequest(req, res, deps);

        if (res.statusCode !== 200) {
            console.error("Test 3 Failed Response:", res.body);
        }
        console.assert(res.statusCode === 200, `Test 3 Failed: Expected 200, got ${res.statusCode}`);
        console.assert(res.body.txHash === "0xMOCK_TX_HASH", "Test 3 Failed: TxHash mismatch");
        console.log("Test 3 Passed (Success Flow)");
    }

    // Test 4: Project Not Registered
    {
        const did = "did:web:unknown.com";
        const wallet = "0x456";
        const db = mockDb([], []); // Empty projects
        const req = mockReq({ authorization: `Bearer ${createMockJwt(did, wallet)}` });
        const res = mockRes();
        const deps = {
            db,
            airdropService: mockService(true),
            vcHandler: mockVcHandler(true)
        };

        await handleAirdropRequest(req, res, deps);
        console.assert(res.statusCode === 403, `Test 4 Failed: Expected 403, got ${res.statusCode}`);
        console.log("Test 4 Passed (Unregistered Project)");
    }

    // Test 5: Sybil Attack (Same DID)
    {
        const did = "did:web:example.com";
        const wallet = "0x789";
        const db = mockDb([{ owner_did: did }], [{ did: did, wallet_address: "0xOLD" }]); // Already claimed
        const req = mockReq({ authorization: `Bearer ${createMockJwt(did, wallet)}` });
        const res = mockRes();
        const deps = {
            db,
            airdropService: mockService(true),
            vcHandler: mockVcHandler(true)
        };

        await handleAirdropRequest(req, res, deps);
        console.assert(res.statusCode === 409, `Test 5 Failed: Expected 409, got ${res.statusCode}`);
        console.log("Test 5 Passed (Sybil DID)");
    }
}

runTests().catch(e => {
    console.error(e);
    process.exit(1);
});
