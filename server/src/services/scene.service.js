import Scene from '../models/Scene.js';
import Video from '../models/Video.js';
import Project from '../models/Project.js';
import EditHistory from '../models/EditHistory.js';
import { ApiError } from '../utils/apiResponse.js';

// ─── Get All Scenes for a Video ────────────────────────────────────────────
export const getScenesByVideoId = async (videoId, userId) => {
    const video = await Video.findById(videoId).lean();
    if (!video) throw new ApiError(404, 'Video not found');

    const project = await Project.findOne({
        _id: video.projectId,
        $or: [{ owner: userId }, { collaborators: userId }],
    });
    if (!project) throw new ApiError(403, 'Access denied');

    return Scene.find({ videoId }).sort({ sceneNumber: 1 }).lean();
};

// ─── Update Scene ──────────────────────────────────────────────────────────
export const updateScene = async (sceneId, userId, updates) => {
    const ALLOWED_EDIT_TYPES = ['script', 'visual', 'voice', 'scene-order'];
    const { editType, ...fieldUpdates } = updates;

    if (!editType || !ALLOWED_EDIT_TYPES.includes(editType)) {
        throw new ApiError(400, `"editType" must be one of: ${ALLOWED_EDIT_TYPES.join(', ')}`);
    }

    const scene = await Scene.findById(sceneId);
    if (!scene) throw new ApiError(404, 'Scene not found');

    // Verify access via project chain
    const video = await Video.findById(scene.videoId).lean();
    if (!video) throw new ApiError(404, 'Associated video not found');

    const project = await Project.findOne({
        _id: video.projectId,
        $or: [{ owner: userId }, { collaborators: userId }],
    });
    if (!project) throw new ApiError(403, 'Access denied');

    // Capture snapshot for edit history
    const FIELD_MAP = {
        script: 'scriptText',
        visual: 'visualPrompt',
        voice: 'voiceoverUrl',
        'scene-order': 'sceneNumber',
    };

    const targetField = FIELD_MAP[editType];
    const previousValue = scene[targetField];
    const newValue = fieldUpdates[targetField] ?? fieldUpdates.value;

    if (newValue === undefined) {
        throw new ApiError(400, `Update must include field "${targetField}" for editType "${editType}"`);
    }

    // Bump version and apply update
    scene[targetField] = newValue;
    scene.version += 1;
    await scene.save();

    // Persist edit history
    await EditHistory.create({
        sceneId,
        videoId: scene.videoId,
        userId,
        editType,
        previousValue,
        newValue,
        aiSuggested: false,
        version: scene.version,
    });

    return scene;
};
