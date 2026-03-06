import { motion } from 'framer-motion';
import Navbar from '../components/layout/Navbar.jsx';
import HeroSection from '../components/home/HeroSection.jsx';
import FeatureCards from '../components/home/FeatureCards.jsx';
import StatsSection from '../components/home/StatsSection.jsx';
import DemoSection from '../components/home/DemoSection.jsx';
import TestimonialsSlider from '../components/home/TestimonialsSlider.jsx';
import PricingCards from '../components/home/PricingCards.jsx';
import CTABanner from '../components/home/CTABanner.jsx';
import { pageTransition } from '../utils/animations.js';

function Footer() {
  return (
    <footer style={{ background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-default)', padding: '40px 0' }}>
      <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 8, background: 'var(--gradient-gold)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M15 10l4.553-2.276A1 1 0 0121 8.67v6.66a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" stroke="#0a0806" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem' }}>ClipCrafters</span>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
          © 2026 ClipCrafters. All rights reserved.
        </p>
        <div style={{ display: 'flex', gap: 20 }}>
          {['Privacy', 'Terms', 'Contact'].map((l) => (
            <a key={l} href="#" style={{ fontSize: '0.8rem', color: 'var(--text-muted)', transition: 'color 0.2s' }}
              onMouseEnter={(e) => e.target.style.color = 'var(--gold-primary)'}
              onMouseLeave={(e) => e.target.style.color = 'var(--text-muted)'}
            >{l}</a>
          ))}
        </div>
      </div>
    </footer>
  );
}

export default function Home() {
  return (
    <motion.div {...pageTransition}>
      <Navbar />
      <main>
        <HeroSection />
        <FeatureCards />
        <StatsSection />
        <DemoSection />
        <TestimonialsSlider />
        <PricingCards />
        <CTABanner />
      </main>
      <Footer />
    </motion.div>
  );
}
