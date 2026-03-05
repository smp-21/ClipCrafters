import asyncHandler from '../utils/asyncHandler.js';
import { sendSuccess } from '../utils/apiResponse.js';
import * as sceneService from '../services/scene.service.js';

// GET /api/scenes/video/:videoId
export const getScenesByVideo = asyncHandler(async (req, res) => {
    const scenes = await sceneService.getScenesByVideoId(req.params.videoId, req.user._id);
    sendSuccess(res, 200, 'Scenes retrieved', scenes);
});

// PUT /api/scenes/:sceneId
// Body: { editType, scriptText | visualPrompt | voiceoverUrl | sceneNumber }
export const updateScene = asyncHandler(async (req, res) => {
    const scene = await sceneService.updateScene(req.params.sceneId, req.user._id, req.body);
    sendSuccess(res, 200, 'Scene updated and edit history recorded', scene);
});
