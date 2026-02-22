import { EventSource } from "eventsource";
global.EventSource = EventSource;

import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import readline from "readline";

const remoteUrl = process.argv[2] || "https://a10m.work/sse";

const transport = new SSEClientTransport(new URL(remoteUrl));

transport.onmessage = (msg) => {
    // Write received messages to stdout (to Claude Desktop)
    console.log(JSON.stringify(msg));
};

transport.onerror = (err) => {
    console.error("Transport Error:", err);
};

async function start() {
    try {
        await transport.start();

        // Read JSON-RPC from Claude Desktop via stdin
        const rl = readline.createInterface({
            input: process.stdin,
            terminal: false
        });

        rl.on('line', async (line) => {
            if (!line.trim()) return;
            try {
                const msg = JSON.parse(line);
                await transport.send(msg);
            } catch (e) {
                console.error("Failed to parse/send message:", e);
            }
        });
    } catch (err) {
        console.error("Failed to start transport:", err);
        process.exit(1);
    }
}

start();
