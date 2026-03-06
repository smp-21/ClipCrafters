import { motion } from 'framer-motion';
import { Film, CheckCircle2, Layers, Zap } from 'lucide-react';
import { STATS } from '../../utils/seedData.js';
import { useAnimatedCounter } from '../../hooks/index.js';

const iconMap = { Film, CheckCircle2, Layers, Zap };

function StatItem({ stat }) {
  const Icon = iconMap[stat.icon] || Film;
  const { count, ref } = useAnimatedCounter(stat.value, 2000, true);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6 }}
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16,
        padding: '40px 20px', flex: 1, textAlign: 'center', position: 'relative',
      }}
    >
      <div style={{
        width: 52, height: 52, borderRadius: '50%',
        background: 'var(--gold-subtle)',
        border: '1px solid var(--border-default)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Icon size={22} color="var(--gold-primary)" />
      </div>

      <div>
        <div style={{ fontSize: 'clamp(2.5rem, 5vw, 3.5rem)', fontFamily: 'var(--font-display)', fontWeight: 900, lineHeight: 1 }}
          className="gradient-text"
        >
          {count.toLocaleString()}<span style={{ fontSize: '0.6em' }}>{stat.suffix}</span>
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', fontFamily: 'var(--font-body)', fontWeight: 500, marginTop: 6 }}>
          {stat.label}
        </div>
      </div>
    </motion.div>
  );
}

export default function StatsSection() {
  return (
    <section style={{ position: 'relative', overflow: 'hidden' }}>
      {/* Gold borders */}
      <div className="divider-gold" />
      <div style={{ background: 'var(--bg-secondary)', padding: '20px 0' }}>
        <div className="container">
          <div style={{
            display: 'flex', flexWrap: 'wrap',
            justifyContent: 'center',
          }}>
            {STATS.map((stat, i) => (
              <div key={stat.label} style={{ display: 'flex', alignItems: 'stretch', flex: '1 1 200px' }}>
                <StatItem stat={stat} />
                {i < STATS.length - 1 && (
                  <div style={{ width: 1, background: 'var(--border-default)', margin: '20px 0' }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="divider-gold" />
    </section>
  );
}
