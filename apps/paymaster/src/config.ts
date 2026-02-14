import dotenv from 'dotenv';
import { z } from 'zod';

dotenv.config();

const envSchema = z.object({
    // Environment & Safety
    NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
    CI: z.string().optional(), // Must NOT be 'true' in production
    DISABLE_PAYMASTER: z.string().transform(v => v === 'true').default('false'), // Emergency shutdown

    PORT: z.string().default('8080'),
    // For testing, we might not always have valid URLs if we mock everything, 
    // but in production these must be URLs.
    RPC_URL: z.string().url(),
    MARKUP_RATE: z.string().regex(/^\d+(\.\d+)?$/).transform(Number).default('0.1'),

    TREASURY_ADDRESS: z.string().startsWith('0x').default('0x129154b7E3f0Ab0E59615ef578f6511b072FB431'), // [REQUIRED] Address to receive fees
    FEE_TOKEN_ADDRESS: z.string().startsWith('0x').default('0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'), // Default to USDC on Base
    FEE_AMOUNT: z.string().regex(/^\d+$/).default('100000'), // 0.1 USDC (6 decimals)
    ETH_PRICE_USD: z.string().regex(/^\d+(\.\d+)?$/).default('2500'), // Default ETH Price ($2500)

    // $DAIM Token Configuration
    DAIM_TOKEN_ADDRESS: z.string().startsWith('0x').default('0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2'), // Deployed DaimToken address
    DAIM_PRICE_USD: z.string().regex(/^\d+(\.\d+)?$/).default('0.10'), // Default $0.10 per DAIM
    ENABLE_DAIM_FEES: z.string().transform(v => v === 'true').default('false'), // Feature flag

    // Monitoring
    MIN_SIGNER_BALANCE_ETH: z.string().regex(/^\d+(\.\d+)?$/).transform(Number).default('0.01'), // Alert threshold

    // Paymaster Configuration
    PAYMASTER_URL: z.string().url().optional(),
    A2A_PAYMASTER_API_KEY: z.string().optional(),
    UPSTREAM_PAYMASTER_URL: z.string().url().default('https://api.pimlico.io/v2/8453/rpc?apikey=public'), // Default to Base Mainnet public for safety
    PIMLICO_POLICY_ID: z.string().optional(),

    // Paymaster Signer (For Minting COMP)
    PAYMASTER_SIGNER_PRIVATE_KEY: z.string().regex(/^0x[a-fA-F0-9]{64}$/, "Invalid Private Key format").optional(),

    // Database
    DB_USER: z.string().optional(),
    DB_PASS: z.string().optional(),
    DB_NAME: z.string().optional(),
    DB_HOST: z.string().optional(),
    INSTANCE_CONNECTION_NAME: z.string().optional(),
});

// We only enforce validation if we are NOT in test mode, or we can mock process.env in tests.
// Ideally, we want config to fail if envs are missing.
const parsedEnv = envSchema.safeParse(process.env);

if (!parsedEnv.success) {
    console.error('❌ Invalid environment variables:', JSON.stringify(parsedEnv.error.format(), null, 2));
    console.log('Available Env Keys:', Object.keys(process.env).join(', '));
    // Do NOT exit here to allow container to start and logs to be flushed.
    // We will throw internally if config is accessed.
    process.exit(1);
}

// PRODUCTION SAFETY CHECK
if (parsedEnv.success && parsedEnv.data.NODE_ENV === 'production') {
    // CRITICAL: CI must not be 'true' in production
    if (parsedEnv.data.CI === 'true') {
        console.error('🚨 FATAL: CI=true is set in production mode!');
        console.error('🚨 This will skip balance verification and cause fund drainage!');
        console.error('🚨 Unset CI or set to false before deploying to production.');
        process.exit(1);
    }

    // Warn if markup rate is too low for production
    if (parsedEnv.data.MARKUP_RATE < 1.5) {
        console.warn('⚠️  WARNING: MARKUP_RATE < 1.5 in production');
        console.warn('⚠️  Recommended: >= 1.5 to protect against gas volatility');
    }

    console.log('✅ Production environment validation passed');
}

export const config = parsedEnv.success ? parsedEnv.data : process.env as any;

