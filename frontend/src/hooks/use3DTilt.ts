import { useState, useCallback, useRef, useEffect, MouseEvent, TouchEvent } from 'react';

interface TiltOptions {
  maxTilt?: number; // Maximum tilt angle in degrees (default 8deg)
  perspective?: number; // Perspective distance in px (default 1000px)
  scale?: number; // Scale factor on hover (default 1.02)
  speed?: number; // Transition speed in ms (default 400ms)
  disabled?: boolean;
}

export function use3DTilt<T extends HTMLElement = HTMLDivElement>(options: TiltOptions = {}) {
  const { maxTilt = 8, scale = 1.02, disabled = false } = options;
  const [style, setStyle] = useState<React.CSSProperties>({});
  const elementRef = useRef<T | null>(null);

  // Check reduced motion preference
  const isReducedMotion = useRef(false);

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    isReducedMotion.current = mediaQuery.matches;

    const handler = (e: MediaQueryListEvent) => {
      isReducedMotion.current = e.matches;
    };

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    }
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent<T>) => {
      if (disabled || isReducedMotion.current || !elementRef.current) return;

      const rect = elementRef.current.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;

      // Mouse position relative to element center (-1 to 1)
      const x = (e.clientX - rect.left - width / 2) / (width / 2);
      const y = (e.clientY - rect.top - height / 2) / (height / 2);

      // Rotations
      const rotateX = -y * maxTilt;
      const rotateY = x * maxTilt;

      // Mouse percent for glare gradient (0 to 1)
      const mouseX = Math.min(1, Math.max(0, (e.clientX - rect.left) / width));
      const mouseY = Math.min(1, Math.max(0, (e.clientY - rect.top) / height));

      setStyle({
        transform: `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(${scale}, ${scale}, ${scale})`,
        transition: 'transform 100ms ease-out',
        ['--mouse-x' as string]: mouseX.toFixed(3),
        ['--mouse-y' as string]: mouseY.toFixed(3),
      });
    },
    [maxTilt, scale, disabled]
  );

  const handleMouseLeave = useCallback(() => {
    if (disabled || isReducedMotion.current) return;
    setStyle({
      transform: 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)',
      transition: 'transform 400ms cubic-bezier(0.16, 1, 0.3, 1)',
      ['--mouse-x' as string]: '0.5',
      ['--mouse-y' as string]: '0.5',
    });
  }, [disabled]);

  const handleTouchMove = useCallback(
    (e: TouchEvent<T>) => {
      if (disabled || isReducedMotion.current || !elementRef.current || !e.touches[0]) return;
      const touch = e.touches[0];
      const rect = elementRef.current.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;

      const x = (touch.clientX - rect.left - width / 2) / (width / 2);
      const y = (touch.clientY - rect.top - height / 2) / (height / 2);

      const rotateX = -y * (maxTilt * 0.5); // Reduced tilt on touch
      const rotateY = x * (maxTilt * 0.5);

      setStyle({
        transform: `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.01, 1.01, 1.01)`,
        transition: 'transform 100ms ease-out',
      });
    },
    [maxTilt, disabled]
  );

  return {
    ref: elementRef,
    style,
    onMouseMove: handleMouseMove,
    onMouseLeave: handleMouseLeave,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleMouseLeave,
  };
}
