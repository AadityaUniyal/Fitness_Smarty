import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

interface PageTransitionProps {
  children: React.ReactNode;
}

const PageTransition: React.FC<PageTransitionProps> = ({ children }) => {
  const location = useLocation();
  const [display, setDisplay] = useState(children);
  const [stage, setStage] = useState<'enter' | 'done'>('done');

  useEffect(() => {
    setDisplay(children);
    setStage('enter');
    const raf = requestAnimationFrame(() => {
      setStage('done');
    });
    return () => cancelAnimationFrame(raf);
  }, [location.pathname, children]);

  return (
    <div
      className={`transition-all duration-400 ease-out ${
        stage === 'enter'
          ? 'opacity-0 translate-y-6 scale-[0.98]'
          : 'opacity-100 translate-y-0 scale-100'
      }`}
    >
      {display}
    </div>
  );
};

export default PageTransition;
