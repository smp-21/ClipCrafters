import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { CheckCircle2, Sun, Moon, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import { useTheme } from '../context/ThemeContext.jsx';
import { authService, projectService } from '../services/index.js';
import Sidebar from '../components/layout/Sidebar.jsx';
import { Spinner } from '../components/ui/index.jsx';
import { getInitials, formatDate } from '../utils/formatters.js';
import { pageTransition, staggerContainer, fadeInUp } from '../utils/animations.js';

export default function Profile() {
  const { user, updateUser } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [stats, setStats] = useState({ total: 0, completed: 0 });
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [sending, setSending] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);
  const [deleteConfirm, setDeleteConfirm] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    projectService.getAll({ limit: 100 }).then((res) => {
      const projects = res.data.data?.projects || res.data.data || [];
      setStats({ total: projects.length, completed: projects.filter((p) => p.status === 'completed').length });
    }).catch(() => {});
  }, []);

  const handleSendOtp = async () => {
    setSending(true);
    try {
      await authService.sendOtp({ method: 'email', email: user?.email });
      setOtpSent(true);
      toast.success(`OTP sent to ${user?.email}`);
      // Countdown
      setResendTimer(60);
      const interval = setInterval(() => setResendTimer((t) => { if (t <= 1) { clearInterval(interval); return 0; } return t - 1; }), 1000);
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to send OTP');
    } finally { setSending(false); }
  };

  const handleVerifyOtp = async () => {
    const code = otp.join('');
    if (code.length < 6) { toast.error('Enter 6-digit OTP'); return; }
    setVerifying(true);
    try {
      await authService.verifyOtp({ otp: code, method: 'email' });
      toast.success('Email verified!');
      updateUser({ isVerified: true });
      setOtpSent(false);
      setOtp(['', '', '', '', '', '']);
    } catch (err) {
      toast.error(err.response?.data?.message || 'Invalid OTP');
    } finally { setVerifying(false); }
  };

  const handleOtpChange = (val, idx) => {
    const next = [...otp];
    next[idx] = val.slice(-1);
    setOtp(next);
    if (val && idx < 5) document.getElementById(`otp-${idx + 1}`)?.focus();
  };

  return (
    <motion.div {...pageTransition} style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{ flex: 1, marginLeft: 240, padding: '32px', maxWidth: 800 }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.8rem', fontWeight: 800, marginBottom: 32 }}>Account Settings</h1>

        <motion.div variants={staggerContainer} initial="hidden" animate="visible" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Avatar & Name */}
          <motion.div variants={fadeInUp} className="glass-card" style={{ padding: '28px', display: 'flex', alignItems: 'center', gap: 24 }}>
            <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'var(--gradient-gold)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem', fontWeight: 800, color: 'var(--text-inverse)', flexShrink: 0 }}>
              {getInitials(user?.name || 'U')}
            </div>
            <div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>{user?.name}</h2>
              <p style={{ color: 'var(--text-muted)', margin: '4px 0 8px' }}>{user?.email}</p>
              {user?.isVerified !== false ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#4ade80', fontSize: '0.8rem' }}>
                  <CheckCircle2 size={14} /> Verified account
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#fbbf24', fontSize: '0.8rem' }}>
                  <AlertCircle size={14} /> Unverified
                </div>
              )}
            </div>
          </motion.div>

          {/* Account Info */}
          <motion.div variants={fadeInUp} className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>Account Information</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { label: 'Full Name', value: user?.name },
                { label: 'Email', value: user?.email },
                { label: 'Role', value: user?.role || 'user' },
                { label: 'Member Since', value: formatDate(user?.createdAt) || 'N/A' },
              ].map(({ label, value }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 12, borderBottom: '1px solid var(--border-default)' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{label}</span>
                  <span style={{ fontSize: '0.875rem', color: 'var(--text-primary)', fontWeight: 500 }}>{value || '—'}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* OTP Verification */}
          {user?.isVerified === false && (
            <motion.div variants={fadeInUp} className="glass-card" style={{ padding: '24px', border: '1px solid rgba(251,191,36,0.3)' }}>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 700, marginBottom: 8 }}>
                <AlertCircle size={18} color="#fbbf24" style={{ marginRight: 8, verticalAlign: 'middle' }} />
                Verify Your Email
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 16 }}>
                Verify your email to unlock all features.
              </p>
              {!otpSent ? (
                <button onClick={handleSendOtp} disabled={sending} className="btn-primary btn-sm" data-cursor="pointer">
                  {sending ? <><Spinner size={14} /> Sending...</> : 'Send Verification Code'}
                </button>
              ) : (
                <div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 12 }}>Enter the 6-digit code sent to {user?.email}</p>
                  <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                    {otp.map((v, i) => (
                      <input
                        key={i}
                        id={`otp-${i}`}
                        type="text"
                        maxLength={1}
                        value={v}
                        onChange={(e) => handleOtpChange(e.target.value, i)}
                        data-cursor="text"
                        style={{
                          width: 44, height: 52, textAlign: 'center', borderRadius: 8,
                          border: '1px solid var(--border-default)', background: 'var(--bg-elevated)',
                          color: 'var(--text-primary)', fontFamily: 'var(--font-mono)',
                          fontSize: '1.4rem', fontWeight: 700, outline: 'none',
                          transition: 'border-color 0.2s',
                        }}
                        onFocus={(e) => e.target.style.borderColor = 'var(--gold-primary)'}
                        onBlur={(e) => e.target.style.borderColor = 'var(--border-default)'}
                      />
                    ))}
                  </div>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                    <button onClick={handleVerifyOtp} disabled={verifying} className="btn-primary btn-sm" data-cursor="pointer">
                      {verifying ? <><Spinner size={14} /> Verifying...</> : 'Verify'}
                    </button>
                    {resendTimer > 0 ? (
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Resend in {resendTimer}s</span>
                    ) : (
                      <button onClick={handleSendOtp} style={{ background: 'none', border: 'none', color: 'var(--gold-primary)', cursor: 'pointer', fontSize: '0.8rem' }}>Resend OTP</button>
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Theme */}
          <motion.div variants={fadeInUp} className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>Appearance</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {[
                { key: 'dark', label: 'Dark', icon: Moon, desc: 'Cinema dark golden theme' },
                { key: 'light', label: 'Light', icon: Sun, desc: 'Bright and airy theme' },
              ].map(({ key, label, icon: Icon, desc }) => (
                <button
                  key={key}
                  onClick={() => key !== theme && toggleTheme()}
                  data-cursor="pointer"
                  style={{
                    padding: '16px', borderRadius: 12,
                    border: `2px solid ${theme === key ? 'var(--gold-primary)' : 'var(--border-default)'}`,
                    background: theme === key ? 'var(--gold-subtle)' : 'var(--bg-elevated)',
                    cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s',
                    display: 'flex', gap: 12, alignItems: 'center',
                  }}
                >
                  <Icon size={20} color={theme === key ? 'var(--gold-primary)' : 'var(--text-muted)'} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem', color: theme === key ? 'var(--gold-light)' : 'var(--text-primary)' }}>{label}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{desc}</div>
                  </div>
                </button>
              ))}
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div variants={fadeInUp} className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>Your Activity</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              {[
                { label: 'Total Projects', value: stats.total },
                { label: 'Videos Completed', value: stats.completed },
              ].map(({ label, value }) => (
                <div key={label} style={{ textAlign: 'center', padding: '16px', background: 'var(--bg-elevated)', borderRadius: 10 }}>
                  <div style={{ fontSize: '2rem', fontFamily: 'var(--font-display)', fontWeight: 900 }} className="gradient-text">{value}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{label}</div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Danger Zone */}
          <motion.div variants={fadeInUp} style={{ padding: '24px', borderRadius: 16, border: '1px solid rgba(239,68,68,0.2)', background: 'rgba(239,68,68,0.03)' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 700, color: '#f87171', marginBottom: 8 }}>Danger Zone</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: 16 }}>Permanently delete your account and all data.</p>
            <button onClick={() => setShowDeleteModal(true)} className="btn-danger btn-sm" data-cursor="pointer">Delete Account</button>
          </motion.div>
        </motion.div>
      </main>

      {/* Delete modal */}
      {showDeleteModal && (
        <div className="modal-overlay">
          <div className="modal-box" style={{ maxWidth: 380 }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', color: '#f87171', marginBottom: 8 }}>Delete Account?</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: 16 }}>This is irreversible. Type your email to confirm.</p>
            <input className="input-neu" placeholder={user?.email} value={deleteConfirm} onChange={(e) => setDeleteConfirm(e.target.value)} data-cursor="text" style={{ marginBottom: 16 }} />
            <div style={{ display: 'flex', gap: 12 }}>
              <button disabled={deleteConfirm !== user?.email} className="btn-danger" data-cursor="pointer" onClick={() => toast.error('Account deletion requires server action')}>Delete Account</button>
              <button className="btn-ghost" onClick={() => setShowDeleteModal(false)} data-cursor="pointer">Cancel</button>
            </div>
          </div>
        </div>
      )}

      <style>{`@media (max-width: 1023px) { main[style] { margin-left: 0 !important; } }`}</style>
    </motion.div>
  );
}
