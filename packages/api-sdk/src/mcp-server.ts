import { Server } from "@modelcontextprotocol/sdk/server/index.js"
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js"
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js"


export class AgentServer {
    private server: Server
    private tools: Map<string, any> = new Map()

    constructor(name: string, version: string) {
        this.server = new Server({
            name,
            version
        }, {
            capabilities: {
                tools: {}
            }
        })

        // Handle List Tools
        this.server.setRequestHandler(ListToolsRequestSchema, async () => {
            return {
                tools: Array.from(this.tools.values()).map(t => ({
                    name: t.name,
                    description: t.description,
                    inputSchema: t.schema
                }))
            }
        })

        // Handle Call Tool
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            const tool = this.tools.get(request.params.name)
            if (!tool) {
                throw new Error(`Tool not found: ${request.params.name}`)
            }

            if (tool.schema) {
                // Assuming tool.schema is a Zod schema or compatible
                const result = tool.schema.safeParse ? tool.schema.safeParse(request.params.arguments) : { success: true, data: request.params.arguments }

                if (!result.success) {
                    const errorMessages = result.error.errors.map((e: any) => `${e.path.join('.')}: ${e.message}`).join(', ')
                    throw new Error(`Invalid arguments for tool ${request.params.name}: ${errorMessages}`)
                }
            }

            return await tool.handler(request.params.arguments)
        })
    }

    registerTool(name: string, description: string, schema: any, handler: any) {
        this.tools.set(name, { name, description, schema, handler })
    }

    async connect(transport: any) {
        await this.server.connect(transport)
    }

    async startStdio() {
        const transport = new StdioServerTransport()
        await this.server.connect(transport)
    }
}
