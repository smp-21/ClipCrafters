import { useRef } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Sparkles, Star, Play, Zap, Mic, Video, LayoutDashboard } from 'lucide-react';
import { staggerContainer, fadeInUp, slideInRight, floatY } from '../../utils/animations.js';
import { unsplash } from '../../utils/imageLoader.js';
import ParticleField from '../ui/ParticleField.jsx';
import { useAuth } from '../../context/AuthContext.jsx';

export default function HeroSection() {
  const { isAuthenticated } = useAuth();

  return (
    <section style={{ minHeight: '100svh', position: 'relative', overflow: 'hidden', display: 'flex', alignItems: 'center' }}>
      {/* Background layers */}
      <div style={{ position: 'absolute', inset: 0, background: 'var(--gradient-hero)' }} />
      <ParticleField count={80} />
      <div className="grid-overlay" />

      {/* Gradient blobs */}
      <motion.div
        animate={{ y: [-20, 20, -20], x: [-10, 10, -10] }}
        transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        style={{
          position: 'absolute', left: '-10%', top: '20%',
          width: '50%', height: '60%', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(201,168,76,0.12) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />
      <motion.div
        animate={{ y: [20, -20, 20], x: [10, -10, 10] }}
        transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut', delay: 2 }}
        style={{
          position: 'absolute', right: '-5%', top: '10%',
          width: '35%', height: '50%', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(232,201,122,0.08) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />

      <div className="container" style={{ position: 'relative', zIndex: 10, paddingTop: 80 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 60, alignItems: 'center' }}>
          {/* LEFT — Text content */}
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            style={{ display: 'flex', flexDirection: 'column', gap: 28 }}
          >
            <motion.div variants={fadeInUp}>
              <span className="section-label">
                <Sparkles size={12} />
                AI-Powered Video Creation
              </span>
            </motion.div>

            <motion.h1
              variants={fadeInUp}
              style={{ fontSize: 'clamp(2.5rem, 5vw, 4.5rem)', fontFamily: 'var(--font-display)', fontWeight: 900, lineHeight: 1.1, letterSpacing: '-0.03em' }}
            >
              Create Expert Videos,{' '}
              <span style={{ display: 'block' }}>
                Powered by{' '}
                <em className="gradient-text" style={{ fontStyle: 'italic' }}>Agentic AI</em>
              </span>
            </motion.h1>

            <motion.p
              variants={fadeInUp}
              style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', lineHeight: 1.7, maxWidth: 480 }}
            >
              Transform research papers, reports, and lecture notes into stunning, accurate videos. AI writes, grounds, and verifies — you stay in control.
            </motion.p>

            <motion.div variants={fadeInUp} style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {isAuthenticated ? (
                <>
                  <Link to="/dashboard" className="btn-primary" data-cursor="pointer" style={{ fontSize: '1rem', padding: '14px 32px' }}>
                    <LayoutDashboard size={18} />
                    Go to Dashboard
                  </Link>
                  <Link to="/projects/create" className="btn-ghost" data-cursor="pointer" style={{ fontSize: '1rem', padding: '14px 32px' }}>
                    Create New Project
                  </Link>
                </>
              ) : (
                <>
                  <Link to="/register" className="btn-primary" data-cursor="pointer" style={{ fontSize: '1rem', padding: '14px 32px' }}>
                    Start Creating Free
                  </Link>
                  <button
                    className="btn-ghost"
                    data-cursor="pointer"
                    style={{ display: 'flex', alignItems: 'center', gap: 8 }}
                    onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}
                  >
                    <Play size={16} fill="currentColor" /> Watch Demo
                  </button>
                </>
              )}
            </motion.div>

            {/* Social proof */}
            <motion.div variants={fadeInUp} style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
              <div style={{ display: 'flex' }}>
                {[unsplash.avatar1, unsplash.avatar2, unsplash.avatar3, unsplash.avatar4].map((src, i) => (
                  <img
                    key={i}
                    src={src}
                    alt={`Creator ${i + 1}`}
                    loading="lazy"
                    style={{ width: 36, height: 36, borderRadius: '50%', border: '2px solid var(--bg-primary)', marginLeft: i === 0 ? 0 : -10, objectFit: 'cover' }}
                  />
                ))}
              </div>
              <div>
                <div style={{ display: 'flex', gap: 2, marginBottom: 2 }}>
                  {[...Array(5)].map((_, i) => <Star key={i} size={14} fill="var(--gold-primary)" color="var(--gold-primary)" />)}
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0 }}>
                  <strong style={{ color: 'var(--text-primary)' }}>Trusted by 10,000+</strong> creators
                </p>
              </div>
            </motion.div>
          </motion.div>

          {/* RIGHT — Hero visual */}
          <motion.div
            variants={slideInRight}
            initial="hidden"
            animate="visible"
            style={{ position: 'relative', display: 'flex', justifyContent: 'center' }}
            className="desktop-only-flex"
          >
            {/* Main image card */}
            <div style={{
              width: '100%', maxWidth: 500,
              borderRadius: 24,
              overflow: 'hidden',
              border: '1px solid var(--border-default)',
              boxShadow: 'var(--shadow-glow-strong)',
              position: 'relative',
            }}>
              <img
                src={unsplash.camera}
                alt="AI Video Creation"
                loading="lazy"
                style={{ width: '100%', height: 340, objectFit: 'cover', display: 'block' }}
              />
              <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(10,8,6,0.8) 0%, transparent 60%)', pointerEvents: 'none' }} />
            </div>

            {/* Floating chip — AI Processing */}
            <motion.div
              variants={floatY}
              animate="animate"
              className="glass-card"
              style={{
                position: 'absolute', top: -20, left: -20,
                padding: '12px 16px',
                display: 'flex', alignItems: 'center', gap: 10,
                minWidth: 180,
              }}
            >
              <motion.div
                animate={{ scale: [1, 1.2, 1], opacity: [0.7, 1, 0.7] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                style={{ width: 10, height: 10, borderRadius: '50%', background: '#4ade80', flexShrink: 0 }}
              />
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>AI Processing...</div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Scene 3 of 8</div>
              </div>
            </motion.div>

            {/* Floating stats card */}
            <motion.div
              animate={{ y: [8, -8, 8] }}
              transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
              className="glass-card"
              style={{
                position: 'absolute', bottom: -20, right: -20,
                padding: '14px 20px',
                display: 'flex', gap: 20,
              }}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.2rem', fontFamily: 'var(--font-display)', fontWeight: 800 }} className="gradient-text">4K</div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>OUTPUT</div>
              </div>
              <div style={{ width: 1, background: 'var(--border-default)' }} />
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.2rem', fontFamily: 'var(--font-display)', fontWeight: 800 }} className="gradient-text">98%</div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>ACCURACY</div>
              </div>
            </motion.div>
          </motion.div>
        </div>

        {/* Feature badge row */}
        <motion.div
          initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.7 }}
          style={{
            display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16,
            marginTop: 64,
          }}
        >
          {[
            { icon: Video, title: '4K Output', subtitle: 'Ultra HD quality' },
            { icon: Mic, title: 'Voice Sync', subtitle: 'Perfect lip sync' },
            { icon: Zap, title: 'AI Scripts', subtitle: '10x faster creation' },
          ].map(({ icon: Icon, title, subtitle }) => (
            <div key={title} className="glass-card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: 'var(--gold-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Icon size={18} color="var(--gold-primary)" />
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)' }}>{title}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{subtitle}</div>
              </div>
            </div>
          ))}
        </motion.div>
      </div>

      <style>{`
        @media (max-width: 767px) {
          .desktop-only-flex { display: none; }
        }
        @media (max-width: 1023px) {
          .hero-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </section>
  );
}
