import asyncHandler from '../utils/asyncHandler.js';
import { sendSuccess, ApiError } from '../utils/apiResponse.js';
import * as authService from '../services/auth.service.js';
import { sendOTPviaSMS, sendOTPviaEmail, verifyOTP } from '../services/notification/otp.service.js';

// ─── Register ──────────────────────────────────────────────────────────────
// POST /api/auth/register
export const register = asyncHandler(async (req, res) => {
    const { name, email, password } = req.body;
    const result = await authService.registerUser({ name, email, password });
    sendSuccess(res, 201, 'Account created successfully', result);
});

// ─── Login ─────────────────────────────────────────────────────────────────
// POST /api/auth/login
export const login = asyncHandler(async (req, res) => {
    const { email, password } = req.body;
    const result = await authService.loginUser({ email, password });
    sendSuccess(res, 200, 'Login successful', result);
});

// ─── Get Own Profile ───────────────────────────────────────────────────────
// GET /api/auth/me  [protected]
export const getMe = asyncHandler(async (req, res) => {
    const user = await authService.getUserProfile(req.user._id);
    sendSuccess(res, 200, 'User profile retrieved', user);
});

// ─── Send OTP ─────────────────────────────────────────────────────────────
// POST /api/auth/send-otp  [protected]
// Body: { method: 'sms' | 'email', phone?, email? }
export const sendOtp = asyncHandler(async (req, res) => {
    const { method, phone, email: emailAddr } = req.body;
    const userId = req.user._id;

    if (!method || !['sms', 'email'].includes(method)) {
        throw new ApiError(400, '"method" must be "sms" or "email"');
    }

    if (method === 'sms') {
        if (!phone) throw new ApiError(400, '"phone" is required for SMS delivery');
        const result = await sendOTPviaSMS(userId, phone);
        return sendSuccess(res, 200, `OTP sent via SMS to ${phone}`, { sid: result.sid });
    }

    // method === 'email'
    const recipient = emailAddr || req.user.email;
    if (!recipient) throw new ApiError(400, '"email" is required for email delivery');
    const result = await sendOTPviaEmail(userId, recipient);
    sendSuccess(res, 200, `OTP sent via email to ${recipient}`, { id: result.id });
});

// ─── Verify OTP ────────────────────────────────────────────────────────────
// POST /api/auth/verify-otp  [protected]
// Body: { otp: '482193', method: 'sms' | 'email' }
export const verifyOtp = asyncHandler(async (req, res) => {
    const { otp, method } = req.body;
    const userId = req.user._id;

    if (!otp || !method) {
        throw new ApiError(400, '"otp" and "method" are required');
    }

    if (!['sms', 'email'].includes(method)) {
        throw new ApiError(400, '"method" must be "sms" or "email"');
    }

    if (!/^\d{6}$/.test(String(otp))) {
        throw new ApiError(400, '"otp" must be a 6-digit number');
    }

    const isValid = await verifyOTP(userId, otp, method);

    if (!isValid) {
        throw new ApiError(401, 'Invalid or expired OTP');
    }

    sendSuccess(res, 200, 'OTP verified successfully', { verified: true });
});
