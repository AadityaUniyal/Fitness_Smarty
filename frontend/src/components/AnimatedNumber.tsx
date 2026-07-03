import React, { useEffect, useRef, useState } from 'react';

interface AnimatedNumberProps {
  value: number;
  duration?: number;
  formatFn?: (n: number) => string;
  className?: string;
  delay?: number;
}

const AnimatedNumber: React.FC<AnimatedNumberProps> = ({
  value,
  duration = 800,
  formatFn = (n) => n.toFixed(0),
  className = '',
  delay = 0,
}) => {
  const [display, setDisplay] = useState(0);
  const startTime = useRef<number | null>(null);
  const raf = useRef<number>(0);
  const started = useRef(false);

  useEffect(() => {
    const timeout = setTimeout(() => {
      started.current = true;
      startTime.current = null;
      const step = (timestamp: number) => {
        if (startTime.current === null) startTime.current = timestamp;
        const elapsed = timestamp - startTime.current;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        setDisplay(value * eased);
        if (progress < 1) {
          raf.current = requestAnimationFrame(step);
        } else {
          setDisplay(value);
        }
      };
      raf.current = requestAnimationFrame(step);
    }, delay);

    return () => {
      clearTimeout(timeout);
      cancelAnimationFrame(raf.current);
    };
  }, [value, duration, delay]);

  useEffect(() => {
    if (started.current) {
      cancelAnimationFrame(raf.current);
      startTime.current = null;
      const step = (timestamp: number) => {
        if (startTime.current === null) startTime.current = timestamp;
        const elapsed = timestamp - startTime.current;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        setDisplay(value * eased);
        if (progress < 1) {
          raf.current = requestAnimationFrame(step);
        } else {
          setDisplay(value);
        }
      };
      raf.current = requestAnimationFrame(step);
    }
  }, [value]);

  return <span className={className}>{formatFn(display)}</span>;
};

export default AnimatedNumber;
