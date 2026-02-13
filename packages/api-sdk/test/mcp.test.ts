import { describe, it, expect, beforeEach } from 'vitest'
import { AgentServer } from '../src/mcp-server'
import { LLMsReader } from '../src/discovery/llms-reader'
import { CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js'
import { z } from 'zod'

describe('a2api: Marketplace & Discovery', () => {
    describe('MCP Server', () => {
        let server: AgentServer

        beforeEach(() => {
            server = new AgentServer('test-agent', '1.0.0')
        })

        it('should register and execute a tool', async () => {
            let executed = false
            server.registerTool('test_tool', 'description', { prop: z.string() }, async (args: any) => {
                executed = true
                return { content: [{ type: 'text', text: 'success' }] }
            })

            // We can't easily invoke handlers directly without exposing the internal server 
            // or mocking the transport. But implementation stores tools in a map.
            // Let's verify by checking internal state if possible, or trust the integration test.

            // For unit testing private members, we can use (server as any).tools
            const tools = (server as any).tools
            expect(tools.has('test_tool')).toBe(true)

            // Simulate execution logic
            const tool = tools.get('test_tool')
            const result = await tool.handler({ prop: 'val' })
            expect(executed).toBe(true)
            expect(result.content[0].text).toBe('success')
        })
    })

    describe('Discovery (LLMsReader)', () => {
        it('should extract endpoints from markdown', () => {
            const reader = new LLMsReader()
            const content = `
# API
- [Docs](https://api.a2a.travel/docs)
- [Pricing](https://api.a2a.travel/pricing)
            `
            const result = reader.extractEndpoints(content)
            expect(result.endpoints).toHaveLength(2)
            expect(result.endpoints).toContain('https://api.a2a.travel/docs')
            expect(result.endpoints).toContain('https://api.a2a.travel/pricing')
        })
    })
})
