import { Router } from 'express';
import { getScenesByVideo, updateScene } from '../controllers/scene.controller.js';
import { protect } from '../middlewares/auth.middleware.js';

const router = Router();

router.use(protect);

router.get('/video/:videoId', getScenesByVideo);
router.put('/:sceneId', updateScene);

export default router;
