import asyncHandler from '../utils/asyncHandler.js';
import { sendSuccess, ApiError } from '../utils/apiResponse.js';
import * as videoService from '../services/video.service.js';

// POST /api/videos/generate
// Body: { text, projectId, title }
export const generateVideo = asyncHandler(async (req, res) => {
    const { text, projectId, title } = req.body;

    if (!text || !projectId) {
        throw new ApiError(400, '"text" and "projectId" are required');
    }

    const video = await videoService.createVideoFromText({
        text,
        projectId,
        userId: req.user._id,
        title,
    });

    sendSuccess(res, 202, 'Video generation started — check status via GET /api/videos/:id', video);
});

// POST /api/videos/upload
// Expects: multipart/form-data with field "sourceFile" + body { projectId, title }
export const uploadVideo = asyncHandler(async (req, res) => {
    const { projectId, title } = req.body;

    if (!req.file) {
        throw new ApiError(400, 'No file uploaded');
    }

    if (!projectId) {
        throw new ApiError(400, '"projectId" is required');
    }

    // Extract text from file path — actual extraction done by FastAPI
    const sourceFilePath = req.file.path.replace(/\\/g, '/');

    const video = await videoService.createVideoFromText({
        text: sourceFilePath,
        projectId,
        userId: req.user._id,
        title: title || req.file.originalname,
    });

    sendSuccess(res, 202, 'File uploaded and video generation started', {
        video,
        file: {
            filename: req.file.filename,
            originalName: req.file.originalname,
            size: req.file.size,
            path: sourceFilePath,
        },
    });
});

// GET /api/videos/:id
export const getVideo = asyncHandler(async (req, res) => {
    const video = await videoService.getVideo(req.params.id, req.user._id);
    sendSuccess(res, 200, 'Video retrieved', video);
});
