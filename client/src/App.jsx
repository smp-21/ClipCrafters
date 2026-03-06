import { Suspense, lazy } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import ProtectedRoute from './components/common/ProtectedRoute.jsx';
import Loader from './components/ui/Loader.jsx';
import CommandPalette from './components/ui/CommandPalette.jsx';
import CustomCursor from './components/ui/CustomCursor.jsx';
import { useCommandPalette } from './hooks/index.js';
import { useEffect } from 'react';

// Lazy page imports
const Home = lazy(() => import('./pages/Home.jsx'));
const Login = lazy(() => import('./pages/Login.jsx'));
const Register = lazy(() => import('./pages/Register.jsx'));
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'));
const ProjectCreate = lazy(() => import('./pages/ProjectCreate.jsx'));
const ProjectDetails = lazy(() => import('./pages/ProjectDetails.jsx'));
const VideoEditor = lazy(() => import('./pages/VideoEditor.jsx'));
const SceneEditor = lazy(() => import('./pages/SceneEditor.jsx'));
const Profile = lazy(() => import('./pages/Profile.jsx'));
const NotFound = lazy(() => import('./pages/NotFound.jsx'));

// Keyboard listener for command palette registration
function CommandPaletteListener() {
  const { isOpen, setIsOpen } = useCommandPalette();
  return null;
}

export default function App() {
  const location = useLocation();

  // Scroll-to-top on route change
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [location.pathname]);

  return (
    <>
      <CustomCursor />
      <CommandPalette />

      <AnimatePresence mode="wait">
        <Suspense fallback={<Loader />}>
          <Routes location={location} key={location.pathname}>
            {/* Public routes */}
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected routes */}
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/projects/create" element={<ProtectedRoute><ProjectCreate /></ProtectedRoute>} />
            <Route path="/projects/:id" element={<ProtectedRoute><ProjectDetails /></ProtectedRoute>} />
            <Route path="/editor/:id" element={<ProtectedRoute><VideoEditor /></ProtectedRoute>} />
            <Route path="/scenes/:id" element={<ProtectedRoute><SceneEditor /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />

            {/* 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </AnimatePresence>
    </>
  );
}
