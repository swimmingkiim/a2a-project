const PORT = process.env.PORT || 8080

async function startServer() {
    console.log('Starting Agent Node...')
    try {
        console.log('Importing dependencies...')
        const express = (await import('express')).default
        const cors = (await import('cors')).default
        const { AgentServer } = await import('@swimmingkiim/api-sdk')
        const { IdentityManager } = await import('@swimmingkiim/trust-sdk')
        const { SSEServerTransport } = await import('@modelcontextprotocol/sdk/server/sse.js')
        const { z } = await import('zod')

        // const { airdropService } = await import('./airdrop.js') // Removed direct import
        const { handleGrantRequest } = await import('./grant-handler.js')

        let db: any = null
        let dbInitError: string | null = null
        try {
            const { Pool } = await import('pg')
            console.log('Dependencies imported successfully.')

            // Initialize PostgreSQL Database
            if (process.env.DB_HOST || process.env.INSTANCE_CONNECTION_NAME) {
                const config: any = {
                    user: process.env.DB_USER,
                    password: process.env.DB_PASSWORD,
                    database: process.env.DB_NAME,
                }

                if (process.env.INSTANCE_CONNECTION_NAME) {
                    config.host = `/cloudsql/${process.env.INSTANCE_CONNECTION_NAME}`
                } else {
                    config.host = process.env.DB_HOST
                    config.port = Number(process.env.DB_PORT) || 5432
                }

                console.log(`Connecting to database: ${config.host} / ${config.database}`)
                db = new Pool(config)

                // Verify connection
                await db.query('SELECT NOW()')
                console.log('Database connected successfully.')

                const initDb = async () => {
                    await db.query(`
                        CREATE TABLE IF NOT EXISTS projects (
                            id SERIAL PRIMARY KEY,
                            name TEXT NOT NULL,
                            description TEXT,
                            api_url TEXT NOT NULL,
                            owner_did TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(api_url, owner_did)
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
                    `)
                }
                await initDb()
                console.log('Database initialized.')
            } else {
                console.warn('No database configuration found (DB_HOST or INSTANCE_CONNECTION_NAME). Running without DB.')
            }

        } catch (e: any) {
            console.error('Failed to initialize PostgreSQL, functionality will be limited:', e)
            if (process.env.INSTANCE_CONNECTION_NAME) {
                console.error('Hint: Make sure the Cloud SQL connection name is correct and the service account has "Cloud SQL Client" role.');
                console.error('If running locally, ensure Cloud SQL Proxy is running.');
            }
            dbInitError = e.message || String(e)
            db = null
        }

        const logActivity = async (type: string, details: any) => {
            if (!db) return
            try {
                await db.query(
                    'INSERT INTO agent_activity_logs (activity_type, details) VALUES ($1, $2)',
                    [type, JSON.stringify(details)]
                )
            } catch (e) {
                console.error('Failed to log activity:', e)
            }
        }

        const app = express()

        app.use(cors())
        app.use(express.json())

        console.log('Initializing IdentityManager...')
        // Initialize A2A Components
        const idManager = new IdentityManager()

        console.log('Initializing AgentServer...')
        // Initialize MCP Server
        const mcpServer = new AgentServer("a2a-agent-node", "1.0.0")

        // Register Tools
        mcpServer.registerTool(
            "get_agent_identity",
            "Returns the DID of this agent",
            {},
            async () => {
                const did = await idManager.createEphemeralDID()
                return {
                    content: [{ type: "text", text: did.did }]
                }
            }
        )


        mcpServer.registerTool(
            "echo",
            "Echoes back the input",
            { message: z.string() },
            async ({ message }: { message: string }) => {
                await logActivity('TOOL_USAGE', { tool: 'echo', message })
                return {
                    content: [{ type: "text", text: `Echo: ${message}` }]
                }
            }
        )

        // MCP SSE Variable
        let transport: any = null



        const MANIFEST = {
            name: "a2a-agent-node",
            description: "A2A Agent Node",
            version: "1.0.0",
            mcp: {
                endpoint: "/sse",
                transport: "sse",
                message_endpoint: "/message"
            },
            tools: [
                {
                    name: "get_agent_identity",
                    description: "Returns the DID of this agent",
                    input_schema: {}
                },
                {
                    name: "echo",
                    description: "Echoes back the input",
                    input_schema: { message: "string" }
                }
            ]
        }

        app.get('/', (_req: any, res: any) => {
            res.header('Content-Type', 'text/html')
            res.send(`
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>A2A Agent Node</title>
                <script>
                    async function fetchProjects() {
                        const res = await fetch('/api/projects');
                        const list = document.getElementById('project-list');
                        
                        if (!res.ok) {
                            const err = await res.json().catch(() => ({ error: res.statusText }));
                            list.innerHTML = \`<div style="color: red; padding: 10px; border: 1px solid red; border-radius: 5px;">
                                <strong>Failed to load projects:</strong> \${err.error || res.statusText}
                                \${res.status === 503 ? '<br><small>Make sure the database configuration is correct.</small>' : ''}
                            </div>\`;
                            return;
                        }

                        const projects = await res.json();
                        if (projects.length === 0) {
                            list.innerHTML = '<p>No projects found.</p>';
                            return;
                        }

                        list.innerHTML = projects.map(p => \`
                            <div class="card">
                                <h3>\${p.name}</h3>
                                <p>\${p.description}</p>
                                <p><strong>API URL:</strong> <a href="\${p.api_url}" target="_blank">\${p.api_url}</a></p>
                                <p class="url">Owner: \${p.owner_did}</p>
                            </div>
                        \`).join('');
                    }

                    async function registerProject(event) {
                        event.preventDefault();
                        const formData = new FormData(event.target);
                        const data = Object.fromEntries(formData.entries());
                        
                        try {
                            const res = await fetch('/api/projects', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(data)
                            });
                            
                            if (res.ok) {
                                alert('Project registered successfully!');
                                fetchProjects();
                                event.target.reset();
                            } else {
                                const err = await res.json();
                                alert('Failed to register: ' + JSON.stringify(err));
                            }
                        } catch (e) {
                            alert('Error: ' + e.message);
                        }
                    }

                    window.onload = fetchProjects;
                </script>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }
                    h1 { color: #2563eb; }
                    code { background: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-family: monospace; }
                    .card { border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-bottom: 20px; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
                    .method { font-weight: bold; color: #059669; }
                    .url { color: #666; }
                </style>
            </head>
            <body>
                <h1>🤖 A2A Agent Node</h1>
                <p>Status: <span style="color: green; font-weight: bold;">● Active</span></p>
                <p>Region: <code>asia-northeast1</code></p>
                
                <h2>🌍 Ecosystem Projects</h2>
                <div id="project-list">
                    <p>Loading projects...</p>
                </div>

                <h2>📝 Register Project</h2>
                <div class="card">
                    <form onsubmit="registerProject(event)">
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; font-weight: bold;">Name:</label>
                            <input type="text" name="name" required style="width: 100%; padding: 8px; box-sizing: border-box;">
                        </div>
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; font-weight: bold;">Description:</label>
                            <input type="text" name="description" required style="width: 100%; padding: 8px; box-sizing: border-box;">
                        </div>
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; font-weight: bold;">API URL:</label>
                            <input type="url" name="apiUrl" required placeholder="https://..." style="width: 100%; padding: 8px; box-sizing: border-box;">
                        </div>
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; font-weight: bold;">Owner DID:</label>
                            <input type="text" name="ownerDid" required placeholder="did:web:yourdomain.com" style="width: 100%; padding: 8px; box-sizing: border-box;">
                            <details style="margin-top: 5px; padding: 10px; background: #f8fafc; border-radius: 4px; font-size: 0.9em;">
                                <summary style="cursor: pointer; font-weight: 600; color: #2563eb;">ℹ️ DID Selection Guide</summary>
                                <div style="margin-top: 10px; line-height: 1.6;">
                                    <p style="margin-bottom: 8px;"><strong>DID (Decentralized Identifier)</strong> is a unique identifier that proves ownership of your project.</p>
                                    
                                    <p style="margin: 12px 0 6px 0; font-weight: 600;">✅ Recommended: did:web (Web-based DID)</p>
                                    <ul style="margin: 5px 0 10px 20px; padding-left: 0;">
                                        <li><code style="background: #e2e8f0; padding: 2px 4px; border-radius: 3px;">did:web:api.yourdomain.com</code></li>
                                        <li>Benefits: No private key exposure risk, prove ownership via domain</li>
                                        <li>Security: High (no private key required)</li>
                                    </ul>

                                    <p style="margin: 12px 0 6px 0; font-weight: 600;">⚠️ Caution: did:ethr (Ethereum address-based)</p>
                                    <ul style="margin: 5px 0 10px 20px; padding-left: 0;">
                                        <li><code style="background: #e2e8f0; padding: 2px 4px; border-radius: 3px;">did:ethr:0x1234...</code></li>
                                        <li>Benefits: Verifiable via blockchain address</li>
                                        <li>⚠️ <strong>Warning</strong>: Exposes your actual wallet address</li>
                                        <li>Recommendation: Use dedicated address (never use main wallet)</li>
                                    </ul>

                                    <p style="margin: 12px 0 6px 0; font-weight: 600;">❌ Not Recommended: did:pkh (Private key-based)</p>
                                    <ul style="margin: 5px 0 0 20px; padding-left: 0;">
                                        <li><code style="background: #e2e8f0; padding: 2px 4px; border-radius: 3px;">did:pkh:eip155:8453:0x...</code></li>
                                        <li>⚠️ May contain private key information</li>
                                        <li>Security: Low (not recommended)</li>
                                    </ul>

                                    <p style="margin-top: 12px; padding: 8px; background: #fef3c7; border-left: 3px solid #f59e0b; font-size: 0.85em;">
                                        <strong>⚡ Security Tip:</strong> We strongly recommend using did:web. It has no risk of private key exposure and can be authenticated with domain ownership alone.
                                    </p>
                                </div>
                            </details>
                        </div>
                        <button type="submit" style="background: #2563eb; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer;">Register Project</button>
                    </form>
                </div>


                <h2>💰 Developer Grant Guide (지원금 안내)</h2>
                <div class="card">
                    <p><strong>Eligibility:</strong> You can claim <strong>100 $DAIM</strong> tokens once per DID and Wallet address as a developer grant.</p>
                    <p><strong>How to Apply:</strong></p>
                    <ol>
                        <li>Create a <strong>Verifiable Credential (VC)</strong> proving ownership of your wallet address.</li>
                        <li>Send a <code>POST</code> request to <code class="url">/api/grant</code> with the VC in the <code>Authorization</code> header.</li>
                    </ol>
                    <div style="background: #1e293b; color: #f8fafc; padding: 15px; border-radius: 6px; overflow-x: auto; font-family: monospace; font-size: 0.9em;">
                        <span style="color: #94a3b8;"># Example Request</span><br>
                        curl -X POST /api/grant \<br>
                        &nbsp;&nbsp;-H "Authorization: Bearer &lt;YOUR_VC_JWT&gt;" \<br>
                        &nbsp;&nbsp;-H "Content-Type: application/json"
                    </div>
                    <p style="margin-top: 10px; font-size: 0.9em; color: #666;">
                        * The VC must be a self-signed JWT where <code>iss</code> (Issuer) == <code>sub</code> (Subject) == Your DID.<br>
                        * The VC credentialSubject must contain <code>walletAddress</code>.
                    </p>
                </div>

                <h2>📡 Interfaces</h2>
                <div class="card">
                    <p><span class="method">GET</span> <code class="url">/api/projects</code> - List all ecosystem projects</p>
                    <p><span class="method">POST</span> <code class="url">/api/projects</code> - Register a new project</p>
                    <p><span class="method">GET</span> <code class="url">/manifest.json</code> - Machine-readable agent description</p>
                    <p><span class="method">GET</span> <code class="url">/sse</code> - MCP Transport Connection (Server-Sent Events)</p>
                    <p><span class="method">POST</span> <code class="url">/message</code> - MCP Message Endpoint</p>
                </div>

                <h2>🛠 Available Tools</h2>
                ${MANIFEST.tools.map(t => `
                <div class="card">
                    <h3>${t.name}</h3>
                    <p>${t.description}</p>
                    <p><strong>Input:</strong> <code>${JSON.stringify(t.input_schema)}</code></p>
                </div>
                `).join('')}

                <h2>📘 Usage</h2>
                <p>Connect to this agent using an MCP Client via the SSE transport at <code>/sse</code>.</p>
            </body>
            </html>
            `)
        })


        // Projects API
        const { ProjectSchema, verifyProjectApi } = await import('./verification.js')



        app.get('/api/projects', async (_req: any, res: any) => {
            if (!db) {
                console.warn(`[API] Failed to serve /api/projects: Database not initialized. Cause: ${dbInitError}`);
                res.status(503).json({ error: dbInitError ? `Database not initialized: ${dbInitError}` : 'Database not initialized (Missing configuration)' })
                return
            }
            try {
                const result = await db.query('SELECT * FROM projects ORDER BY created_at DESC')
                res.json(result.rows)
            } catch (err: any) {
                res.status(500).json({ error: err.message })
            }
        })

        app.post('/api/projects', async (req: any, res: any) => {
            if (!db) {
                console.warn(`[API] Failed to serve /api/projects: Database not initialized. Cause: ${dbInitError}`);
                res.status(503).json({ error: dbInitError ? `Database not initialized: ${dbInitError}` : 'Database not initialized (Missing configuration)' })
                return
            }
            try {
                const data = ProjectSchema.parse(req.body)

                // Verify API
                await verifyProjectApi(data.apiUrl, data.ownerDid)

                const query = `
                    INSERT INTO projects (name, description, api_url, owner_did)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id, name, description, api_url, owner_did, created_at
                `
                const values = [data.name, data.description, data.apiUrl, data.ownerDid]
                const result = await db.query(query, values)

                res.status(201).json(result.rows[0])
            } catch (error: any) {
                // Handle duplicate entry (PostgreSQL error code 23505)
                if (error.code === '23505') {
                    res.status(409).json({
                        error: 'This API URL is already registered by this owner. Duplicate registration is not allowed.',
                        details: 'A project with the same API URL and owner DID already exists.'
                    })
                } else {
                    res.status(400).json({ error: error.message || error })
                }
            }
        })

        app.post('/api/grant', async (req: any, res: any) => {
            await handleGrantRequest(req, res, db)
        })

        app.get('/api/logs', async (_req: any, res: any) => {
            if (!db) {
                console.warn(`[API] Failed to serve /api/projects: Database not initialized. Cause: ${dbInitError}`);
                res.status(503).json({ error: dbInitError ? `Database not initialized: ${dbInitError}` : 'Database not initialized (Missing configuration)' })
                return
            }
            try {
                const limit = _req.query.limit ? parseInt(_req.query.limit as string) : 50
                const result = await db.query('SELECT * FROM agent_activity_logs ORDER BY created_at DESC LIMIT $1', [limit])
                res.json(result.rows)
            } catch (err: any) {
                res.status(500).json({ error: err.message })
            }
        })

        app.get('/manifest.json', (_req: any, res: any) => {
            res.json(MANIFEST)
        })

        app.get('/health', (_req: any, res: any) => {
            res.status(200).send('OK')
        })

        app.get('/sse', async (_req: any, res: any) => {
            console.log('New SSE connection')
            transport = new SSEServerTransport('/message', res)
            await mcpServer.connect(transport)
        })

        app.post('/message', async (req: any, res: any) => {
            if (transport) {
                await transport.handlePostMessage(req, res)
            } else {
                res.status(400).send('No active connection')
            }
        })

        app.get('/llms.txt', (_req: any, res: any) => {
            res.header('Content-Type', 'text/plain');
            res.send(`# A2A Agent Node\n\nThis is an A2A Agent Node. See /manifest.json for tools.`);
        });

        app.listen(Number(PORT), '0.0.0.0', () => {
            console.log(`Agent Node listening on port ${PORT}`)
        })

    } catch (error) {
        console.error('Failed to start Agent Node:', error)
        process.exit(1)
    }
}

startServer()
