import rateLimit from "express-rate-limit";

/**
 * Creates an IP-based rate limiter middleware.
 * Uses in-memory store (sufficient for single Cloud Run instance).
 *
 * @param windowMs — Time window in milliseconds
 * @param max — Maximum requests per IP within the window
 */
export function createRateLimiter(windowMs: number, max: number) {
    return rateLimit({
        windowMs,
        max,
        standardHeaders: true,
        legacyHeaders: false,
        message: { error: "Too many requests. Please try again later." },
        keyGenerator: (req) => {
            // Cloud Run sets x-forwarded-for; fall back to req.ip
            return (
                (req.headers["x-forwarded-for"] as string)?.split(",")[0]?.trim() ||
                req.ip ||
                "unknown"
            );
        },
    });
}

/** Strict limiter for write endpoints: 5 req / min per IP */
export const writeRateLimiter = createRateLimiter(60_000, 5);

/** Standard limiter for read endpoints: 30 req / min per IP */
export const readRateLimiter = createRateLimiter(60_000, 30);

/** Grant limiter: 3 req / min per IP (token distribution) */
export const grantRateLimiter = createRateLimiter(60_000, 3);
