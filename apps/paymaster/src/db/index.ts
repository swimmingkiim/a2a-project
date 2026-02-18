import { Pool } from "pg";
import { config } from "../config";

let pool: Pool;

export function getDbPool(): Pool {
  if (!pool) {
    // Cloud Run vs Local Config
    // If DB_HOST starts with '/', assume it's a Unix Socket (Cloud Run)
    // Otherwise, it's a TCP host (Local)

    const dbConfig: any = {
      user: config.DB_USER,
      password: config.DB_PASS,
      database: config.DB_NAME,
    };

    if (config.DB_HOST && config.DB_HOST.startsWith("/")) {
      dbConfig.host = config.DB_HOST; // Explicit Unix Socket
    } else if (config.INSTANCE_CONNECTION_NAME) {
      dbConfig.host = `/cloudsql/${config.INSTANCE_CONNECTION_NAME}`; // Auto Cloud SQL Socket
    } else {
      dbConfig.host = config.DB_HOST || "127.0.0.1";
      dbConfig.port = 5432;
    }

    console.log(`🔌 Connecting to Database: ${dbConfig.database} @ ${dbConfig.host}`);

    pool = new Pool(dbConfig);

    pool.on("error", (err: any) => {
      console.error("Unexpected error on idle client", err);
      process.exit(-1);
    });
  }
  return pool;
}

export async function initDb() {
  const client = await getDbPool().connect();
  try {
    console.log("🛠️  Initializing Database Schema...");

    await client.query(`
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                did VARCHAR(255) NOT NULL UNIQUE,
                api_key VARCHAR(255) NOT NULL UNIQUE,
                is_active BOOLEAN DEFAULT TRUE,
                usage_count BIGINT DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        `);

    // Index for faster lookup
    await client.query(`
            CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key);
        `);

    console.log("✅ Database Schema Initialized.");
  } finally {
    client.release();
  }
}
