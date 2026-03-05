import rateLimit from 'express-rate-limit';

/**
 * General API rate limiter — 100 requests per 15 minutes per IP
 */
export const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100,
    standardHeaders: true,   // Return RateLimit-* headers
    legacyHeaders: false,     // Disable X-RateLimit-* headers
    message: {
        success: false,
        message: 'Too many requests from this IP, please try again after 15 minutes.',
    },
});

/**
 * Auth-specific limiter — stricter: 10 attempts per 15 minutes
 * Protect login/register from brute-force
 */
export const authLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 10,
    standardHeaders: true,
    legacyHeaders: false,
    message: {
        success: false,
        message: 'Too many authentication attempts. Please wait 15 minutes before trying again.',
    },
});
