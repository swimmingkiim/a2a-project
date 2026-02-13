export class RateLimiter {
    private requests: Map<string, number[]> = new Map();
    private limit: number;
    private windowMs: number;

    constructor(limit: number, windowMs: number) {
        this.limit = limit;
        this.windowMs = windowMs;
    }

    isRateLimited(key: string): boolean {
        const now = Date.now();
        const timestamps = this.requests.get(key) || [];

        // Filter out old timestamps
        const windowStart = now - this.windowMs;
        const recentRequests = timestamps.filter(t => t > windowStart);

        if (recentRequests.length >= this.limit) {
            return true;
        }

        recentRequests.push(now);
        this.requests.set(key, recentRequests);
        return false;
    }
}
