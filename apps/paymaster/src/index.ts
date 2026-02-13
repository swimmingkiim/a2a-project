import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { handlePaymasterRequest } from './paymaster';
import { initDb } from './db';
import { registerRouter } from './routes/register';
import { config } from './config';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8080;

app.use(cors({
    origin: '*', // Allow all origins for Paymaster service (or restrict in production)
    allowedHeaders: ['Content-Type', 'Authorization', 'x-api-key']
}));
app.use(express.json());

// Mount Registration Route
app.use('/v1', registerRouter);

// JSON-RPC Endpoint
app.post('/v1/paymaster', async (req, res) => {
    // EMERGENCY SHUTDOWN CHECK
    if (config.DISABLE_PAYMASTER) {
        console.warn('🚨 [EMERGENCY] Paymaster is disabled. Rejecting request.');
        return res.status(503).json({
            jsonrpc: "2.0",
            error: {
                code: -32004,
                message: "Paymaster service temporarily disabled"
            },
            id: req.body.id || null
        });
    }

    try {
        const apiKey = req.get('x-api-key') || '';
        const clientIp = req.ip;

        // Create a masked copy of headers for logging
        const logHeaders = { ...req.headers };
        if (logHeaders['x-api-key']) {
            logHeaders['x-api-key'] = '********';
        }
        console.log('Headers:', JSON.stringify(logHeaders));

        const result = await handlePaymasterRequest(req.body, { apiKey, clientIp });

        let statusCode = 200;
        if (result.error) {
            switch (result.error.code) {
                case -32600: statusCode = 400; break;
                case -32001: statusCode = 401; break;
                case -32003: statusCode = 403; break;
                case -32002: statusCode = 429; break;
                case -32004: statusCode = 503; break;
                default: statusCode = 200;
            }
        }
        res.status(statusCode).json(result);
    } catch (error: any) {
        console.error('Paymaster Error:', error);
        res.status(500).json({
            jsonrpc: "2.0",
            error: {
                code: -32603,
                message: error.message || "Internal Error"
            },
            id: req.body.id || null
        });
    }
});


app.get('/health', (req, res) => {
    const status = {
        status: config.DISABLE_PAYMASTER ? 'disabled' : 'ok',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        environment: config.NODE_ENV,
        emergencyShutdown: config.DISABLE_PAYMASTER
    };

    const statusCode = config.DISABLE_PAYMASTER ? 503 : 200;
    res.status(statusCode).json(status);
});

app.get('/', (req, res) => {
    const documentation = `
# A2A Paymaster API

Welcome to the A2A Paymaster Service. This service provides gas sponsorship for AI Agents on Base L2.

## Endpoints

### 1. Register API Key
**POST** \`/v1/register\`

Generates a unique API Key for your DID. You must sign a timestamped message to prove ownership.

**Headers**:
- \`Content-Type: application/json\`

**Body**:
\`\`\`json
{
  "did": "did:pkh:eip155:1:0xYourAddress",
  "signature": "0x...", 
  "timestamp": 1700000000000
}
\`\`\`

**Signing Logic**:
1. Get current timestamp (ms).
2. Create message: \`Register A2A Paymaster for \${did} at \${timestamp}\`
3. Sign message with your wallet (EIP-191).

---

### 2. Sponsor Transaction (JSON-RPC)
**POST** \`/v1/paymaster\`

Standard ERC-7677 / Pimlico compatible Paymaster RPC.

**Headers**:
- \`Content-Type: application/json\`
- \`x-api-key: YOUR_API_KEY\`

**Body**:
\`\`\`json
{
  "jsonrpc": "2.0",
  "method": "pm_sponsorUserOperation",
  "params": [ userOp, entryPoint ],
  "id": 1
}
\`\`\`

---

## Contact
For support, contact the A2A Team.
`;
    res.setHeader('Content-Type', 'text/markdown; charset=utf-8');
    res.send(documentation.trim());
});

export { app };

if (require.main === module) {
    (async () => {
        try {
            // Initialize DB if configured
            if (process.env.DB_HOST || process.env.INSTANCE_CONNECTION_NAME) {
                await initDb();
            }
            app.listen(Number(PORT), '0.0.0.0', () => {
                console.log(`Paymaster Service running on port ${PORT}`);
                console.log(`Network: ${process.env.RPC_URL || 'Default (Check Config)'}`);
            });
        } catch (e) {
            console.error("Failed to start server:", e);
            process.exit(1);
        }
    })();
}
