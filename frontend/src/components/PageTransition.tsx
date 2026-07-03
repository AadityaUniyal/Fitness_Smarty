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
    setStage('enter');
    const timer = setTimeout(() => setStage('done'), 50);
    return () => clearTimeout(timer);
  }, [location.pathname]);

  useEffect(() => {
    setDisplay(children);
    setStage('enter');
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        setStage('done');
      });
    });
  }, [children]);

  return (
    <div
      className={`transition-all duration-500 ease-out will-change-transform will-change-opacity ${stage === 'enter' ? 'opacity-0 translate-y-4' : 'opacity-100 translate-y-0'}`}
    >
      {display}
    </div>
  );
};

export default PageTransition;
