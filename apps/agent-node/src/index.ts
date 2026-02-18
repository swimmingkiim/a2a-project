const PORT = process.env.PORT || 8080;

async function startServer() {
  console.log("Starting Agent Node...");
  try {
    console.log("Importing dependencies...");
    const express = (await import("express")).default;
    const cors = (await import("cors")).default;
    const { AgentServer } = await import("@swimmingkiim/api-sdk");
    const { IdentityManager } = await import("@swimmingkiim/trust-sdk");
    const { SSEServerTransport } = await import("@modelcontextprotocol/sdk/server/sse.js");
    const { z } = await import("zod");

    // const { airdropService } = await import('./airdrop.js') // Removed direct import
    const { handleGrantRequest } = await import("./grant-handler.js");
    const { writeRateLimiter, readRateLimiter, grantRateLimiter } = await import("./rate-limiter.js");

    let db: any = null;
    let dbInitError: string | null = null;
    try {
      const { Pool } = await import("pg");
      console.log("Dependencies imported successfully.");

      // Initialize PostgreSQL Database
      if (process.env.DB_HOST || process.env.INSTANCE_CONNECTION_NAME) {
        const config: any = {
          user: process.env.DB_USER,
          password: process.env.DB_PASSWORD,
          database: process.env.DB_NAME,
        };

        if (process.env.INSTANCE_CONNECTION_NAME) {
          config.host = `/cloudsql/${process.env.INSTANCE_CONNECTION_NAME}`;
        } else {
          config.host = process.env.DB_HOST;
          config.port = Number(process.env.DB_PORT) || 5432;
        }

        console.log(`Connecting to database: ${config.host} / ${config.database}`);
        db = new Pool(config);

        // Verify connection
        await db.query("SELECT NOW()");
        console.log("Database connected successfully.");

        const initDb = async () => {
          await db.query(`
                        CREATE TABLE IF NOT EXISTS projects (
                            id SERIAL PRIMARY KEY,
                            name TEXT NOT NULL,
                            description TEXT,
                            api_url TEXT NOT NULL,
                            owner_wallet TEXT NOT NULL,
                            owner_did TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(api_url, owner_wallet)
                        );

                        CREATE TABLE IF NOT EXISTS agent_activity_logs (
                            id SERIAL PRIMARY KEY,
                            activity_type TEXT NOT NULL,
                            details JSONB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );

                        CREATE TABLE IF NOT EXISTS developer_grants (
                            id SERIAL PRIMARY KEY,
                            did TEXT NOT NULL UNIQUE,
                            wallet_address TEXT NOT NULL UNIQUE,
                            tx_hash TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    `);

          // --- Migrations: Add columns that may be missing on existing tables ---
          await db.query(`
                        DO $$
                        BEGIN
                            -- Add owner_wallet column if it doesn't exist
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name = 'projects' AND column_name = 'owner_wallet'
                            ) THEN
                                ALTER TABLE projects ADD COLUMN owner_wallet TEXT;
                                -- Backfill existing rows with zero-address placeholder
                                UPDATE projects SET owner_wallet = '0x0000000000000000000000000000000000000000' WHERE owner_wallet IS NULL;
                                ALTER TABLE projects ALTER COLUMN owner_wallet SET NOT NULL;
                            END IF;

                            -- Add UNIQUE constraint on (api_url, owner_wallet) if it doesn't exist
                            IF NOT EXISTS (
                                SELECT 1 FROM pg_constraint
                                WHERE conname = 'projects_api_url_owner_wallet_key'
                            ) THEN
                                ALTER TABLE projects ADD CONSTRAINT projects_api_url_owner_wallet_key UNIQUE (api_url, owner_wallet);
                            END IF;
                        END $$;
                    `);
        };
        await initDb();
        console.log("Database initialized.");
      } else {
        console.warn(
          "No database configuration found (DB_HOST or INSTANCE_CONNECTION_NAME). Running without DB.",
        );
      }
    } catch (e: any) {
      console.error("Failed to initialize PostgreSQL, functionality will be limited:", e);
      if (process.env.INSTANCE_CONNECTION_NAME) {
        console.error(
          'Hint: Make sure the Cloud SQL connection name is correct and the service account has "Cloud SQL Client" role.',
        );
        console.error("If running locally, ensure Cloud SQL Proxy is running.");
      }
      dbInitError = e.message || String(e);
      db = null;
    }

    const logActivity = async (type: string, details: any) => {
      if (!db) return;
      try {
        await db.query("INSERT INTO agent_activity_logs (activity_type, details) VALUES ($1, $2)", [
          type,
          JSON.stringify(details),
        ]);
      } catch (e) {
        console.error("Failed to log activity:", e);
      }
    };

    const app = express();

    app.use(cors());
    app.use(express.json({ limit: "1mb" }));

    console.log("Initializing IdentityManager...");
    // Initialize A2A Components
    const idManager = new IdentityManager();

    console.log("Initializing AgentServer...");
    // Initialize MCP Server
    const mcpServer = new AgentServer("a2a-agent-node", "1.0.0");

    // Register Tools
    mcpServer.registerTool("get_agent_identity", "Returns the DID of this agent", {}, async () => {
      const did = await idManager.createEphemeralDID();
      return {
        content: [{ type: "text", text: did.did }],
      };
    });

    mcpServer.registerTool(
      "echo",
      "Echoes back the input",
      { message: z.string() },
      async ({ message }: { message: string }) => {
        await logActivity("TOOL_USAGE", { tool: "echo", message });
        return {
          content: [{ type: "text", text: `Echo: ${message}` }],
        };
      },
    );

    // MCP SSE Variable
    let transport: any = null;

    const MANIFEST = {
      name: "a2a-agent-node",
      description: "A2A Agent Node",
      version: "1.0.0",
      mcp: {
        endpoint: "/sse",
        transport: "sse",
        message_endpoint: "/message",
      },
      tools: [
        {
          name: "get_agent_identity",
          description: "Returns the DID of this agent",
          input_schema: {},
        },
        {
          name: "echo",
          description: "Echoes back the input",
          input_schema: { message: "string" },
        },
      ],
    };

    app.get("/", (_req: any, res: any) => {
      res.header("Content-Type", "text/html");
      res.send(`
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>A2A Agent Node</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }
                    h1 { color: #2563eb; }
                    code { background: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-family: monospace; }
                    .card { border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-bottom: 20px; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
                    .method { font-weight: bold; color: #059669; }
                    .url { color: #666; }
                    pre { background: #1e293b; color: #f8fafc; padding: 15px; border-radius: 6px; overflow-x: auto; font-family: monospace; font-size: 0.9em; }
                    .comment { color: #94a3b8; }
                </style>
            </head>
            <body>
                <h1>🤖 A2A Agent Node</h1>
                <p>Status: <span style="color: green; font-weight: bold;">● Active</span></p>

                <h2>📡 API Endpoints</h2>
                <div class="card">
                    <p><span class="method">GET</span> <code class="url">/api/projects</code> — List all ecosystem projects</p>
                    <p><span class="method">POST</span> <code class="url">/api/projects</code> — Register a new project (rate limited)</p>
                    <p><span class="method">POST</span> <code class="url">/api/grant</code> — Apply for developer grant (rate limited)</p>
                    <p><span class="method">GET</span> <code class="url">/manifest.json</code> — Machine-readable agent description</p>
                    <p><span class="method">GET</span> <code class="url">/sse</code> — MCP Transport Connection (Server-Sent Events)</p>
                    <p><span class="method">POST</span> <code class="url">/message</code> — MCP Message Endpoint</p>
                </div>

                <h2>📝 Register a Project (API)</h2>
                <div class="card">
                    <p>To register a project, send a <code>POST</code> request to <code>/api/projects</code>:</p>
                    <pre><span class="comment"># Example Request</span>
curl -X POST /api/projects \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "My Bot",
    "description": "A helpful AI assistant",
    "apiUrl": "https://my-bot.example.com",
    "ownerWallet": "0xYourWalletAddress",
    "ownerDid": "did:web:my-bot.example.com"
  }'</pre>
                    <p style="margin-top: 10px; font-size: 0.9em; color: #666;">The API URL must serve a valid <code>/manifest.json</code> and <code>/llms.txt</code>.</p>
                </div>

                <h2>💰 Developer Grant</h2>
                <div class="card">
                    <p>Claim <strong>100 $DAIM</strong> tokens per registered project.</p>
                    <pre><span class="comment"># Example Request</span>
curl -X POST /api/grant \\
  -H "Authorization: Bearer &lt;YOUR_VC_JWT&gt;" \\
  -H "Content-Type: application/json"</pre>
                    <p style="margin-top: 10px; font-size: 0.9em; color: #666;">The VC must be a self-signed JWT where <code>iss == sub == Your DID</code> and <code>credentialSubject</code> contains <code>walletAddress</code>.</p>
                </div>

                <h2>🛠 Available MCP Tools</h2>
                ${MANIFEST.tools
          .map(
            (t) => `
                <div class="card">
                    <h3>${t.name}</h3>
                    <p>${t.description}</p>
                    <p><strong>Input:</strong> <code>${JSON.stringify(t.input_schema)}</code></p>
                </div>
                `,
          )
          .join("")}
            </body>
            </html>
            `);
    });

    // Projects API
    const { ProjectSchema, verifyProjectApi } = await import("./verification.js");

    app.get("/api/projects", async (_req: any, res: any) => {
      if (!db) {
        console.warn(
          `[API] Failed to serve /api/projects: Database not initialized. Cause: ${dbInitError}`,
        );
        res.status(503).json({
          error: dbInitError
            ? `Database not initialized: ${dbInitError}`
            : "Database not initialized (Missing configuration)",
        });
        return;
      }
      try {
        const result = await db.query("SELECT * FROM projects ORDER BY created_at DESC");
        res.json(result.rows);
      } catch (err: any) {
        res.status(500).json({ error: err.message });
      }
    });

    app.post("/api/projects", writeRateLimiter, async (req: any, res: any) => {
      if (!db) {
        console.warn(
          `[API] Failed to serve /api/projects: Database not initialized. Cause: ${dbInitError}`,
        );
        res.status(503).json({
          error: dbInitError
            ? `Database not initialized: ${dbInitError}`
            : "Database not initialized (Missing configuration)",
        });
        return;
      }
      try {
        const data = ProjectSchema.parse(req.body);

        // Verify API (DID verification is optional)
        await verifyProjectApi(data.apiUrl, data.ownerDid);

        const query = `
                    INSERT INTO projects (name, description, api_url, owner_wallet, owner_did)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id, name, description, api_url, owner_wallet, owner_did, created_at
                `;
        const values = [data.name, data.description, data.apiUrl, data.ownerWallet, data.ownerDid ?? null];
        const result = await db.query(query, values);

        res.status(201).json(result.rows[0]);
      } catch (error: any) {
        // Handle duplicate entry (PostgreSQL error code 23505)
        if (error.code === "23505") {
          res.status(409).json({
            error:
              "This API URL is already registered by this owner. Duplicate registration is not allowed.",
            details: "A project with the same API URL and owner DID already exists.",
          });
        } else {
          res.status(400).json({ error: error.message || error });
        }
      }
    });

    app.post("/api/grant", grantRateLimiter, async (req: any, res: any) => {
      await handleGrantRequest(req, res, db);
    });

    app.get("/api/logs", readRateLimiter, async (_req: any, res: any) => {
      if (!db) {
        console.warn(
          `[API] Failed to serve /api/projects: Database not initialized. Cause: ${dbInitError}`,
        );
        res.status(503).json({
          error: dbInitError
            ? `Database not initialized: ${dbInitError}`
            : "Database not initialized (Missing configuration)",
        });
        return;
      }
      try {
        const limit = _req.query.limit ? parseInt(_req.query.limit as string) : 50;
        const result = await db.query(
          "SELECT * FROM agent_activity_logs ORDER BY created_at DESC LIMIT $1",
          [limit],
        );
        res.json(result.rows);
      } catch (err: any) {
        res.status(500).json({ error: err.message });
      }
    });

    app.get("/manifest.json", (_req: any, res: any) => {
      res.json(MANIFEST);
    });

    app.get("/health", (_req: any, res: any) => {
      res.status(200).send("OK");
    });

    app.get("/sse", async (_req: any, res: any) => {
      console.log("New SSE connection");
      res.writeHead(200, {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
      });
      res.write(": connected\n\n");
      transport = new SSEServerTransport("/message", res);
      await mcpServer.connect(transport);
    });

    app.post("/message", async (req: any, res: any) => {
      if (transport) {
        await transport.handlePostMessage(req, res);
      } else {
        res.status(400).send("No active connection");
      }
    });

    app.get("/llms.txt", (_req: any, res: any) => {
      res.header("Content-Type", "text/plain");
      res.send(`# A2A Agent Node\n\nThis is an A2A Agent Node. See /manifest.json for tools.`);
    });

    app.listen(Number(PORT), "0.0.0.0", () => {
      console.log(`Agent Node listening on port ${PORT}`);
    });
  } catch (error) {
    console.error("Failed to start Agent Node:", error);
    process.exit(1);
  }
}

startServer();
