import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart3, FolderOpen, PlusCircle, User, LogOut, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext.jsx';
import { getInitials } from '../../utils/formatters.js';
import ThemeToggle from '../ui/ThemeToggle.jsx';

const NAV = [
  { label: 'Dashboard', icon: BarChart3, route: '/dashboard' },
  { label: 'Projects', icon: FolderOpen, route: '/projects/create', exact: false },
  { label: 'Create New', icon: PlusCircle, route: '/projects/create', highlighted: true },
  { label: 'Profile', icon: User, route: '/profile' },
];

export default function Sidebar({ isMobileOpen, onMobileClose }) {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/'); };

  const SidebarContent = ({ mobile = false }) => (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Logo */}
      <div style={{ padding: collapsed ? '20px 16px' : '20px 20px', borderBottom: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'space-between' }}>
        {!collapsed && (
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none' }}>
            <div style={{ width: 28, height: 28, borderRadius: 8, background: 'var(--gradient-gold)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M15 10l4.553-2.276A1 1 0 0121 8.67v6.66a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" stroke="#0a0806" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
              Clip<span style={{ background: 'var(--gradient-gold)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Crafters</span>
            </span>
          </Link>
        )}
        {mobile && (
          <button onClick={onMobileClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', marginLeft: 'auto' }}>
            <X size={20} />
          </button>
        )}
        {!mobile && collapsed && (
          <div style={{ width: 28, height: 28, borderRadius: 8, background: 'var(--gradient-gold)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M15 10l4.553-2.276A1 1 0 0121 8.67v6.66a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" stroke="#0a0806" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {NAV.map(({ label, icon: Icon, route, highlighted }) => {
          const active = location.pathname === route;
          return (
            <Link
              key={label}
              to={route}
              onClick={mobile ? onMobileClose : undefined}
              title={collapsed ? label : undefined}
              data-cursor="pointer"
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: collapsed ? '10px' : '10px 12px',
                borderRadius: 10, textDecoration: 'none',
                justifyContent: collapsed ? 'center' : 'flex-start',
                background: active ? 'var(--gold-subtle)' : highlighted ? 'var(--gold-subtle)' : 'transparent',
                border: active ? '1px solid var(--border-active)' : highlighted ? '1px solid var(--border-default)' : '1px solid transparent',
                color: active || highlighted ? 'var(--gold-light)' : 'var(--text-secondary)',
                fontFamily: 'var(--font-body)', fontWeight: 500,
                fontSize: '0.875rem', transition: 'all 0.2s',
                position: 'relative',
              }}
              onMouseEnter={(e) => { if (!active) { e.currentTarget.style.background = 'var(--bg-elevated)'; e.currentTarget.style.color = 'var(--text-primary)'; } }}
              onMouseLeave={(e) => { if (!active) { e.currentTarget.style.background = highlighted ? 'var(--gold-subtle)' : 'transparent'; e.currentTarget.style.color = active || highlighted ? 'var(--gold-light)' : 'var(--text-secondary)'; } }}
            >
              {active && <div style={{ position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)', width: 3, height: '60%', background: 'var(--gradient-gold)', borderRadius: '0 2px 2px 0' }} />}
              <Icon size={18} style={{ flexShrink: 0 }} />
              {!collapsed && <span style={{ whiteSpace: 'nowrap' }}>{label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div style={{ padding: collapsed ? '12px 8px' : '12px', borderTop: '1px solid var(--border-default)', display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ display: 'flex', justifyContent: collapsed ? 'center' : 'flex-start' }}>
          <ThemeToggle size="sm" />
        </div>

        {!collapsed && user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px', borderRadius: 10, background: 'var(--bg-elevated)' }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--gradient-gold)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-inverse)' }}>
              {getInitials(user.name || 'U')}
            </div>
            <div style={{ overflow: 'hidden', flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: '0.8rem', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user.name}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user.role}</div>
            </div>
          </div>
        )}

        <button
          onClick={handleLogout}
          data-cursor="pointer"
          style={{
            display: 'flex', alignItems: 'center', gap: 10,
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: collapsed ? '10px' : '10px 12px',
            borderRadius: 10, background: 'none', border: '1px solid transparent',
            cursor: 'pointer', color: 'var(--text-muted)',
            fontFamily: 'var(--font-body)', fontSize: '0.875rem',
            transition: 'all 0.2s', width: '100%',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(239,68,68,0.08)'; e.currentTarget.style.color = '#f87171'; e.currentTarget.style.borderColor = 'rgba(239,68,68,0.2)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.borderColor = 'transparent'; }}
        >
          <LogOut size={16} style={{ flexShrink: 0 }} />
          {!collapsed && 'Logout'}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <motion.aside
        animate={{ width: collapsed ? 68 : 240 }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        style={{
          position: 'fixed', top: 0, left: 0, bottom: 0,
          background: 'var(--bg-secondary)',
          borderRight: '1px solid var(--border-default)',
          zIndex: 50, overflow: 'hidden',
          display: 'flex', flexDirection: 'column',
        }}
        className="sidebar-desktop"
      >
        <SidebarContent />
        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          data-cursor="pointer"
          style={{
            position: 'absolute', top: '50%', right: -14,
            transform: 'translateY(-50%)',
            width: 28, height: 28, borderRadius: '50%',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-default)',
            cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--text-muted)', zIndex: 10,
          }}
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </motion.aside>

      {/* Mobile drawer */}
      <AnimatePresence>
        {isMobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={onMobileClose}
              style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 199 }}
            />
            <motion.aside
              initial={{ x: '-100%' }} animate={{ x: 0 }} exit={{ x: '-100%' }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              style={{
                position: 'fixed', top: 0, left: 0, bottom: 0,
                width: 240,
                background: 'var(--bg-secondary)',
                borderRight: '1px solid var(--border-default)',
                zIndex: 200,
              }}
            >
              <SidebarContent mobile />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <style>{`
        @media (max-width: 767px) { .sidebar-desktop { display: none; } }
      `}</style>
    </>
  );
}
