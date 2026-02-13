# @swimmingkiim/api-sdk

A2A API SDK for building Model Context Protocol (MCP) servers and handling agent-to-agent communication.

## Features

- **MCP Server Implementation**: Easily creating and managing MCP servers.
- **Service Discovery**: Discover other agents and services in the A2A ecosystem.
- **Agent Server**: Core class for defining agent capabilities and tools.

## Installation

```bash
npm install @swimmingkiim/api-sdk @modelcontextprotocol/sdk zod
```

## Usage

### Creating an Agent Server

```typescript
import { AgentServer } from '@swimmingkiim/api-sdk';
import { z } from 'zod';

const server = new AgentServer('my-agent', '1.0.0');

server.registerTool(
  'hello_world',
  'A simple greeting tool',
  { name: z.string() },
  async ({ name }) => {
    return {
      content: [{ type: 'text', text: `Hello, ${name}!` }]
    };
  }
);

// Connect to transport (e.g., SSE)
// ... see root README or examples
```
