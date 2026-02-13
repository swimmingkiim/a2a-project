import { AgentServer } from '../src/mcp-server'
import { LLMsReader } from '../src/discovery/llms-reader'
import { z } from 'zod'

async function main() {
    console.log("--- Starting A2A API SDK Verification ---")

    // 1. MCP Server Test
    console.log("Initializing MCP Server...")
    const server = new AgentServer("test-agent", "1.0.0")

    server.registerTool(
        "calculator",
        "A simple calculator",
        {
            num1: z.number(),
            num2: z.number(),
        },
        async ({ num1, num2 }: { num1: number, num2: number }) => {
            return {
                content: [{ type: "text", text: String(num1 + num2) }]
            }
        }
    )
    console.log("Tool registered successfully.")

    // 2. Discovery Test (Mock)
    console.log("Testing Discovery Reader...")
    const reader = new LLMsReader()
    const mockContent = `
# Agent API
This is an agent.
- [Docs](https://api.example.com/docs)
- [Pricing](https://api.example.com/pricing)
    `
    const discovery = reader.extractEndpoints(mockContent)
    console.log("Discovered endpoints:", discovery.endpoints)

    if (discovery.endpoints.length === 2) {
        console.log("Discovery logic verified.")
    } else {
        console.error("Discovery logic failed.")
        process.exit(1)
    }
}

main().catch(console.error)
