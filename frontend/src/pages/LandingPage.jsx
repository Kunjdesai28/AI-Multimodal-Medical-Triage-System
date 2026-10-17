import React from 'react';
import { ArrowRight } from 'lucide-react';

export const LandingPage = ({ onStartAssessment }) => {
  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      width: '100%',
      minHeight: 'calc(100vh - 80px)',
    }}>
      {/* HERO SECTION */}
      <div style={{ textAlign: 'center', position: 'relative', maxWidth: '880px', width: '100%' }}>
        <h1 style={{
          fontSize: 'clamp(2.5rem, 5vw, 4rem)',
          lineHeight: 1.15,
          fontWeight: 800,
          marginBottom: '20px',
          letterSpacing: '-0.03em',
        }}>
          Intelligent Triage. <br />
          <span className="gradient-text-emerald">Multimodal Insight.</span> Faster Decisions.
        </h1>

        <p style={{
          fontSize: '1.2rem',
          color: 'var(--text-secondary)',
          maxWidth: '780px',
          margin: '0 auto 36px',
          lineHeight: 1.6,
        }}>
          An AI-assisted multimodal triage platform combining clinical data, vital signs, ECG signals, 
          and emergency scans to support emergency patient prioritization with full explainability.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <button 
            onClick={onStartAssessment} 
            className="btn btn-primary"
            style={{ padding: '14px 36px', fontSize: '1.05rem', borderRadius: '12px', display: 'inline-flex', alignItems: 'center', gap: '10px', boxShadow: '0 4px 14px rgba(16, 185, 129, 0.35)' }}
          >
            Start Assessment
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

