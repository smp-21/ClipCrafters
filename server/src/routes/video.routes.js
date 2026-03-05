import { Router } from 'express';
import { generateVideo, uploadVideo, getVideo } from '../controllers/video.controller.js';
import { protect } from '../middlewares/auth.middleware.js';
import upload, { handleMulterError } from '../middlewares/upload.middleware.js';

const router = Router();

router.use(protect);

router.post('/generate', generateVideo);
router.post('/upload', upload.single('sourceFile'),
    handleMulterError, uploadVideo);
router.get('/:id', getVideo);

export default router;
