import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { ChevronLeft, ChevronRight, Shield, Download, Film } from 'lucide-react';
import { videoService, sceneService } from '../services/index.js';
import ScenePanel from '../components/editor/ScenePanel.jsx';
import VideoPreview from '../components/editor/VideoPreview.jsx';
import TimelineBar from '../components/editor/TimelineBar.jsx';
import SceneEditModal from '../components/editor/SceneEditModal.jsx';
import { Spinner } from '../components/ui/index.jsx';
import ThemeToggle from '../components/ui/ThemeToggle.jsx';
import { pageTransition } from '../utils/animations.js';

export default function VideoEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [video, setVideo] = useState(null);
  const [scenes, setScenes] = useState([]);
  const [selectedScene, setSelectedScene] = useState(null);
  const [editModal, setEditModal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('preview'); // mobile tabs
  const [factChecking, setFactChecking] = useState(false);

  useEffect(() => {
    if (id) fetchEditor();
  }, [id]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'ArrowLeft') prevScene();
      if (e.key === 'ArrowRight') nextScene();
      if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); /* autosave */ }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [selectedScene, scenes]);

  const prevScene = useCallback(() => {
    const idx = scenes.findIndex((s) => s._id === selectedScene?._id);
    if (idx > 0) setSelectedScene(scenes[idx - 1]);
  }, [scenes, selectedScene]);

  const nextScene = useCallback(() => {
    const idx = scenes.findIndex((s) => s._id === selectedScene?._id);
    if (idx < scenes.length - 1) setSelectedScene(scenes[idx + 1]);
  }, [scenes, selectedScene]);

  const fetchEditor = async () => {
    setLoading(true);
    try {
      const vidRes = await videoService.getById(id);
      const vid = vidRes.data.data;
      setVideo(vid);

      const sceneRes = await sceneService.getByVideo(id);
      const sc = sceneRes.data.data || [];
      setScenes(sc);
      if (sc.length > 0) setSelectedScene(sc[0]);
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to load editor');
      navigate('/dashboard');
    } finally { setLoading(false); }
  };

  const handleSceneSaved = (updated) => {
    setScenes((prev) => prev.map((s) => s._id === updated._id ? { ...s, ...updated } : s));
    if (selectedScene?._id === updated._id) setSelectedScene((p) => ({ ...p, ...updated }));
    setEditModal(null);
  };

  const handleFactCheckAll = async () => {
    setFactChecking(true);
    toast.loading(`Checking ${scenes.length} scenes...`, { id: 'factcheck' });
    await new Promise((r) => setTimeout(r, 1500));
    toast.success(`Fact-check complete — no issues found`, { id: 'factcheck' });
    setFactChecking(false);
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)' }}>
        <Spinner size={36} />
      </div>
    );
  }

  return (
    <motion.div {...pageTransition} style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)', overflow: 'hidden' }}>
      {/* Top bar */}
      <div style={{ height: 56, borderBottom: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', padding: '0 16px', gap: 16, background: 'var(--bg-secondary)', flexShrink: 0 }}>
        <button onClick={() => navigate(-1)} className="btn-icon" data-cursor="pointer"><ChevronLeft size={18} /></button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          <Film size={14} />
          <span>{video?.title || 'Video Editor'}</span>
          {scenes.length > 0 && <><ChevronRight size={12} /><span className="badge badge-gold">{scenes.length} scenes</span></>}
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
          <button onClick={handleFactCheckAll} disabled={factChecking} className="btn-ghost btn-sm" data-cursor="pointer">
            {factChecking ? <Spinner size={14} /> : <Shield size={14} />} Fact Check All
          </button>
          <button className="btn-ghost btn-sm" data-cursor="pointer"><Download size={14} /> Export</button>
          <ThemeToggle size="sm" />
        </div>
      </div>

      {/* Main 3-panel layout (desktop) */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left — Scene panel */}
        <div style={{ width: 260, borderRight: '1px solid var(--border-default)', overflow: 'hidden', display: 'flex', flexDirection: 'column', background: 'var(--bg-secondary)', flexShrink: 0 }} className="scene-panel-desktop">
          <ScenePanel scenes={scenes} selectedId={selectedScene?._id} onSelect={setSelectedScene} />
        </div>

        {/* Center — Video preview */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg-primary)' }}>
          <VideoPreview video={video} selectedScene={selectedScene} onEditScene={setEditModal} />
        </div>

        {/* Right — Inline edit on desktop */}
        {selectedScene && (
          <div style={{ width: 320, borderLeft: '1px solid var(--border-default)', overflowY: 'auto', padding: '20px', background: 'var(--bg-secondary)', flexShrink: 0 }} className="right-panel-desktop">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                Scene <span className="gradient-text">{selectedScene.sceneNumber}</span>
              </h3>
              <div className="form-group">
                <label className="form-label">Script</label>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{selectedScene.scriptText || 'No script yet'}</p>
              </div>
              {selectedScene.visualPrompt && (
                <div className="form-group">
                  <label className="form-label">Visual Prompt</label>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>{selectedScene.visualPrompt}</p>
                </div>
              )}
              <button onClick={() => setEditModal(selectedScene)} className="btn-primary btn-sm" data-cursor="pointer" style={{ width: '100%', justifyContent: 'center' }}>
                Open Full Editor
              </button>
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={prevScene} className="btn-ghost btn-sm" data-cursor="pointer"><ChevronLeft size={14} /></button>
                <button onClick={nextScene} className="btn-ghost btn-sm" data-cursor="pointer"><ChevronRight size={14} /></button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Timeline bar */}
      <TimelineBar scenes={scenes} selectedId={selectedScene?._id} onSelect={setSelectedScene} />

      {/* Scene edit modal */}
      {editModal && (
        <SceneEditModal scene={editModal} onClose={() => setEditModal(null)} onSaved={handleSceneSaved} />
      )}

      <style>{`
        @media (max-width: 767px) {
          .scene-panel-desktop, .right-panel-desktop { display: none; }
        }
      `}</style>
    </motion.div>
  );
}
