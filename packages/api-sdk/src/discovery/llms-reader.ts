export interface LLMDiscovery {
    endpoints: string[]
    description?: string
}

export class LLMsReader {
    async fetchLLMsTxt(url: string): Promise<string> {
        this.validateUrl(url)
        const response = await fetch(url)
        if (!response.ok) {
            throw new Error(`Failed to fetch llms.txt from ${url}`)
        }
        return await response.text()
    }

    private validateUrl(urlStr: string): void {
        const url = new URL(urlStr)

        // Protocol check
        if (!['http:', 'https:'].includes(url.protocol)) {
            throw new Error(`Invalid protocol: ${url.protocol}. Only http and https are allowed.`)
        }

        const hostname = url.hostname

        // Block localhost
        if (hostname === 'localhost' || hostname.endsWith('.localhost')) {
            throw new Error('Access to localhost is forbidden')
        }

        // Block IPv4 private ranges and 0.0.0.0
        // 127.0.0.0/8
        if (hostname.startsWith('127.')) throw new Error('Access to loopback interface is forbidden')
        // 0.0.0.0/8
        if (hostname.startsWith('0.')) throw new Error('Access to 0.0.0.0 is forbidden')
        // 10.0.0.0/8
        if (hostname.startsWith('10.')) throw new Error('Access to private IP range 10.0.0.0/8 is forbidden')
        // 192.168.0.0/16
        if (hostname.startsWith('192.168.')) throw new Error('Access to private IP range 192.168.0.0/16 is forbidden')
        // 172.16.0.0/12 (172.16.0.0 - 172.31.255.255)
        if (hostname.startsWith('172.')) {
            const secondOctet = parseInt(hostname.split('.')[1], 10)
            if (secondOctet >= 16 && secondOctet <= 31) {
                throw new Error('Access to private IP range 172.16.0.0/12 is forbidden')
            }
        }
        // IPv6 (simple check for ::1)
        if (hostname === '[::1]' || hostname === '::1') {
            throw new Error('Access to IPv6 loopback is forbidden')
        }
    }

    extractEndpoints(content: string): LLMDiscovery {
        const links: string[] = []
        // Simple regex to find markdown links that might be API endpoints
        // In a real implementation, this should parse specific sections defined in the spec
        const linkRegex = /\[.*?\]\((https?:\/\/.*?)\)/g
        let match

        while ((match = linkRegex.exec(content)) !== null) {
            links.push(match[1])
        }

        return {
            endpoints: links,
            description: content.substring(0, 100) + '...'
        }
    }
}
