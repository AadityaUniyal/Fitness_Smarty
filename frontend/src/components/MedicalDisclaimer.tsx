import React from 'react';

interface MedicalDisclaimerProps {
  variant?: 'banner' | 'inline' | 'modal';
  onDismiss?: () => void;
}

/**
 * Medical Disclaimer Component
 *
 * Displays a clearly visible disclaimer that the app does not provide
 * medical advice.  Required for any health/fitness application,
 * especially with pregnancy_mode and menopause_mode features.
 *
 * Variants:
 *  - banner: Full-width persistent banner at top of page
 *  - inline: Compact text for embedding in other components
 *  - modal: Dismissable overlay (stores consent in localStorage)
 */
const MedicalDisclaimer: React.FC<MedicalDisclaimerProps> = ({
  variant = 'banner',
  onDismiss,
}) => {
  const disclaimerText =
    'Fitness Smarty provides AI-generated fitness and nutrition guidance ' +
    'for informational purposes only. It is not a substitute for professional ' +
    'medical advice, diagnosis, or treatment. Always consult a qualified ' +
    'healthcare provider before starting any exercise program or making ' +
    'dietary changes, especially if you are pregnant, nursing, have a ' +
    'medical condition, or are taking medication.';

  if (variant === 'inline') {
    return (
      <p
        style={{
          fontSize: '0.75rem',
          color: 'rgba(255,255,255,0.5)',
          fontStyle: 'italic',
          margin: '0.5rem 0',
          lineHeight: 1.4,
        }}
      >
        ⚠️ {disclaimerText}
      </p>
    );
  }

  if (variant === 'modal') {
    return (
      <div
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          backdropFilter: 'blur(4px)',
        }}
      >
        <div
          style={{
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            borderRadius: '16px',
            padding: '2rem',
            maxWidth: '480px',
            border: '1px solid rgba(255,255,255,0.1)',
            boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
          }}
        >
          <h3
            style={{
              color: '#ff6b6b',
              marginTop: 0,
              fontSize: '1.1rem',
            }}
          >
            ⚠️ Important Health Disclaimer
          </h3>
          <p
            style={{
              color: 'rgba(255,255,255,0.8)',
              fontSize: '0.9rem',
              lineHeight: 1.6,
            }}
          >
            {disclaimerText}
          </p>
          <button
            onClick={onDismiss}
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              color: '#fff',
              padding: '10px 24px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: 600,
              width: '100%',
              marginTop: '0.5rem',
            }}
          >
            I Understand
          </button>
        </div>
      </div>
    );
  }

  // Default: banner
  return (
    <div
      style={{
        background: 'rgba(255, 107, 107, 0.1)',
        borderBottom: '1px solid rgba(255, 107, 107, 0.3)',
        padding: '8px 16px',
        textAlign: 'center',
        fontSize: '0.75rem',
        color: 'rgba(255, 255, 255, 0.7)',
        position: 'relative',
      }}
    >
      <span style={{ color: '#ff6b6b', marginRight: '6px' }}>⚠️</span>
      This app provides AI-generated guidance for informational purposes only
      — not medical advice.{' '}
      <a
        href="/privacy-policy.html"
        style={{
          color: '#667eea',
          textDecoration: 'underline',
        }}
      >
        Privacy Policy
      </a>
      {onDismiss && (
        <button
          onClick={onDismiss}
          aria-label="Dismiss disclaimer"
          style={{
            position: 'absolute',
            right: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            background: 'none',
            border: 'none',
            color: 'rgba(255,255,255,0.5)',
            cursor: 'pointer',
            fontSize: '1rem',
          }}
        >
          ✕
        </button>
      )}
    </div>
  );
};

export default MedicalDisclaimer;
