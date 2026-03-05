import asyncHandler from '../utils/asyncHandler.js';
import { sendSuccess, ApiError } from '../utils/apiResponse.js';
import EditHistory from '../models/EditHistory.js';
import Scene from '../models/Scene.js';
import Video from '../models/Video.js';
import Project from '../models/Project.js';

/**
 * Verify the requesting user has access through the scene → video → project chain
 */
const verifySceneAccess = async (sceneId, userId) => {
    const scene = await Scene.findById(sceneId).lean();
    if (!scene) throw new ApiError(404, 'Scene not found');

    const video = await Video.findById(scene.videoId).lean();
    if (!video) throw new ApiError(404, 'Associated video not found');

    const project = await Project.findOne({
        _id: video.projectId,
        $or: [{ owner: userId }, { collaborators: userId }],
    });
    if (!project) throw new ApiError(403, 'Access denied');

    return { scene, video };
};

// POST /api/edits/create
export const createEditHistory = asyncHandler(async (req, res) => {
    const { sceneId, videoId, editType, previousValue, newValue, aiSuggested, version } = req.body;

    if (!sceneId || !videoId || !editType || version === undefined) {
        throw new ApiError(400, '"sceneId", "videoId", "editType", and "version" are required');
    }

    await verifySceneAccess(sceneId, req.user._id);

    const EDIT_TYPES = ['script', 'visual', 'voice', 'scene-order'];
    if (!EDIT_TYPES.includes(editType)) {
        throw new ApiError(400, `"editType" must be one of: ${EDIT_TYPES.join(', ')}`);
    }

    const record = await EditHistory.create({
        sceneId,
        videoId,
        userId: req.user._id,
        editType,
        previousValue: previousValue ?? null,
        newValue: newValue ?? null,
        aiSuggested: Boolean(aiSuggested),
        version,
    });

    sendSuccess(res, 201, 'Edit history record created', record);
});

// GET /api/edits/scene/:sceneId
export const getEditsByScene = asyncHandler(async (req, res) => {
    await verifySceneAccess(req.params.sceneId, req.user._id);

    const edits = await EditHistory.find({ sceneId: req.params.sceneId })
        .populate('userId', 'name email avatar')
        .sort({ createdAt: -1 })
        .lean();

    sendSuccess(res, 200, 'Edit history retrieved', edits);
});
