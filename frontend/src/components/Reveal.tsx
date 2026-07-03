import React, { useEffect, useRef, useState } from 'react';

interface RevealProps {
  children: React.ReactNode;
  className?: string;
  animation?: 'fade-in-up' | 'fade-in' | 'scale-in' | 'slide-in-right' | 'slide-in-left';
  delay?: number;
  threshold?: number;
  as?: 'div' | 'span';
}

const Reveal: React.FC<RevealProps> = ({
  children,
  className = '',
  animation = 'fade-in-up',
  delay = 0,
  threshold = 0.1,
  as = 'div',
}) => {
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTimeout(() => setVisible(true), delay);
          observer.disconnect();
        }
      },
      { threshold }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [delay, threshold]);

  const Tag = as as keyof JSX.IntrinsicElements;
  return React.createElement(Tag, {
    ref,
    className: `${className} ${visible ? animation : 'opacity-0'}`,
    style: { animationDelay: visible ? `${delay}ms` : undefined } as React.CSSProperties,
  }, children);
};

interface StaggerProps {
  children: React.ReactNode[];
  className?: string;
  itemClassName?: string;
  baseDelay?: number;
  staggerDelay?: number;
}

const Stagger: React.FC<StaggerProps> = ({
  children,
  className = '',
  itemClassName = '',
  baseDelay = 0,
  staggerDelay = 60,
}) => {
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.05 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} className={className}>
      {children.map((child, i) => (
        <div
          key={i}
          className={`${itemClassName} ${visible ? 'fade-in-up' : 'opacity-0'}`}
          style={{ animationDelay: visible ? `${baseDelay + i * staggerDelay}ms` : undefined }}
        >
          {child}
        </div>
      ))}
    </div>
  );
};

export { Reveal, Stagger };
export default Reveal;
