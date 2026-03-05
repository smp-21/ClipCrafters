import { Router } from 'express';
import { createEditHistory, getEditsByScene } from '../controllers/edit.controller.js';
import { protect } from '../middlewares/auth.middleware.js';

const router = Router();

router.use(protect);

router.post('/create', createEditHistory);
router.get('/scene/:sceneId', getEditsByScene);

export default router;
