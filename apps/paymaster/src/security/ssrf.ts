import { URL } from 'url';

/**
 * Validates that the Upstream URL is not a private/local IP.
 * This prevents SSRF if the URL is dynamically configured or compromised.
 */
export function isSafeUrl(urlString: string): boolean {
    try {
        const url = new URL(urlString);
        const hostname = url.hostname;

        // Safe Whitelist
        const whitelist = ['.pimlico.io', '.alchemy.com', '.base.org'];
        const isWhitelisted = whitelist.some(domain => hostname.endsWith(domain));

        if (isWhitelisted) {
            return true;
        }

        // Block localhost
        if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1') {
            return false;
        }

        // Block private ranges (simple regex for IPv4)
        // 10.x.x.x, 192.168.x.x, 172.16-31.x.x
        if (hostname.startsWith('10.') ||
            hostname.startsWith('192.168.') ||
            /^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname)) {
            return false;
        }

        // AWS Metadata / Cloud metadata
        if (hostname === '169.254.169.254') {
            return false;
        }

        return true;
    } catch (e) {
        return false;
    }
}
