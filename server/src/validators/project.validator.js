import { ApiError } from '../utils/apiResponse.js';

const SOURCE_TYPES = ['research-paper', 'lecture-notes', 'report', 'text'];

// ─── Create Project Validator ───────────────────────────────────────────────
export const validateCreateProject = (req, res, next) => {
    const errors = [];
    const { title, sourceType } = req.body;

    if (!title || String(title).trim().length < 3) {
        errors.push('"title" is required and must be at least 3 characters');
    }

    if (String(title).trim().length > 200) {
        errors.push('"title" must not exceed 200 characters');
    }

    if (sourceType && !SOURCE_TYPES.includes(sourceType)) {
        errors.push(`"sourceType" must be one of: ${SOURCE_TYPES.join(', ')}`);
    }

    if (errors.length > 0) {
        return next(new ApiError(422, 'Validation failed', errors));
    }

    next();
};

// ─── Update Project Validator ───────────────────────────────────────────────
export const validateUpdateProject = (req, res, next) => {
    const errors = [];
    const { title, status, sourceType } = req.body;
    const STATUSES = ['draft', 'processing', 'completed'];

    if (title !== undefined && String(title).trim().length < 3) {
        errors.push('"title" must be at least 3 characters');
    }

    if (status !== undefined && !STATUSES.includes(status)) {
        errors.push(`"status" must be one of: ${STATUSES.join(', ')}`);
    }

    if (sourceType !== undefined && !SOURCE_TYPES.includes(sourceType)) {
        errors.push(`"sourceType" must be one of: ${SOURCE_TYPES.join(', ')}`);
    }

    if (errors.length > 0) {
        return next(new ApiError(422, 'Validation failed', errors));
    }

    next();
};
