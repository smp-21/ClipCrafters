import { Router } from 'express';
import {
    register,
    login,
    getMe,
    sendOtp,
    verifyOtp,
} from '../controllers/auth.controller.js';
import { protect } from '../middlewares/auth.middleware.js';
import { validateRegister, validateLogin } from '../validators/auth.validator.js';
import { authLimiter } from '../middlewares/rateLimit.middleware.js';

const router = Router();

// ── Public ──────────────────────────────────────────────────────────────────
router.post('/register', authLimiter, validateRegister, register);
router.post('/login', authLimiter, validateLogin, login);

// ── Protected ───────────────────────────────────────────────────────────────
router.get('/me', protect, getMe);
router.post('/send-otp', protect, authLimiter, sendOtp);
router.post('/verify-otp', protect, authLimiter, verifyOtp);

export default router;
