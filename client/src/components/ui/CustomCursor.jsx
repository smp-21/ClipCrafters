import { useEffect, useRef, useState } from 'react';
import { motion, useSpring } from 'framer-motion';

export default function CustomCursor() {
  const [isPointer, setIsPointer] = useState(false);
  const [isText, setIsText] = useState(false);
  const [isHidden, setIsHidden] = useState(true);
  const mouseX = useRef(0);
  const mouseY = useRef(0);

  const outerX = useSpring(0, { stiffness: 120, damping: 20 });
  const outerY = useSpring(0, { stiffness: 120, damping: 20 });
  const innerX = useSpring(0, { stiffness: 800, damping: 35 });
  const innerY = useSpring(0, { stiffness: 800, damping: 35 });

  useEffect(() => {
    // Only show on pointer devices
    if (window.matchMedia('(hover: none)').matches) return;

    document.body.classList.add('no-cursor');

    const move = (e) => {
      mouseX.current = e.clientX;
      mouseY.current = e.clientY;
      outerX.set(e.clientX - 20);
      outerY.set(e.clientY - 20);
      innerX.set(e.clientX - 4);
      innerY.set(e.clientY - 4);
      setIsHidden(false);
    };

    const over = (e) => {
      const target = e.target;
      const isPtr = target.matches('a, button, [data-cursor="pointer"], label, select, input[type=checkbox], input[type=radio]');
      const isTxt = target.matches('input, textarea, [data-cursor="text"]');
      setIsPointer(isPtr);
      setIsText(isTxt);
    };

    const leave = () => setIsHidden(true);
    const enter = () => setIsHidden(false);

    window.addEventListener('mousemove', move);
    window.addEventListener('mouseover', over);
    document.addEventListener('mouseleave', leave);
    document.addEventListener('mouseenter', enter);

    return () => {
      document.body.classList.remove('no-cursor');
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseover', over);
      document.removeEventListener('mouseleave', leave);
      document.removeEventListener('mouseenter', enter);
    };
  }, [outerX, outerY, innerX, innerY]);

  if (typeof window !== 'undefined' && window.matchMedia('(hover: none)').matches) return null;

  return (
    <>
      {/* Outer ring */}
      <motion.div
        style={{
          position: 'fixed',
          left: outerX,
          top: outerY,
          width: 40,
          height: 40,
          borderRadius: '50%',
          border: '1.5px solid var(--gold-primary)',
          pointerEvents: 'none',
          zIndex: 99999,
          mixBlendMode: 'difference',
          opacity: isHidden ? 0 : 1,
          scale: isPointer ? 1.8 : isText ? 0.3 : 1,
          backgroundColor: isPointer ? 'var(--gold-glow)' : 'transparent',
          transition: 'opacity 0.2s, scale 0.2s, background-color 0.2s',
        }}
      />
      {/* Inner dot */}
      <motion.div
        style={{
          position: 'fixed',
          left: innerX,
          top: innerY,
          width: 8,
          height: 8,
          borderRadius: '50%',
          backgroundColor: 'var(--gold-light)',
          pointerEvents: 'none',
          zIndex: 99999,
          opacity: isHidden || isPointer || isText ? 0 : 1,
          transition: 'opacity 0.2s',
        }}
      />
    </>
  );
}
