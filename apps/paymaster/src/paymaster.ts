

import { config } from './config';
import { JsonRpcRequest, JsonRpcResponse, PaymasterContext } from './types';
import { RateLimiter } from './security/rate-limiter';
import { isSafeUrl } from './security/ssrf';
import { createPublicClient, http, PublicClient, parseEther } from 'viem';

// Fee Validation
import { USDCFeeValidator } from './fee-validation/USDCFeeValidator';
import { DAIMFeeValidator } from './fee-validation/DAIMFeeValidator';
import { MockTokenPriceOracle } from './oracle/MockTokenPriceOracle';
import { IFeeValidator } from './fee-validation/IFeeValidator';

const client = createPublicClient({
    transport: http(config.RPC_URL)
});

// Initialize USDC Validator (always active)
const usdcValidator = new USDCFeeValidator({
    treasuryAddress: config.TREASURY_ADDRESS,
    usdcTokenAddress: config.FEE_TOKEN_ADDRESS,
    floorFeeAmount: config.FEE_AMOUNT,
    ethPriceUSD: config.ETH_PRICE_USD,
    markupRate: config.MARKUP_RATE
});

// Initialize DAIM Validator (conditional)
let daimValidator: IFeeValidator | null = null;
if (config.ENABLE_DAIM_FEES && config.DAIM_TOKEN_ADDRESS) {
    const oracle = new MockTokenPriceOracle(
        parseFloat(config.DAIM_PRICE_USD),
        parseFloat(config.ETH_PRICE_USD)
    );

    daimValidator = new DAIMFeeValidator({
        treasuryAddress: config.TREASURY_ADDRESS,
        daimTokenAddress: config.DAIM_TOKEN_ADDRESS,
        markupRate: config.MARKUP_RATE
    }, oracle);

    console.log(`✅ DAIM fee validation enabled (Token: ${config.DAIM_TOKEN_ADDRESS}, Price: $${config.DAIM_PRICE_USD})`);
} else {
    console.log(`ℹ️  DAIM fee validation disabled (ENABLE_DAIM_FEES=${config.ENABLE_DAIM_FEES})`);
}

// Helper to validate fee in UserOp using Strategy Pattern
async function validateFeeIncluded(userOp: any, client: PublicClient) {
    console.log(`[Fee Validation] Checking for embedded fee...`);

    // Try USDC validation first (default/legacy)
    const usdcValid = await usdcValidator.validateFeeIncluded(userOp, client);
    if (usdcValid) {
        console.log(`[Fee Validation] ✅ Valid USDC fee found`);
        return true;
    }

    // Try DAIM validation if enabled
    if (daimValidator) {
        const daimValid = await daimValidator.validateFeeIncluded(userOp, client);
        if (daimValid) {
            console.log(`[Fee Validation] ✅ Valid DAIM fee found`);
            return true;
        }
    }

    console.warn(`[Fee Validation] ❌ No valid fee found (tried: USDC${daimValidator ? ', DAIM' : ''})`);
    return false;
}

// Rate Limiter: 10 requests per 10 seconds for testing
const rateLimiter = new RateLimiter(10, 10000);

export async function handlePaymasterRequest(request: JsonRpcRequest, context?: PaymasterContext): Promise<JsonRpcResponse> {
    const { method, params, id } = request;

    console.log(`[Paymaster] Received request: ${method}`);

    // Basic Validation
    if (!method || !params) {
        return {
            jsonrpc: "2.0",
            error: { code: -32600, message: "Invalid Request" },
            id: id || null
        };
    }

    // Only allow specific methods
    const allowedMethods = [
        'pm_sponsorUserOperation',
        'pm_getPaymasterStubData',
        'pm_getPaymasterData',
        'eth_sendUserOperation',
        'eth_estimateUserOperationGas',
        'eth_getUserOperationReceipt',
        'eth_supportedEntryPoints',
        'eth_chainId',
        'net_version'
    ];

    if (!allowedMethods.includes(method)) {
        return {
            jsonrpc: "2.0",
            error: { code: -32601, message: "Method not found" },
            id: id
        };
    }



    try {
        let authorizedDid = 'Admin';

        // 1. Authentication (Static + Dynamic)
        const apiKey = context?.apiKey;
        let isAuthenticated = false;

        // A. Static Key Check (Admin/Legacy)
        if (config.A2A_PAYMASTER_API_KEY && apiKey === config.A2A_PAYMASTER_API_KEY) {
            isAuthenticated = true;
        }

        // B. Dynamic Key Check (DB)
        if (!isAuthenticated && apiKey) {
            const { getDbPool } = require('./db'); // Lazy load to avoid init issues if DB not used
            // Check if DB is configured (pool might throw if not, so we check env or try/catch)
            // Ideally getDbPool() handles it or we assume it's set if we are here.

            try {
                const pool = getDbPool();
                const res = await pool.query(
                    'SELECT did, is_active FROM api_keys WHERE api_key = $1',
                    [apiKey]
                );

                if (res.rows.length > 0 && res.rows[0].is_active) {
                    isAuthenticated = true;
                    authorizedDid = res.rows[0].did;

                    // Async update usage count (fire and forget)
                    pool.query('UPDATE api_keys SET usage_count = usage_count + 1 WHERE api_key = $1', [apiKey]).catch(console.error);
                }
            } catch (dbError) {
                console.error('[Auth] DB Connection Failed:', dbError);
                // [FIX] Return 503 instead of 401 so the client knows it's a server issue, not an invalid key
                throw new Error("Service Unavailable: DB Connection Failed");
            }
        }

        if (!isAuthenticated) {
            console.warn(`[Auth] Invalid API Key: ${apiKey}`);
            throw new Error(`Unauthorized: Invalid API Key.`);
        }

        // 2. Rate Limiting
        const limitKey = context?.apiKey || context?.clientIp || 'unknown';
        if (rateLimiter.isRateLimited(limitKey)) {
            throw new Error("Too Many Requests");
        }

        // 3. Request Verification (DID check placeholder)
        const userOp = params[0];
        if (userOp?.sender === '0xUnauthorized') {
            throw new Error("Forbidden: Unauthorized DID");
        }

        // [FEE VALIDATION] (Phase 5)
        // Check if the Treasury Fee is included in the UserOp
        // Only enforce this for sponsorship requests
        if (method === 'pm_sponsorUserOperation' && userOp) {
            // We can make this optional via config or per-DID in the future
            if (config.TREASURY_ADDRESS && config.TREASURY_ADDRESS !== '0x0000000000000000000000000000000000000000') {
                const hasFee = await validateFeeIncluded(userOp, client);
                if (!hasFee) {
                    throw new Error("Forbidden: Missing Treasury Fee Transfer");
                }
            }
        }

        // [FIX] Inject Gas Fees for eth_estimateUserOperationGas if missing
        if (method === 'eth_estimateUserOperationGas' && userOp) {
            if (!userOp.maxFeePerGas || !userOp.maxPriorityFeePerGas) {
                console.log(`[Paymaster] Injecting default gas fees for estimation...`);
                try {
                    const gasPrice = await client.getGasPrice();
                    // Use a safe default (e.g. 2x current gas price to ensure it passes upstream validation)
                    // Upstream often requires these fields to be present and sufficient.
                    if (!userOp.maxFeePerGas) {
                        userOp.maxFeePerGas = `0x${(gasPrice * 3n).toString(16)}`; // 3x buffer
                    }
                    if (!userOp.maxPriorityFeePerGas) {
                        userOp.maxPriorityFeePerGas = `0x${(parseEther("0.000000001")).toString(16)}`; // 1 gwei
                    }
                } catch (e) {
                    console.warn(`[Paymaster] Failed to fetch gas price for estimation:`, e);
                    // Fallback to high values if RPC fails
                    if (!userOp.maxFeePerGas) userOp.maxFeePerGas = '0x1000000000'; // 68 Gwei
                    if (!userOp.maxPriorityFeePerGas) userOp.maxPriorityFeePerGas = '0x3B9ACA00'; // 1 Gwei
                }
            }
        }

        // [FIX] Inject Pimlico Sponsorship Policy ID
        // This ensures usage of the specific policy (and its balance) instead of the default.
        if (method === 'pm_sponsorUserOperation' && config.PIMLICO_POLICY_ID) {
            console.log(`[Paymaster] Applying Policy ID: ${config.PIMLICO_POLICY_ID}`);
            const userOp = params[0];
            const entryPoint = params[1]; // usually absent in request but Pimlico might expect it or we reconstruct params

            // Reconstruct params with policy ID
            // Pimlico expects: [UserOperation, EntryPoint, { sponsorshipPolicyId: "..." }]
            // But standard pm_sponsorUserOperation is [UserOp, EntryPoint]
            // Pimlico extends this.

            // We need to be careful not to break standard signature if we are just proxying.
            // But we ARE proxying to Pimlico specifically.

            request.params = [
                userOp,
                entryPoint || "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789", // Default to v0.6 if missing
                { sponsorshipPolicyId: config.PIMLICO_POLICY_ID }
            ];
        }

        // Forward to Upstream Paymaster
        const UPSTREAM_PAYMASTER_URL = config.UPSTREAM_PAYMASTER_URL;
        console.log(`[Paymaster] Forwarding to: ${UPSTREAM_PAYMASTER_URL}`);

        // SSRF Check (Phase 4)
        if (!isSafeUrl(UPSTREAM_PAYMASTER_URL)) {
            console.error(`[SSRF] Blocked Unsafe URL: ${UPSTREAM_PAYMASTER_URL}`);
            throw new Error("Forbidden: Unsafe Upstream URL");
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

        try {
            const response = await fetch(UPSTREAM_PAYMASTER_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Upstream Error: ${response.status} ${errorText}`);
            }

            const data = await response.json();
            // ... continue with data processing
            const result = data.result;

            // 4. Markup Engine (Phase 3) - DISABLED for sponsorship to avoid signature mismatch
            // We can only apply markup during estimation. Validating Paymaster signature requires exact gas values.
            /*
            if (method === 'pm_sponsorUserOperation' && result && config.MARKUP_RATE) {
                 // Markup logic removed to prevent AA21/AA24 (Signature Check Fail)
            }
            */


            return data as JsonRpcResponse;

        } catch (fetchError: any) {
            clearTimeout(timeoutId);
            if (fetchError.name === 'AbortError') {
                throw new Error("Gateway Timeout: Upstream Paymaster did not respond in time.");
            }
            throw fetchError;
        }

    } catch (error: any) {
        console.error("Processing Failed:", error);

        // Map errors to JSON-RPC codes
        let code = -32603; // Internal error
        let message = error.message || "Internal Proxy Error";

        if (message.includes("Forbidden")) {
            code = -32003;
        } else if (message.includes("Unauthorized")) {
            code = -32001;
        } else if (message.includes("Too Many Requests")) {
            code = -32002;
        } else if (message.includes("Service Unavailable")) {
            code = -32004; // Custom code for 503
        } else if (message.includes("Gateway Timeout")) {
            code = -32005; // Custom code for 504
        }

        return {
            jsonrpc: "2.0",
            error: { code, message },
            id: id
        };
    }
}
