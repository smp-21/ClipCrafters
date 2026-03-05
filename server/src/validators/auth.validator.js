import { ApiError } from '../utils/apiResponse.js';

// ─── Helpers ───────────────────────────────────────────────────────────────
const isValidEmail = (email) => /^\S+@\S+\.\S+$/.test(email);

const validate = (schema) => (req, res, next) => {
    const errors = [];

    for (const [field, rules] of Object.entries(schema)) {
        const value = req.body[field];

        if (rules.required && (value === undefined || value === '')) {
            errors.push(`"${field}" is required`);
            continue;
        }

        if (value === undefined || value === '') continue; // optional, skip remaining checks

        if (rules.type === 'email' && !isValidEmail(value)) {
            errors.push(`"${field}" must be a valid email address`);
        }

        if (rules.minLength && String(value).length < rules.minLength) {
            errors.push(`"${field}" must be at least ${rules.minLength} characters`);
        }

        if (rules.maxLength && String(value).length > rules.maxLength) {
            errors.push(`"${field}" must not exceed ${rules.maxLength} characters`);
        }

        if (rules.enum && !rules.enum.includes(value)) {
            errors.push(`"${field}" must be one of: ${rules.enum.join(', ')}`);
        }
    }

    if (errors.length > 0) {
        return next(new ApiError(422, 'Validation failed', errors));
    }

    next();
};

// ─── Auth Validators ────────────────────────────────────────────────────────

export const validateRegister = validate({
    name: { required: true, minLength: 2, maxLength: 100 },
    email: { required: true, type: 'email' },
    password: { required: true, minLength: 8, maxLength: 128 },
});

export const validateLogin = validate({
    email: { required: true, type: 'email' },
    password: { required: true, minLength: 1 },
});
